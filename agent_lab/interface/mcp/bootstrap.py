from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING

from agent_lab.core.extra_deps import resolve_extra_deps
from agent_lab.interface.mcp import registrar_registration

if TYPE_CHECKING:
    from agent_lab.core.container import Container
    from agent_lab.interface.mcp.registrar import McpRegistrar

# Built-in registrar modules whose @RegisterMcpRegistrar decorators must fire
# regardless of the app's scan_packages — they live in agent_lab, not in a
# scanned agent package, so no downstream scan would import them.
_BUILTIN_REGISTRAR_MODULES = (
    "agent_lab.interface.mcp.decorated_tool_registrar",
    "agent_lab.interface.mcp.decorated_prompt_registrar",
    "agent_lab.interface.mcp.default_tool_registrar",
    "agent_lab.interface.mcp.coordinator_planner_supervisor_tool_registrar",
)


def load_builtin_registrars() -> None:
    """Imports Agent-Lab's built-in registrar modules so their decorators fire.

    Idempotent via ``sys.modules``; the registrar counterpart to
    ``discovery.scan_packages`` for the library's own registrars.
    """
    for module_name in _BUILTIN_REGISTRAR_MODULES:
        import_module(module_name)


def build_registrars(container: Container) -> list[McpRegistrar]:
    """Instantiates every ``@RegisterMcpRegistrar``-registered registrar.

    Each registrar's ``extra_deps`` are resolved by provider-attribute name off
    the live (possibly downstream-subclassed) container — the ``AgentRegistry``
    convention. Every registrar is constructed eagerly here, before
    ``build_mcp_server`` calls any ``register_*`` hook: prompt-contributing
    registrars populate the shared ``PromptRegistry`` in ``__init__``, so all
    construction must complete first (dynamic tool descriptions read
    ``prompt_registry.names()``).
    """
    registrars: list = []
    for descriptor in registrar_registration.registered_registrars():
        kwargs = resolve_extra_deps(
            container,
            descriptor.extra_deps,
            owner=f"MCP registrar '{descriptor.registrar_cls.__name__}'",
        )
        registrars.append(descriptor.registrar_cls(**kwargs))
    return registrars
