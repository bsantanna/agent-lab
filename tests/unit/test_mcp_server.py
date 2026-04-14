from unittest.mock import MagicMock, patch

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
