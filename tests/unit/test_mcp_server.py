from unittest.mock import MagicMock, patch

import pytest

from app.interface.mcp.schema import (
    AgentItem,
    MessageItem,
    PostMessageResult,
    _get_mcp_schema,
)
from app.interface.mcp.server import _build_auth
from app.interface.mcp.registrar import McpRegistrar
from app.interface.mcp.default_tool_registrar import DefaultToolRegistrar


class TestMcpModels:
    def test_agent_item(self):
        item = AgentItem(
            id="a1",
            agent_name="Test Agent",
            agent_type="test_echo",
            agent_summary="An echo agent",
            language_model_id="lm1",
            is_active=True,
        )
        assert item.id == "a1"
        assert item.agent_name == "Test Agent"
        assert item.agent_type == "test_echo"
        assert item.is_active is True

    def test_message_item(self):
        item = MessageItem(
            id="m1",
            message_role="human",
            message_content="Hello",
            agent_id="a1",
        )
        assert item.id == "m1"
        assert item.response_data is None
        assert item.replies_to is None

    def test_message_item_with_optional_fields(self):
        item = MessageItem(
            id="m1",
            message_role="assistant",
            message_content="Hi there",
            agent_id="a1",
            response_data='{"key": "value"}',
            replies_to="m0",
        )
        assert item.response_data == '{"key": "value"}'
        assert item.replies_to == "m0"

    def test_post_message_result(self):
        result = PostMessageResult(
            id="m2",
            message_content="Response text",
            agent_id="a1",
        )
        assert result.id == "m2"
        assert result.response_data is None

    def test_post_message_result_with_response_data(self):
        result = PostMessageResult(
            id="m2",
            message_content="Response text",
            agent_id="a1",
            response_data="data",
        )
        assert result.response_data == "data"


class TestBuildAuth:
    def test_build_auth_disabled(self):
        config = {"auth": {"enabled": False}}
        result = _build_auth(config)
        assert result is None

    @patch("fastmcp.server.auth.providers.jwt.JWTVerifier")
    @patch("fastmcp.server.auth.OAuthProxy")
    def test_build_auth_enabled(self, mock_oauth, mock_jwt):
        config = {
            "auth": {
                "enabled": True,
                "url": "http://keycloak:8080",
                "realm": "test-realm",
                "client_id": "test-client",
                "client_secret": "test-secret",
            },
            "broker": {"url": "redis://localhost:6379"},
            "api_base_url": "http://localhost:8000",
        }

        _build_auth(config)

        mock_jwt.assert_called_once()
        mock_oauth.assert_called_once()
        call_kwargs = mock_oauth.call_args[1]
        assert "test-realm" in call_kwargs["upstream_authorization_endpoint"]
        assert "test-realm" in call_kwargs["upstream_token_endpoint"]
        assert call_kwargs["upstream_client_id"] == "test-client"
        assert call_kwargs["base_url"] == "http://localhost:8000/mcp"


class TestGetMcpSchema:
    @patch("app.interface.mcp.schema.get_access_token", return_value=None)
    def test_get_mcp_schema_no_token(self, mock_token):
        result = _get_mcp_schema()
        assert result == "public"

    @patch("app.interface.mcp.schema.get_access_token")
    def test_get_mcp_schema_with_token(self, mock_token):
        mock_token.return_value = MagicMock(claims={"sub": "abc-def-123"})
        result = _get_mcp_schema()
        assert result == "id_abc_def_123"

    @patch("app.interface.mcp.schema.get_access_token")
    def test_get_mcp_schema_token_no_sub(self, mock_token):
        mock_token.return_value = MagicMock(claims={})
        result = _get_mcp_schema()
        assert result == "public"


