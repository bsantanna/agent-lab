from typing_extensions import Iterator

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
        agent = self.agent_service.get_agent_by_id(agent_id)
        return self.repository.get_all(agent.id)

    def get_message_by_id(self, message_id: str) -> Message:
        return self.repository.get_by_id(message_id)

    def create_message(
        self,
        message_role: str,
        message_content: str,
        agent_id: str,
        response_data: dict = None,
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
            response_data=response_data,
            attachment_id=attachment_id,
            replies_to=replies_to,
        )

    def delete_message_by_id(self, message_id: str) -> None:
        message = self.get_message_by_id(message_id)
        if message.replies_to is not None:
            self.repository.delete_by_id(message.replies_to)
        return self.repository.delete_by_id(message_id)
