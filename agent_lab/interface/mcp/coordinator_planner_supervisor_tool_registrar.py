from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Callable

from jinja2 import DictLoader, Environment, select_autoescape

import agent_lab.services.agent_types.coordinator_planner_supervisor as _cps_package
from agent_lab.interface.mcp.prompt_registry import PromptRegistry
from agent_lab.interface.mcp.prompt_set_registrar import PromptSetRegistrar
from agent_lab.interface.mcp.user_prompt_resolver import UserPromptResolver
from agent_lab.services.agent_types.coordinator_planner_supervisor import (
    SUPERVISED_AGENT_CONFIGURATION,
    SUPERVISED_AGENTS,
)

_AGENT_TYPE = "coordinator_planner_supervisor"
_TEMPLATES_DIR = Path(_cps_package.__file__).parent
_ROLES = [
    "coordinator",
    "planner",
    "supervisor",
    "researcher",
    "coder",
    "browser",
    "reporter",
]


def _load_default_template(role: str) -> str:
    return (_TEMPLATES_DIR / f"default_{role}_system_prompt.txt").read_text().strip()


class CoordinatorPlannerSupervisorToolRegistrar(PromptSetRegistrar):
    """Exposes the coordinator_planner_supervisor role prompts over MCP.

    Templates are rendered fully server-side with the same Jinja environment
    and variables as ``AgentBase.parse_prompt_template`` — several templates
    use control flow over ``SUPERVISED_AGENTS``/``SUPERVISED_AGENT_CONFIGURATION``
    that an external MCP client cannot substitute. Clients may pass
    ``deep_search_mode`` and ``current_time`` (advertised as prompt arguments
    and accepted by ``read_prompt_mcp``/the ``prompt://{name}`` resource
    template); unset, they default to ``False`` and the server clock.
    """

    agent_type = _AGENT_TYPE
    role_setting_keys = {role: f"{role}_system_prompt" for role in _ROLES}
    role_prompt_names = {role: f"{_AGENT_TYPE}_{role}" for role in _ROLES}

    def __init__(
        self,
        user_prompt_resolver: UserPromptResolver,
        prompt_registry: PromptRegistry,
    ) -> None:
        super().__init__(
            user_prompt_resolver,
            prompt_registry,
            default_templates={role: _load_default_template(role) for role in _ROLES},
        )

    def _build_prompt_fn(self, role: str) -> Callable[..., str]:
        def prompt(deep_search_mode: str = "false", current_time: str = "") -> str:
            """Render the role's system prompt.

            Args:
                deep_search_mode: "true" to render the deep-search variant.
                current_time: Timestamp substituted for CURRENT_TIME;
                    defaults to the server clock when empty.
            """
            return self._resolve_prompt(
                role,
                {"deep_search_mode": deep_search_mode, "current_time": current_time},
            )

        return prompt

    def _render(self, template: str, params: dict[str, str]) -> str:
        deep_search_mode = (
            str(params.get("deep_search_mode", "")).strip().lower() == "true"
        )
        current_time = params.get("current_time") or datetime.now().strftime(
            "%a %b %d %Y %H:%M:%S %z"
        )
        env = Environment(
            loader=DictLoader({"prompt": template}),
            autoescape=select_autoescape(),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        return env.get_template("prompt").render(
            CURRENT_TIME=current_time,
            DEEP_SEARCH_MODE=deep_search_mode,
            SUPERVISED_AGENTS=SUPERVISED_AGENTS,
            SUPERVISED_AGENT_CONFIGURATION=SUPERVISED_AGENT_CONFIGURATION,
        )
