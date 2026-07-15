from unittest.mock import MagicMock

from agent_lab.interface.mcp.prompt_registry import PromptRegistry
from agent_lab.interface.mcp.prompt_set_registrar import PromptSetRegistrar
from agent_lab.interface.mcp.registrar import McpRegistrar


class SampleRegistrar(PromptSetRegistrar):
    agent_type = "sample_agent"
    role_setting_keys = {
        "coordinator": "coordinator_system_prompt",
        "reporter": "reporter_system_prompt",
    }
    role_prompt_names = {
        "coordinator": "sample_agent_coordinator",
        "reporter": "sample_agent_reporter",
    }


def _make_registrar(prompt_registry=None):
    resolver = MagicMock()
    resolver.resolve.side_effect = lambda **kwargs: kwargs["default_template"]
    registrar = SampleRegistrar(
        user_prompt_resolver=resolver,
        prompt_registry=prompt_registry or PromptRegistry(),
        default_templates={"coordinator": "COORD_TEMPLATE", "reporter": "REP_TEMPLATE"},
    )
    return registrar, resolver


class TestPromptSetRegistrar:
    def test_is_mcp_registrar(self):
        assert issubclass(PromptSetRegistrar, McpRegistrar)

    def test_init_registers_all_roles_in_prompt_registry(self):
        prompt_registry = PromptRegistry()
        _make_registrar(prompt_registry)
        assert prompt_registry.names() == [
            "sample_agent_coordinator",
            "sample_agent_reporter",
        ]

    def test_registry_resolver_delegates_to_user_prompt_resolver(self):
        prompt_registry = PromptRegistry()
        _, resolver = _make_registrar(prompt_registry)
        result = prompt_registry.resolve("sample_agent_reporter")
        assert result == "REP_TEMPLATE"
        resolver.resolve.assert_called_once_with(
            agent_type="sample_agent",
            setting_key="reporter_system_prompt",
            default_template="REP_TEMPLATE",
        )

    def test_default_render_is_identity(self):
        registrar, _ = _make_registrar()
        assert registrar._render("{{ CURRENT_TIME }}", {}) == "{{ CURRENT_TIME }}"

    def test_render_override_applies_to_resolved_prompt(self):
        class RenderingRegistrar(SampleRegistrar):
            def _render(self, template: str, params: dict) -> str:
                return template.lower()

        resolver = MagicMock()
        resolver.resolve.side_effect = lambda **kwargs: kwargs["default_template"]
        registrar = RenderingRegistrar(
            user_prompt_resolver=resolver,
            prompt_registry=PromptRegistry(),
            default_templates={"coordinator": "COORD", "reporter": "REP"},
        )
        assert registrar._resolve_prompt("coordinator") == "coord"

    def test_registry_resolver_forwards_params_to_render(self):
        class ParamEchoRegistrar(SampleRegistrar):
            def _render(self, template: str, params: dict) -> str:
                return f"{template}|{params.get('mode', 'default')}"

        resolver = MagicMock()
        resolver.resolve.side_effect = lambda **kwargs: kwargs["default_template"]
        prompt_registry = PromptRegistry()
        ParamEchoRegistrar(
            user_prompt_resolver=resolver,
            prompt_registry=prompt_registry,
            default_templates={"coordinator": "COORD", "reporter": "REP"},
        )
        assert (
            prompt_registry.resolve("sample_agent_coordinator", mode="fast")
            == "COORD|fast"
        )
        assert prompt_registry.resolve("sample_agent_reporter") == "REP|default"

    def test_build_prompt_fn_override_exposes_named_arguments(self):
        class ParamPromptRegistrar(SampleRegistrar):
            def _render(self, template: str, params: dict) -> str:
                return f"{template}|{params.get('mode', 'default')}"

            def _build_prompt_fn(self, role: str):
                def prompt(mode: str = "default") -> str:
                    return self._resolve_prompt(role, {"mode": mode})

                return prompt

        resolver = MagicMock()
        resolver.resolve.side_effect = lambda **kwargs: kwargs["default_template"]
        registrar = ParamPromptRegistrar(
            user_prompt_resolver=resolver,
            prompt_registry=PromptRegistry(),
            default_templates={"coordinator": "COORD", "reporter": "REP"},
        )
        mcp = MagicMock()
        registrar.register_prompts(mcp)
        closures = [c.args[0] for c in mcp.prompt.return_value.call_args_list]
        assert closures[0](mode="fast") == "COORD|fast"
        assert closures[0]() == "COORD|default"

    def test_register_prompts_registers_each_role(self):
        registrar, _ = _make_registrar()
        mcp = MagicMock()
        registrar.register_prompts(mcp)
        names = sorted(call.kwargs["name"] for call in mcp.prompt.call_args_list)
        assert names == ["sample_agent_coordinator", "sample_agent_reporter"]
        descriptions = [
            call.kwargs["description"] for call in mcp.prompt.call_args_list
        ]
        assert all("sample_agent" in d for d in descriptions)

    def test_register_resources_registers_each_role_with_prompt_uri(self):
        registrar, _ = _make_registrar()
        mcp = MagicMock()
        registrar.register_resources(mcp)
        uris = sorted(call.kwargs["uri"] for call in mcp.resource.call_args_list)
        assert uris == [
            "prompt://sample_agent_coordinator",
            "prompt://sample_agent_reporter",
        ]
        mime_types = {call.kwargs["mime_type"] for call in mcp.resource.call_args_list}
        assert mime_types == {"text/plain"}

    def test_registered_prompt_closures_bind_their_own_role(self):
        registrar, _ = _make_registrar()
        mcp = MagicMock()
        registrar.register_prompts(mcp)
        closures = [c.args[0] for c in mcp.prompt.return_value.call_args_list]
        assert [fn() for fn in closures] == ["COORD_TEMPLATE", "REP_TEMPLATE"]

    def test_register_tools_is_inherited_no_op(self):
        registrar, _ = _make_registrar()
        mcp = MagicMock()
        registrar.register_tools(mcp, MagicMock())
        mcp.tool.assert_not_called()
