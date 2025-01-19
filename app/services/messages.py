from typing import Iterator

from app.domain.exceptions.base import InvalidFieldError
from app.domain.models import Message
from app.domain.repositories.agents import AgentNotFoundError
from app.domain.repositories.messages import MessageRepository
from app.services.agents import AgentService
from app.services.attachments import AttachmentService


class MessageService:
    def __init__(
        self,
        message_repository: MessageRepository,
        agent_service: AgentService,
        attachment_service: AttachmentService,
    ) -> None:
        self.repository: MessageRepository = message_repository
        self.agent_service: AgentService = agent_service
        self.attachment_service: AttachmentService = attachment_service

    def get_messages(self, agent_id: str) -> Iterator[Message]:
        # verify agent
        try:
            self.agent_service.get_agent_by_id(agent_id)
        except AgentNotFoundError:
            raise InvalidFieldError(field_name="agent_id", reason="agent not found")
        return self.repository.get_all(agent_id)

    def get_message_by_id(self, message_id: str) -> Message:
        return self.repository.get_by_id(message_id)

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
            self.agent_service.get_agent_by_id(agent_id)
        except AgentNotFoundError:
            raise InvalidFieldError(field_name="agent_id", reason="agent not found")

        return self.repository.add(
            message_role=message_role,
            message_content=message_content,
            agent_id=agent_id,
            attachment_id=attachment_id,
            replies_to=replies_to,
        )

    def delete_message_by_id(self, message_id: str) -> None:
        message = self.get_message_by_id(message_id)

        if message.replies_to is not None:
            parent_message = self.repository.get_by_id(message.replies_to)
            self.repository.delete_by_id(message.replies_to)
            if parent_message.attachment_id is not None:
                self.attachment_service.delete_attachment_by_id(
                    attachment_id=parent_message.attachment_id
                )

        else:
            raise InvalidFieldError(
                field_name="replies_to", reason="replies_to is None"
            )

        return self.repository.delete_by_id(message_id)
