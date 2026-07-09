import functools

from opentelemetry import trace

_tracer = trace.get_tracer("agent-lab")


def trace_agent_message(func):
    """Wrap an agent message handler in an OpenTelemetry span so Langfuse
    records it as a trace. Replaces the former ``@langwatch.trace()``."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        with _tracer.start_as_current_span(func.__qualname__):
            return func(*args, **kwargs)

    return wrapper


def set_current_trace_io(*, input_value, output_value, metadata):
    """Set Langfuse trace-level input/output/metadata attributes on the
    current span. Replaces ``langwatch.get_current_trace().update(...)``."""
    span = trace.get_current_span()
    span.set_attribute("langfuse.trace.input", input_value)
    span.set_attribute("langfuse.trace.output", output_value)
    for key, value in metadata.items():
        span.set_attribute(f"langfuse.trace.metadata.{key}", value)
