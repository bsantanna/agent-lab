from __future__ import annotations

import functools
import inspect
from dataclasses import dataclass
from typing import Callable, Optional


@dataclass(frozen=True)
class ToolDescriptor:
    fn: Callable
    name: str
    description: Optional[str]
    annotations: Optional[dict]


_registry: dict = {}  # keyed by tool name, preserving decoration order


def RegisterMcpTool(
    name: str,
    *,
    description: Optional[str] = None,
    annotations: Optional[dict] = None,
):
    """Registers a standalone async function as an MCP tool.

    The decorated function's first parameter must be ``container``; it is bound
    at registration time and hidden from the client-facing schema (see
    ``bind_container``). Discovered via the same ``scan_packages`` /
    ``agent_lab.agents`` entry-point pass as ``@RegisterAgent`` and registered
    by ``DecoratedToolRegistrar`` — the simple alternative to writing a full
    ``McpRegistrar`` subclass.
    """

    def decorator(fn):
        if not inspect.iscoroutinefunction(fn):
            raise TypeError(f"@RegisterMcpTool requires an async function, got {fn!r}")
        params = list(inspect.signature(fn).parameters)
        if not params or params[0] != "container":
            raise TypeError(
                f"@RegisterMcpTool function for tool '{name}' must take "
                f"'container' as its first parameter"
            )
        existing = _registry.get(name)
        if existing is not None and existing.fn is not fn:
            raise ValueError(f"MCP tool '{name}' already registered by {existing.fn!r}")
        _registry[name] = ToolDescriptor(fn, name, description, annotations)
        return fn

    return decorator


def registered_tools() -> list:
    return list(_registry.values())


def bind_container(descriptor: ToolDescriptor, container) -> Callable:
    """Wraps a tool function with ``container`` bound in and hidden.

    ``container`` is supplied as the first positional argument and dropped from
    the exposed signature, so fastmcp builds the tool schema from the remaining
    (client-facing) parameters only. Client-facing annotations are resolved by
    fastmcp against the tool's own module (via ``functools.wraps``' __wrapped__),
    which is why ``container`` itself must stay unannotated — it never reaches
    fastmcp, but an unresolved annotation on it would break get_type_hints.
    """
    fn = descriptor.fn
    bound = functools.partial(fn, container)

    @functools.wraps(fn)
    async def wrapper(*args, **kwargs):
        return await bound(*args, **kwargs)

    signature = inspect.signature(fn)
    wrapper.__signature__ = signature.replace(
        parameters=list(signature.parameters.values())[1:]
    )
    return wrapper


def _reset_registry_for_tests() -> None:
    _registry.clear()