class TestMcpRegistrar:
    def test_base_registrar_no_ops(self):
        class NoOpRegistrar(McpRegistrar):
            pass

        registrar = NoOpRegistrar()
        mcp = MagicMock()
        container = MagicMock()
        registrar.register_tools(mcp, container)
        registrar.register_prompts(mcp)
        registrar.register_resources(mcp)

    def test_default_tool_registrar_is_mcp_registrar(self):
        assert issubclass(DefaultToolRegistrar, McpRegistrar)

    def test_default_tool_registrar_registers_tools(self):
        registrar = DefaultToolRegistrar()
        mcp = MagicMock()
        container = MagicMock()
        registrar.register_tools(mcp, container)
        tool_names = sorted(call[1]["name"] for call in mcp.tool.call_args_list)
        assert tool_names == ["get_agent_list", "get_message_list", "post_message"]

    def test_custom_registrar_overrides(self):
        class CustomRegistrar(McpRegistrar):
            def register_prompts(self, mcp):
                mcp.prompt(name="test_prompt")(lambda: "test")

        registrar = CustomRegistrar()
        mcp = MagicMock()
        container = MagicMock()
        registrar.register_prompts(mcp)
        mcp.prompt.assert_called_once_with(name="test_prompt")
        registrar.register_tools(mcp, container)
        registrar.register_resources(mcp)


def _registered_tools(container):
    """Register the default tools against a mock FastMCP and return the
    captured tool coroutines keyed by registration order."""
    mcp = MagicMock()
    DefaultToolRegistrar().register_tools(mcp, container)
    functions = [c.args[0] for c in mcp.tool.return_value.call_args_list]
    return dict(zip(["get_agent_list", "get_message_list", "post_message"], functions))


@patch("app.interface.mcp.default_tool_registrar._get_mcp_schema", return_value="test")
class TestDefaultToolClosures:
    @pytest.mark.asyncio
    async def test_get_agent_list(self, _schema):
        container = MagicMock()
        container.agent_service.return_value.get_agents.return_value = [
            MagicMock(
                id="a1",
                agent_name="Echo",
                agent_type="test_echo",
                agent_summary="echoes",
                language_model_id="lm1",
                is_active=True,
            )
        ]

        result = await _registered_tools(container)["get_agent_list"]()

        assert len(result) == 1
        assert result[0].id == "a1"
        assert result[0].agent_type == "test_echo"
        container.agent_service.return_value.get_agents.assert_called_once_with("test")

    @pytest.mark.asyncio
    async def test_get_message_list(self, _schema):
        container = MagicMock()
        container.message_service.return_value.get_messages.return_value = [
            MagicMock(
                id="m1",
                message_role="human",
                message_content="hi",
                agent_id="a1",
                response_data=None,
                replies_to=None,
            )
        ]

        result = await _registered_tools(container)["get_message_list"]("a1")

        assert len(result) == 1
        assert result[0].message_content == "hi"
        container.message_service.return_value.get_messages.assert_called_once_with(
            "a1", "test"
        )

    @pytest.mark.asyncio
    async def test_post_message(self, _schema):
        container = MagicMock()
        agent = MagicMock(agent_type="test_echo")
        container.agent_service.return_value.get_agent_by_id.return_value = agent
        matching_agent = container.agent_registry.return_value.get_agent.return_value
        matching_agent.process_message.return_value = MagicMock(
            message_content="echo: hi", response_data=None, agent_id="a1"
        )
        human_message = MagicMock(id="m1")
        assistant_message = MagicMock(
            id="m2", message_content="echo: hi", agent_id="a1", response_data=None
        )
        message_service = container.message_service.return_value
        message_service.create_message.side_effect = [human_message, assistant_message]

        result = await _registered_tools(container)["post_message"]("a1", "hi")

        assert result.id == "m2"
        assert result.message_content == "echo: hi"
        assert message_service.create_message.call_count == 2
        assert (
            message_service.create_message.call_args_list[1].kwargs["replies_to"]
            is human_message
        )
        matching_agent.process_message.assert_called_once()
