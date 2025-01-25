import logging
from opentelemetry import trace, metrics
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics._internal.export import PeriodicExportingMetricReader
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs._internal.export import BatchLogRecordProcessor
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


class Tracer:
    def __init__(
        self, collector_endpoint: str, service_name: str, log_level=logging.INFO
    ):
        resource = Resource(attributes={SERVICE_NAME: service_name})
        trace_provider = TracerProvider(resource=resource)
        trace.set_tracer_provider(trace_provider)

        processor = BatchSpanProcessor(
            OTLPSpanExporter(endpoint=f"{collector_endpoint}/v1/traces")
        )
        trace_provider.add_span_processor(processor)
        trace.set_tracer_provider(trace_provider)

        reader = PeriodicExportingMetricReader(
            OTLPMetricExporter(endpoint=f"{collector_endpoint}/v1/metrics")
        )
        meter_provider = MeterProvider(resource=resource, metric_readers=[reader])
        metrics.set_meter_provider(meter_provider)

        log_exporter = OTLPLogExporter(endpoint=f"{collector_endpoint}/v1/logs")
        logger_provider = LoggerProvider(resource=resource)
        logger_provider.add_log_record_processor(BatchLogRecordProcessor(log_exporter))
        otlp_handler = LoggingHandler(logger_provider=logger_provider)
        console_handler = logging.StreamHandler()
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[console_handler, otlp_handler],
        )

        self.logger = logging.getLogger(__name__)

    def setup(self, app):
        FastAPIInstrumentor.instrument_app(app)

    def log(self):
        return self.logger
