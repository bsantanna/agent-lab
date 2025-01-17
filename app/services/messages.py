from typing import Iterator

from app.domain.exceptions.base import InvalidFieldError
from app.domain.models import Message
from app.domain.repositories.agents import AgentNotFoundError
from app.domain.repositories.messages import MessageRepository
from app.services.agents import AgentService


class MessageService:
    def __init__(
        self, message_repository: MessageRepository, agent_service: AgentService
    ) -> None:
        self._repository: MessageRepository = message_repository
        self._agent_service: AgentService = agent_service

    def get_messages(self, agent_id: str) -> Iterator[Message]:
        # verify agent
        try:
            self._agent_service.get_agent_by_id(agent_id)
        except AgentNotFoundError:
            raise InvalidFieldError(field_name="agent_id", reason="agent not found")
        return self._repository.get_all(agent_id)

    def get_message_by_id(self, message_id: str) -> Message:
        return self._repository.get_by_id(message_id)

    def create_message(
        self,
        message_role: str,
        message_content: str,
        agent_id: str,
        attachment_id: str = None,
        replies_to: Message = None,
    ) -> Message:
        # verify agent
        try:
            self._agent_service.get_agent_by_id(agent_id)
        except AgentNotFoundError:
            raise InvalidFieldError(field_name="agent_id", reason="agent not found")

        return self._repository.add(
            message_role=message_role,
            message_content=message_content,
            agent_id=agent_id,
            attachment_id=attachment_id,
            replies_to=replies_to,
        )

    def delete_message_by_id(self, message_id: str) -> None:
        return self._repository.delete_by_id(message_id)
