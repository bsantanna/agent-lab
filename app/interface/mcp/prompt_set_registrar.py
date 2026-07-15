from __future__ import annotations

from typing import Callable

from fastmcp import FastMCP

from app.interface.mcp.prompt_registry import PromptRegistry
from app.interface.mcp.registrar import McpRegistrar
from app.interface.mcp.user_prompt_resolver import UserPromptResolver


class PromptSetRegistrar(McpRegistrar):
    """Exposes one agent type's role-keyed system prompts over MCP.

    Each role is registered under three surfaces at once: the shared
    ``PromptRegistry`` (backing the ``read_prompt_mcp`` tool and the global
    ``prompt://{name}`` resource template — tools are the only MCP primitive
    reliably model-callable across clients), ``prompts/get``, and a concrete
    ``prompt://<name>`` resource.

    Subclasses declare ``agent_type``, ``role_setting_keys`` and
    ``role_prompt_names``, pass their default templates to ``__init__``, and
    may override:

    - ``_render(template, params)`` to post-process the resolved template
      (the default returns it unchanged);
    - ``_build_prompt_fn(role)`` to accept named prompt arguments — the
      returned function's signature is advertised as MCP ``PromptArgument``s
      and its keyword values flow into ``_render`` as ``params``.
    """

    agent_type: str
    role_setting_keys: dict[str, str]
    role_prompt_names: dict[str, str]

    def __init__(
        self,
        user_prompt_resolver: UserPromptResolver,
        prompt_registry: PromptRegistry,
        default_templates: dict[str, str],
    ) -> None:
        self._user_prompt_resolver = user_prompt_resolver
        self._default_templates = default_templates
        for role in self.role_prompt_names:
            self._register_resolver(prompt_registry, role)

    def _register_resolver(self, prompt_registry: PromptRegistry, role: str) -> None:
        prompt_registry.register(
            self.role_prompt_names[role],
            lambda **params: self._resolve_prompt(role, params),
        )

    def _resolve_prompt(self, role: str, params: dict[str, str] | None = None) -> str:
        template = self._user_prompt_resolver.resolve(
            agent_type=self.agent_type,
            setting_key=self.role_setting_keys[role],
            default_template=self._default_templates[role],
        )
        return self._render(template, params or {})

    def _render(self, template: str, params: dict[str, str]) -> str:
        return template

    def _build_prompt_fn(self, role: str) -> Callable[..., str]:
        def prompt() -> str:
            return self._resolve_prompt(role)

        return prompt

    def _prompt_description(self, role: str) -> str:
        return f"System prompt for the {self.agent_type} {role} step."

    def register_prompts(self, mcp: FastMCP) -> None:
        for role, prompt_name in self.role_prompt_names.items():
            self._add_prompt(mcp, role, prompt_name)

    def _add_prompt(self, mcp: FastMCP, role: str, prompt_name: str) -> None:
        mcp.prompt(
            name=prompt_name,
            description=self._prompt_description(role),
        )(self._build_prompt_fn(role))

    def register_resources(self, mcp: FastMCP) -> None:
        for role, prompt_name in self.role_prompt_names.items():
            self._add_resource(mcp, role, prompt_name)

    def _add_resource(self, mcp: FastMCP, role: str, prompt_name: str) -> None:
        @mcp.resource(
            uri=f"prompt://{prompt_name}",
            name=prompt_name,
            description=self._prompt_description(role),
            mime_type="text/plain",
        )
        def resource() -> str:
            return self._resolve_prompt(role)
