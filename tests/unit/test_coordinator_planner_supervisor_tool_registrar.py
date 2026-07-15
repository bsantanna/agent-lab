from datetime import datetime
from unittest.mock import MagicMock

from app.interface.mcp.coordinator_planner_supervisor_tool_registrar import (
    CoordinatorPlannerSupervisorToolRegistrar,
)
from app.interface.mcp.prompt_registry import PromptRegistry
from app.services.agent_types.coordinator_planner_supervisor import SUPERVISED_AGENTS

_EXPECTED_PROMPT_NAMES = [
    f"coordinator_planner_supervisor_{role}"
    for role in [
        "browser",
        "coder",
        "coordinator",
        "planner",
        "reporter",
        "researcher",
        "supervisor",
    ]
]


def _make_registrar(prompt_registry=None, override=None):
    resolver = MagicMock()
    resolver.resolve.side_effect = lambda **kwargs: (
        override or kwargs["default_template"]
    )
    registrar = CoordinatorPlannerSupervisorToolRegistrar(
        user_prompt_resolver=resolver,
        prompt_registry=prompt_registry or PromptRegistry(),
    )
    return registrar, resolver


class TestCoordinatorPlannerSupervisorToolRegistrar:
    def test_registers_all_seven_roles(self):
        prompt_registry = PromptRegistry()
        _make_registrar(prompt_registry)
        assert prompt_registry.names() == _EXPECTED_PROMPT_NAMES

    def test_resolve_delegates_with_agent_type_and_setting_key(self):
        registrar, resolver = _make_registrar()
        registrar._resolve_prompt("planner")
        kwargs = resolver.resolve.call_args.kwargs
        assert kwargs["agent_type"] == "coordinator_planner_supervisor"
        assert kwargs["setting_key"] == "planner_system_prompt"
        assert kwargs["default_template"]

    def test_rendered_prompts_contain_no_jinja_syntax(self):
        prompt_registry = PromptRegistry()
        _make_registrar(prompt_registry)
        for name in _EXPECTED_PROMPT_NAMES:
            rendered = prompt_registry.resolve(name)
            assert "{{" not in rendered, name
            assert "{%" not in rendered, name

    def test_planner_prompt_renders_supervised_agents(self):
        registrar, _ = _make_registrar()
        rendered = registrar._resolve_prompt("planner")
        for agent in SUPERVISED_AGENTS:
            assert agent in rendered

    def test_coordinator_prompt_renders_current_time(self):
        registrar, _ = _make_registrar()
        rendered = registrar._resolve_prompt("coordinator")
        assert "{{ CURRENT_TIME }}" not in rendered
        assert str(datetime.now().year) in rendered

    def test_tenant_override_is_rendered_too(self):
        registrar, _ = _make_registrar(
            override="Custom prompt for {{ SUPERVISED_AGENTS|join(', ') }}"
        )
        rendered = registrar._resolve_prompt("supervisor")
        assert rendered == f"Custom prompt for {', '.join(SUPERVISED_AGENTS)}"

    def test_researcher_renders_with_deep_search_mode_disabled(self):
        registrar, _ = _make_registrar()
        rendered = registrar._resolve_prompt("researcher")
        assert "{%" not in rendered
        assert rendered

    def test_deep_search_mode_param_changes_researcher_prompt(self):
        registrar, _ = _make_registrar()
        default = registrar._resolve_prompt("researcher")
        deep = registrar._resolve_prompt("researcher", {"deep_search_mode": "true"})
        assert deep != default
        assert "web_crawl" in deep
        assert "{%" not in deep

    def test_current_time_param_overrides_server_clock(self):
        registrar, _ = _make_registrar()
        rendered = registrar._resolve_prompt(
            "coordinator", {"current_time": "Mon Jan 05 2026 09:00:00"}
        )
        assert "Mon Jan 05 2026 09:00:00" in rendered

    def test_prompt_fn_advertises_named_arguments(self):
        registrar, _ = _make_registrar()
        fn = registrar._build_prompt_fn("researcher")
        deep = fn(deep_search_mode="true")
        default = fn()
        assert deep != default
        assert "web_crawl" in deep
