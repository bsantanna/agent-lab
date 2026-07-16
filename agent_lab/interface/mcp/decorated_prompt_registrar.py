from __future__ import annotations

import functools
from typing import Callable

from fastmcp import FastMCP

from agent_lab.interface.mcp import prompt_registration
from agent_lab.interface.mcp.prompt_registration import PromptDescriptor
from agent_lab.interface.mcp.prompt_registry import PromptRegistry
from agent_lab.interface.mcp.registrar import McpRegistrar
from agent_lab.interface.mcp.registrar_registration import RegisterMcpRegistrar
from agent_lab.interface.mcp.user_prompt_resolver import UserPromptResolver


@RegisterMcpRegistrar(extra_deps=("prompt_registry", "user_prompt_resolver"))
class DecoratedPromptRegistrar(McpRegistrar):
    """Exposes every ``@RegisterMcpPrompt``-decorated function over MCP.

    Each decorated prompt lands on the full prompt triple: the shared
    ``PromptRegistry`` is populated in ``__init__`` (before any ``register_*``
    hook runs, so ``read_prompt_mcp``'s description lists the names), and
    ``prompts/get`` plus a concrete ``prompt://<name>`` resource are added by
    the ``register_*`` hooks. Every surface funnels through ``_resolve`` so
    tenancy-enabled prompts behave identically everywhere.
    """

    def __init__(
        self,
        prompt_registry: PromptRegistry,
        user_prompt_resolver: UserPromptResolver,
    ) -> None:
        self._user_prompt_resolver = user_prompt_resolver
        self._descriptors = tuple(prompt_registration.registered_prompts())
        for descriptor in self._descriptors:
            self._register_resolver(prompt_registry, descriptor)

    # Helper methods called once per iteration give each closure its own stack
    # frame — the loop-closure registration convention used across registrars.
    def _register_resolver(
        self, prompt_registry: PromptRegistry, descriptor: PromptDescriptor
    ) -> None:
        prompt_registry.register(
            descriptor.name,
            lambda **params: self._resolve(descriptor, params),
        )

    def _resolve(self, descriptor: PromptDescriptor, params: dict) -> str:
        text = descriptor.fn(**params)
        if descriptor.agent_type is None:
            return text
        # Tenant overrides replace the output verbatim; params only affect the
        # default path (see RegisterMcpPrompt docstring).
        return self._user_prompt_resolver.resolve(
            agent_type=descriptor.agent_type,
            setting_key=descriptor.setting_key,
            default_template=text,
        )

    def register_prompts(self, mcp: FastMCP) -> None:
        for descriptor in self._descriptors:
            self._add_prompt(mcp, descriptor)

    def _add_prompt(self, mcp: FastMCP, descriptor: PromptDescriptor) -> None:
        mcp.prompt(
            name=descriptor.name,
            description=descriptor.description,
        )(self._build_prompt_fn(descriptor))

    def _build_prompt_fn(self, descriptor: PromptDescriptor) -> Callable[..., str]:
        # functools.wraps points __wrapped__ at the decorated function, so the
        # advertised PromptArguments come from its signature while the call
        # still funnels through _resolve for tenancy.
        @functools.wraps(descriptor.fn)
        def prompt(**kwargs) -> str:
            return self._resolve(descriptor, kwargs)

        return prompt

    def register_resources(self, mcp: FastMCP) -> None:
        for descriptor in self._descriptors:
            self._add_resource(mcp, descriptor)

    def _add_resource(self, mcp: FastMCP, descriptor: PromptDescriptor) -> None:
        @mcp.resource(
            uri=f"prompt://{descriptor.name}",
            name=descriptor.name,
            description=descriptor.description,
            mime_type="text/plain",
        )
        def resource() -> str:
            return self._resolve(descriptor, {})
