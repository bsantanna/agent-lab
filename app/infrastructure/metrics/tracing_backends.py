import base64
import logging
import os
from abc import ABC, abstractmethod
from contextlib import nullcontext

import langwatch
from langwatch.attributes import AttributeKey
from langwatch.domain import SpanProcessingExcludeRule
from openinference.instrumentation.openai import OpenAIInstrumentor
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.langchain import LangchainInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


class TracingBackend(ABC):
    """A pluggable tracing framework.

    Each backend owns its own activation config, attaches itself to the shared
    OpenTelemetry ``TracerProvider``, and optionally contributes per-message
    hooks. Adding a framework means adding an implementation and registering it
    in the container — the coordinator, the decorator and the call sites never
    change (Open/Closed).
    """

    @abstractmethod
    def configure(self, tracer_provider: TracerProvider) -> bool:
        """Wire this backend into the shared provider.

        Returns ``True`` when the backend became active (its configuration was
        present and valid), ``False`` when it stayed disabled.
        """

    def message_span(self, name: str):
        """Context manager wrapping an agent-message handler. Defaults to a
        no-op; backends that maintain their own trace context override it."""
        return nullcontext()

    def record_io(self, *, input_value, output_value, metadata) -> None:
        """Record trace-level input/output/metadata. Defaults to a no-op."""


class LangfuseTracingBackend(TracingBackend):
    """Mirrors sampled OTel spans to Langfuse via OTLP and annotates the current
    span with Langfuse trace-level semantic attributes."""

    def configure(self, tracer_provider: TracerProvider) -> bool:
        host = os.getenv("LANGFUSE_HOST")
        public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
        secret_key = os.getenv("LANGFUSE_SECRET_KEY")
        if not (host and public_key and secret_key and tracer_provider):
            logging.warning("Langfuse tracing is disabled.")
            return False

        # Langfuse ingests via OTLP; excluded paths are already dropped by the
        # ExcludePathSampler, so this exporter simply mirrors the sampled spans
        # to Langfuse alongside the collector export.
        auth = base64.b64encode(f"{public_key}:{secret_key}".encode()).decode()
        exporter = OTLPSpanExporter(
            endpoint=f"{host}/api/public/otel/v1/traces",
            headers={
                "Authorization": f"Basic {auth}",
                "x-langfuse-ingestion-version": "4",
            },
        )
        tracer_provider.add_span_processor(BatchSpanProcessor(exporter))
        return True

    def record_io(self, *, input_value, output_value, metadata) -> None:
        span = trace.get_current_span()
        span.set_attribute("langfuse.trace.input", input_value)
        span.set_attribute("langfuse.trace.output", output_value)
        for key, value in metadata.items():
            span.set_attribute(f"langfuse.trace.metadata.{key}", value)


class LangWatchTracingBackend(TracingBackend):
    """Runs LangWatch alongside the other backends. It attaches to the shared
    provider (``tracer_provider=...``) so spans reach LangWatch without
    clobbering the collector/Langfuse exporters, and owns its own trace context
    per agent message."""

    def __init__(self, *, service_name: str, service_version: str, excluded_paths):
        self._service_name = service_name
        self._service_version = service_version
        self._excluded_paths = excluded_paths

    def configure(self, tracer_provider: TracerProvider) -> bool:
        endpoint = os.getenv("LANGWATCH_ENDPOINT")
        api_key = os.getenv("LANGWATCH_API_KEY")
        if not (endpoint and api_key and tracer_provider):
            logging.warning("Langwatch tracing is disabled.")
            return False

        exclude_rules = [
            SpanProcessingExcludeRule(
                field_name="span_name",
                match_value=path,
                match_operation="includes",
            )
            for path in self._excluded_paths
        ]
        langwatch.setup(
            endpoint_url=endpoint,
            api_key=api_key,
            base_attributes={
                AttributeKey.ServiceName: self._service_name,
                AttributeKey.ServiceVersion: self._service_version,
            },
            instrumentors=[LangchainInstrumentor(), OpenAIInstrumentor()],
            span_exclude_rules=exclude_rules,
            tracer_provider=tracer_provider,
        )
        return True

    def message_span(self, name: str):
        return langwatch.trace(name=name)

    def record_io(self, *, input_value, output_value, metadata) -> None:
        langwatch.get_current_trace().update(
            input=input_value,
            output=output_value,
            metadata=metadata,
        )
