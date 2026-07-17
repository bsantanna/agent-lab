from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING

from agent_lab.core.extra_deps import resolve_extra_deps
from agent_lab.interface.mcp import registrar_registration

if TYPE_CHECKING:
    from agent_lab.core.container import Container
    from agent_lab.interface.mcp.registrar import McpRegistrar

# Framework bridge registrars, loaded unconditionally: they expose whatever
# the @discoverable_mcp_tool / @discoverable_mcp_prompt registries contain and
# nothing of their own, so they must never depend on the app's scan_packages —
# excluding built-in capabilities from the scan must not silently disable a
# downstream app's own decorated tools and prompts. Capability modules
# (default_tool_registrar, coordinator_planner_supervisor_tool_registrar) are
# discovered via the scan instead.
_FRAMEWORK_REGISTRAR_MODULES = (
    "agent_lab.interface.mcp.decorated_tool_registrar",
    "agent_lab.interface.mcp.decorated_prompt_registrar",
)


def load_framework_registrars() -> None:
    """Imports the framework bridge registrar modules so their decorators fire.

    Idempotent via ``sys.modules``. Everything else — agents, MCP tools,
    prompts, capability registrars — is discovered through
    ``discovery.scan_packages``.
    """
    for module_name in _FRAMEWORK_REGISTRAR_MODULES:
        import_module(module_name)


def build_registrars(container: Container) -> list[McpRegistrar]:
    """Instantiates every ``@discoverable_mcp_registrar``-registered registrar.

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
