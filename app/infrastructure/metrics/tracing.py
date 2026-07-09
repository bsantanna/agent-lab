import functools

import langwatch
from opentelemetry import trace

_tracer = trace.get_tracer("agent-lab")

# Flipped by tracer.py once langwatch.setup() succeeds. When enabled, the helpers
# below also record to LangWatch so it runs alongside Langfuse for comparison;
# otherwise they are a no-op for LangWatch and only the OTel/Langfuse path runs.
_langwatch_enabled = False


def enable_langwatch_tracing():
    """Called by the tracer setup after a successful ``langwatch.setup()``."""
    global _langwatch_enabled
    _langwatch_enabled = True


def trace_agent_message(func):
    """Wrap an agent message handler in an OpenTelemetry span so Langfuse
    records it as a trace. When LangWatch is enabled, the same call is also
    wrapped in a ``langwatch.trace()`` context so both frameworks capture it
    from the single decorator."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        with _tracer.start_as_current_span(func.__qualname__):
            if _langwatch_enabled:
                with langwatch.trace(name=func.__qualname__):
                    return func(*args, **kwargs)
            return func(*args, **kwargs)

    return wrapper


def set_current_trace_io(*, input_value, output_value, metadata):
    """Set trace-level input/output/metadata on the current span. Writes
    Langfuse span attributes and, when LangWatch is enabled, mirrors the same
    values onto the current LangWatch trace."""
    span = trace.get_current_span()
    span.set_attribute("langfuse.trace.input", input_value)
    span.set_attribute("langfuse.trace.output", output_value)
    for key, value in metadata.items():
        span.set_attribute(f"langfuse.trace.metadata.{key}", value)

    if _langwatch_enabled:
        langwatch.get_current_trace().update(
            input=input_value,
            output=output_value,
            metadata=metadata,
        )
