from unittest.mock import MagicMock

from agent_lab.interface.api.messages.schema import MessageRequest
from agent_lab.services.agent_types.test_echo.test_echo_agent import TestEchoAgent


def test_get_input_params_dumps_the_message_request():
    agent = TestEchoAgent(agent_utils=MagicMock())
    request = MessageRequest(
        message_role="human", message_content="hi", agent_id="agent-1"
    )

    assert agent.get_input_params(request, schema="public") == {
        "message_role": "human",
        "message_content": "hi",
        "agent_id": "agent-1",
        "attachment_id": None,
    }
