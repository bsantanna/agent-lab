from unittest.mock import MagicMock

import pytest

from app.domain.exceptions.base import InvalidFieldError
from app.domain.models import Agent, Message
from app.domain.repositories.agents import AgentNotFoundError
from app.services.messages import MessageService


@pytest.fixture
def message_service():
    repo = MagicMock()
    agent_service = MagicMock()
    attachment_service = MagicMock()
    service = MessageService(
        message_repository=repo,
        agent_service=agent_service,
        attachment_service=attachment_service,
    )
    return service, repo, agent_service, attachment_service


class TestMessageService:
    def test_get_messages(self, message_service):
        service, repo, agent_service, _ = message_service
        agent = MagicMock(spec=Agent)
        agent.id = "agent-1"
        agent_service.get_agent_by_id.return_value = agent
        expected = [MagicMock(spec=Message)]
        repo.get_all.return_value = expected

        result = service.get_messages(agent_id="agent-1", schema="test")

        assert result == expected
        agent_service.get_agent_by_id.assert_called_once_with("agent-1", "test")
        repo.get_all.assert_called_once_with("agent-1", "test")

    def test_get_message_by_id(self, message_service):
        service, repo, _, _ = message_service
        message = MagicMock(spec=Message)
        repo.get_by_id.return_value = message

        result = service.get_message_by_id(message_id="msg-1", schema="test")

        assert result == message
        repo.get_by_id.assert_called_once_with("msg-1", "test")

    def test_create_message(self, message_service):
        service, repo, agent_service, _ = message_service
        agent = MagicMock(spec=Agent)
        agent_service.get_agent_by_id.return_value = agent
        message = MagicMock(spec=Message)
        repo.add.return_value = message

        result = service.create_message(
            message_role="human",
            message_content="Hello",
            agent_id="agent-1",
            schema="test",
        )

        assert result == message
        agent_service.get_agent_by_id.assert_called_once_with("agent-1", "test")
        repo.add.assert_called_once_with(
            message_role="human",
            message_content="Hello",
            agent_id="agent-1",
            schema="test",
            response_data=None,
            attachment_id=None,
            replies_to=None,
        )

    def test_create_message_with_optional_fields(self, message_service):
        service, repo, agent_service, _ = message_service
        agent = MagicMock(spec=Agent)
        agent_service.get_agent_by_id.return_value = agent
        parent = MagicMock(spec=Message)
        message = MagicMock(spec=Message)
        repo.add.return_value = message

        result = service.create_message(
            message_role="assistant",
            message_content="Reply",
            agent_id="agent-1",
            schema="test",
            response_data={"key": "value"},
            attachment_id="att-1",
            replies_to=parent,
        )

        assert result == message
        repo.add.assert_called_once_with(
            message_role="assistant",
            message_content="Reply",
            agent_id="agent-1",
            schema="test",
            response_data={"key": "value"},
            attachment_id="att-1",
            replies_to=parent,
        )

    def test_create_message_agent_not_found(self, message_service):
        service, repo, agent_service, _ = message_service
        agent_service.get_agent_by_id.side_effect = AgentNotFoundError("agent-1")

        with pytest.raises(InvalidFieldError) as exc_info:
            service.create_message(
                message_role="human",
                message_content="Hello",
                agent_id="agent-1",
                schema="test",
            )

        assert exc_info.value.status_code == 400
        repo.add.assert_not_called()

    def test_delete_message_by_id_no_reply(self, message_service):
        service, repo, _, _ = message_service
        message = MagicMock(spec=Message)
        message.replies_to = None
        repo.get_by_id.return_value = message

        service.delete_message_by_id(message_id="msg-1", schema="test")

        repo.delete_by_id.assert_called_once_with("msg-1", "test")

    def test_delete_message_by_id_with_reply(self, message_service):
        service, repo, _, _ = message_service
        message = MagicMock(spec=Message)
        message.replies_to = "reply-msg-id"
        repo.get_by_id.return_value = message

        service.delete_message_by_id(message_id="msg-1", schema="test")

        assert repo.delete_by_id.call_count == 2
        repo.delete_by_id.assert_any_call("reply-msg-id", "test")
        repo.delete_by_id.assert_any_call("msg-1", "test")
