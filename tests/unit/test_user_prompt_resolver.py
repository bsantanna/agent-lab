from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from agent_lab.interface.mcp.user_prompt_resolver import UserPromptResolver


def _agent(agent_id="a1", agent_type="coordinator_planner_supervisor"):
    return SimpleNamespace(id=agent_id, agent_type=agent_type, is_active=True)


def _setting(key, value):
    return SimpleNamespace(setting_key=key, setting_value=value)


def _make_resolver(agents=None, settings=None):
    agent_service = MagicMock()
    agent_setting_service = MagicMock()
    agent_service.get_agents.return_value = agents or []
    agent_setting_service.get_agent_settings.return_value = settings or []
    resolver = UserPromptResolver(
        agent_service=agent_service, agent_setting_service=agent_setting_service
    )
    return resolver, agent_service, agent_setting_service


class TestUserPromptResolver:
    @patch(
        "agent_lab.interface.mcp.user_prompt_resolver._get_mcp_schema",
        return_value="public",
    )
    def test_public_schema_returns_default(self, _mock_schema):
        resolver, agent_service, _ = _make_resolver()
        result = resolver.resolve(
            agent_type="coordinator_planner_supervisor",
            setting_key="coordinator_system_prompt",
            default_template="DEFAULT",
        )
        assert result == "DEFAULT"
        agent_service.get_agents.assert_not_called()

    @patch(
        "agent_lab.interface.mcp.user_prompt_resolver._get_mcp_schema",
        return_value="id_tenant",
    )
    def test_no_matching_agent_returns_default(self, _mock_schema):
        resolver, _, setting_service = _make_resolver(
            agents=[_agent(agent_type="some_other_type")]
        )
        result = resolver.resolve(
            agent_type="coordinator_planner_supervisor",
            setting_key="coordinator_system_prompt",
            default_template="DEFAULT",
        )
        assert result == "DEFAULT"
        setting_service.get_agent_settings.assert_not_called()

    @patch(
        "agent_lab.interface.mcp.user_prompt_resolver._get_mcp_schema",
        return_value="id_tenant",
    )
    def test_matching_agent_with_setting_returns_user_template(self, _mock_schema):
        resolver, _, _ = _make_resolver(
            agents=[_agent()],
            settings=[_setting("coordinator_system_prompt", "USER_PROMPT")],
        )
        result = resolver.resolve(
            agent_type="coordinator_planner_supervisor",
            setting_key="coordinator_system_prompt",
            default_template="DEFAULT",
        )
        assert result == "USER_PROMPT"

    @patch(
        "agent_lab.interface.mcp.user_prompt_resolver._get_mcp_schema",
        return_value="id_tenant",
    )
    def test_empty_setting_value_falls_back_to_default(self, _mock_schema):
        resolver, _, _ = _make_resolver(
            agents=[_agent()],
            settings=[_setting("coordinator_system_prompt", "   ")],
        )
        result = resolver.resolve(
            agent_type="coordinator_planner_supervisor",
            setting_key="coordinator_system_prompt",
            default_template="DEFAULT",
        )
        assert result == "DEFAULT"

    @patch(
        "agent_lab.interface.mcp.user_prompt_resolver._get_mcp_schema",
        return_value="id_tenant",
    )
    def test_missing_setting_key_falls_back_to_default(self, _mock_schema):
        resolver, _, _ = _make_resolver(
            agents=[_agent()],
            settings=[_setting("planner_system_prompt", "ONLY_PLANNER")],
        )
        result = resolver.resolve(
            agent_type="coordinator_planner_supervisor",
            setting_key="coordinator_system_prompt",
            default_template="DEFAULT",
        )
        assert result == "DEFAULT"

    @patch(
        "agent_lab.interface.mcp.user_prompt_resolver._get_mcp_schema",
        return_value="id_tenant",
    )
    def test_first_matching_agent_wins_when_multiple(self, _mock_schema):
        first = _agent(agent_id="first")
        second = _agent(agent_id="second")
        resolver, _, setting_service = _make_resolver(
            agents=[first, second],
            settings=[_setting("coordinator_system_prompt", "FIRST_USER_PROMPT")],
        )
        resolver.resolve(
            agent_type="coordinator_planner_supervisor",
            setting_key="coordinator_system_prompt",
            default_template="DEFAULT",
        )
        args, kwargs = setting_service.get_agent_settings.call_args
        assert (args and args[0] == "first") or kwargs.get("agent_id") == "first"
