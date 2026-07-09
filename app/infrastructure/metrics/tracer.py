import base64
import logging
import os

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
from opentelemetry.trace import SpanKind, TraceState, Link
from typing_extensions import Optional, Sequence

service_name = os.getenv("SERVICE_NAME", "Agent-Lab")
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

        langfuse_host = os.getenv("LANGFUSE_HOST")
        langfuse_public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
        langfuse_secret_key = os.getenv("LANGFUSE_SECRET_KEY")
        if (
            langfuse_host is not None
            and langfuse_public_key is not None
            and langfuse_secret_key is not None
            and tracer_provider is not None
        ):
            # Langfuse ingests via OTLP; excluded paths are already dropped by
            # ExcludePathSampler, so this exporter simply mirrors the sampled
            # spans to Langfuse alongside the collector export.
            auth = base64.b64encode(
                f"{langfuse_public_key}:{langfuse_secret_key}".encode()
            ).decode()
            langfuse_exporter = OTLPSpanExporter(
                endpoint=f"{langfuse_host}/api/public/otel/v1/traces",
                headers={
                    "Authorization": f"Basic {auth}",
                    "x-langfuse-ingestion-version": "4",
                },
            )
            tracer_provider.add_span_processor(BatchSpanProcessor(langfuse_exporter))
        else:
            logging.warning("Langfuse tracing is disabled.")
