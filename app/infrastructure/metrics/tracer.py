import logging
import os

from langwatch.attributes import AttributeKey
from langwatch.domain import SpanProcessingExcludeRule
from openinference.instrumentation.openai import OpenAIInstrumentor
from opentelemetry import trace, metrics
from opentelemetry.context import Context
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.langchain import LangchainInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs._internal.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics._internal.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, Attributes
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.sampling import Sampler, Decision, SamplingResult
import langwatch
from opentelemetry.trace import SpanKind, TraceState, Link
from typing_extensions import Optional, Sequence

service_name = os.getenv("SERVICE_NAME", "Agent-Lab")
service_version = os.getenv("SERVICE_VERSION", "snapshot")
collector_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
resource = Resource(attributes={SERVICE_NAME: service_name})
excluded_paths = [
    "/apple-touch-icon.png",
    "/apple-touch-icon-precomposed.png",
    "/docs",
    "/favicon.ico",
    "/openapi.json",
    "/status/liveness",
    "/status/readiness",
    "/status/metrics",
]


class ExcludePathSampler(Sampler):
    def __init__(self, paths):
        self.excluded_paths = paths

    def should_sample(
        self,
        parent_context: Optional[Context],
        trace_id: int,
        name: str,
        kind: Optional[SpanKind] = None,
        attributes: Attributes = None,
        links: Optional[Sequence[Link]] = None,
        trace_state: Optional[TraceState] = None,
    ) -> SamplingResult:
        for path in self.excluded_paths:
            if path in name:
                return SamplingResult(Decision.DROP)
        return SamplingResult(Decision.RECORD_AND_SAMPLE)

    def get_description(self) -> str:
        return f"ExcludePathSampler({self.excluded_paths})"


tracer_provider = None

if collector_endpoint is not None:
    # traces
    tracer_provider = TracerProvider(
        resource=resource, sampler=ExcludePathSampler(excluded_paths)
    )
    trace.set_tracer_provider(tracer_provider)
    processor = BatchSpanProcessor(
        OTLPSpanExporter(endpoint=f"{collector_endpoint}/v1/traces")
    )
    tracer_provider.add_span_processor(processor)
    trace.set_tracer_provider(tracer_provider)

    # metrics
    reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(endpoint=f"{collector_endpoint}/v1/metrics")
    )
    meter_provider = MeterProvider(resource=resource, metric_readers=[reader])
    metrics.set_meter_provider(meter_provider)

    # logs
    log_exporter = OTLPLogExporter(endpoint=f"{collector_endpoint}/v1/logs")
    logger_provider = LoggerProvider(resource=resource)
    logger_provider.add_log_record_processor(BatchLogRecordProcessor(log_exporter))
    otlp_handler = LoggingHandler(logger_provider=logger_provider)
    console_handler = logging.StreamHandler()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[console_handler, otlp_handler],
    )


class Tracer:
    def setup(self, app):
        FastAPIInstrumentor.instrument_app(app)
        HTTPXClientInstrumentor().instrument()
        LangchainInstrumentor().instrument()
        SQLAlchemyInstrumentor().instrument()

        langwatch_endpoint = os.getenv("LANGWATCH_ENDPOINT")
        langwatch_api_key = os.getenv("LANGWATCH_API_KEY")
        if (
            langwatch_endpoint is not None
            and langwatch_api_key is not None
            and tracer_provider is not None
        ):
            exclude_rules = []
            for path in excluded_paths:
                exclude_rules.append(
                    SpanProcessingExcludeRule(
                        field_name="span_name",
                        match_value=f"{path}",
                        match_operation="includes",
                    )
                )

            langwatch.setup(
                endpoint_url=langwatch_endpoint,
                api_key=langwatch_api_key,
                base_attributes={
                    AttributeKey.ServiceName: service_name,
                    AttributeKey.ServiceVersion: service_version,
                },
                instrumentors=[LangchainInstrumentor(), OpenAIInstrumentor()],
                span_exclude_rules=exclude_rules,
                tracer_provider=tracer_provider,
            )
        else:
            logging.warning("Langwatch tracing is disabled.")
