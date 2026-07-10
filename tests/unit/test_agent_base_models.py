from unittest.mock import MagicMock

import pytest
from langchain_openai import ChatOpenAI

from app.domain.exceptions.base import ConfigurationError
from app.services.agent_types.test_echo.test_echo_agent import (
    TestEchoAgent as EchoAgent,
)


def _make_agent(integration_type: str) -> EchoAgent:
    agent = EchoAgent(agent_utils=MagicMock())
    agent.agent_service = MagicMock()
    integration = MagicMock()
    integration.integration_type = integration_type
    agent.get_language_model_integration = MagicMock(
        return_value=(MagicMock(), integration)
    )
    agent.get_integration_credentials = MagicMock(
        return_value=("https://example.com", "api-key")
    )
    return agent


class TestGetChatModel:
    def test_openai_integration_returns_chat_openai(self):
        agent = _make_agent("openai_api_v1")

        chat_model = agent.get_chat_model("agent-1", "test", "gpt-4o")

        assert isinstance(chat_model, ChatOpenAI)

    def test_unsupported_integration_type_raises(self):
        agent = _make_agent("ollama_api_v1")

        with pytest.raises(ConfigurationError):
            agent.get_chat_model("agent-1", "test", "some-model")
