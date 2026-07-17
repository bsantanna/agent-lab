from __future__ import annotations

import inspect
from dataclasses import dataclass
from typing import Callable, Optional


@dataclass(frozen=True)
class PromptDescriptor:
    fn: Callable[..., str]
    name: str
    description: Optional[str]
    agent_type: Optional[str]
    setting_key: Optional[str]


_registry: dict = {}  # keyed by prompt name, preserving decoration order


def discoverable_mcp_prompt(
    name: str,
    *,
    description: Optional[str] = None,
    agent_type: Optional[str] = None,
    setting_key: Optional[str] = None,
):
    """Registers a plain function as an MCP prompt on all three surfaces.

    The decorated function must be synchronous (``PromptRegistry.resolve`` is
    synchronous) and return the prompt text; its named parameters are
    advertised as MCP ``PromptArgument``s. ``DecoratedPromptRegistrar`` exposes
    it under the prompt triple: the shared ``PromptRegistry`` (backing the
    ``read_prompt_mcp`` tool and the global ``prompt://{name}`` resource
    template), ``prompts/get``, and a concrete ``prompt://<name>`` resource.

    Passing ``agent_type`` and ``setting_key`` (both or neither) opts into
    per-tenant overrides through ``UserPromptResolver``: a tenant's non-empty
    ``AgentSetting`` replaces the function's output verbatim — parameters only
    affect the default path. Prompts needing rendered/parameterized overrides
    belong in a ``PromptSetRegistrar`` subclass instead.

    Discovered via the same ``scan_packages`` / ``agent_lab.agents``
    entry-point pass as ``@discoverable_agent`` — the simple alternative to writing
    a full ``McpRegistrar`` subclass.
    """
    if (agent_type is None) != (setting_key is None):
        raise TypeError(
            f"@discoverable_mcp_prompt for prompt '{name}' must set agent_type and "
            f"setting_key together (or neither)"
        )

    def decorator(fn):
        if inspect.iscoroutinefunction(fn):
            raise TypeError(
                f"@discoverable_mcp_prompt requires a synchronous function "
                f"(PromptRegistry resolution is synchronous), got async {fn!r}"
            )
        existing = _registry.get(name)
        if existing is not None and existing.fn is not fn:
            raise ValueError(
                f"MCP prompt '{name}' already registered by {existing.fn!r}"
            )
        _registry[name] = PromptDescriptor(
            fn, name, description, agent_type, setting_key
        )
        return fn

    return decorator


def registered_prompts() -> list:
    return list(_registry.values())


def _reset_registry_for_tests() -> None:
    _registry.clear()
