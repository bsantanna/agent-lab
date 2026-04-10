from unittest.mock import MagicMock, patch

import pytest

from app.interface.mcp.server import (
    AgentItem,
    MessageItem,
    PostMessageResult,
    _build_auth,
    _read_prompt,
    _make_prompt_fn,
    _AGENT_TYPE_PROMPTS,
    _PROMPTS_BASE,
)


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
    @patch("app.interface.mcp.server.get_access_token", return_value=None)
    def test_get_mcp_schema_no_token(self, mock_token):
        from app.interface.mcp.server import _get_mcp_schema

        result = _get_mcp_schema()
        assert result == "public"

    @patch("app.interface.mcp.server.get_access_token")
    def test_get_mcp_schema_with_token(self, mock_token):
        from app.interface.mcp.server import _get_mcp_schema

        mock_token.return_value = MagicMock(claims={"sub": "abc-def-123"})
        result = _get_mcp_schema()
        assert result == "id_abc_def_123"

    @patch("app.interface.mcp.server.get_access_token")
    def test_get_mcp_schema_token_no_sub(self, mock_token):
        from app.interface.mcp.server import _get_mcp_schema

        mock_token.return_value = MagicMock(claims={})
        result = _get_mcp_schema()
        assert result == "public"


class TestPromptHelpers:
    def test_read_prompt_returns_content(self):
        prompt_file = "adaptive_rag/default_execution_system_prompt.txt"
        content = _read_prompt(prompt_file)
        assert isinstance(content, str)
        assert len(content) > 0

    def test_read_prompt_nonexistent_raises(self):
        with pytest.raises(FileNotFoundError):
            _read_prompt("nonexistent/file.txt")

    def test_make_prompt_fn_returns_callable(self):
        prompt_file = "adaptive_rag/default_execution_system_prompt.txt"
        fn = _make_prompt_fn(prompt_file)
        assert callable(fn)
        result = fn()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_agent_type_prompts_structure(self):
        for agent_type, info in _AGENT_TYPE_PROMPTS.items():
            assert "description" in info
            assert "prompt_file" in info
            if info["prompt_file"] is not None:
                full_path = _PROMPTS_BASE / info["prompt_file"]
                assert full_path.exists(), f"Prompt file missing for {agent_type}: {full_path}"
