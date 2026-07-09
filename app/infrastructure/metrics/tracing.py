import functools
from contextlib import ExitStack

from opentelemetry import trace

_tracer = trace.get_tracer("agent-lab")

# Active tracing backends, populated by Tracer.setup() at startup. The decorator
# and IO helper below fan out over whatever is registered, so they stay unaware
# of any concrete framework (Langfuse, LangWatch, ...).
_active_backends = []


def register_active_backends(backends):
    """Record the backends that successfully configured, so the message-level
    hooks below can fan out to them."""
    global _active_backends
    _active_backends = list(backends)


def trace_agent_message(func):
    """Wrap an agent message handler in an OpenTelemetry span and in each active
    backend's own message span (e.g. a LangWatch trace)."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        with _tracer.start_as_current_span(func.__qualname__):
            with ExitStack() as stack:
                for backend in _active_backends:
                    stack.enter_context(backend.message_span(func.__qualname__))
                return func(*args, **kwargs)

    return wrapper


def set_current_trace_io(*, input_value, output_value, metadata):
    """Record trace-level input/output/metadata on every active backend."""
    for backend in _active_backends:
        backend.record_io(
            input_value=input_value,
            output_value=output_value,
            metadata=metadata,
        )
