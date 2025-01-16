from typing import Iterator

from app.domain.models import Message
from app.domain.repositories.messages import MessageRepository


class MessageService:
    def __init__(self, message_repository: MessageRepository) -> None:
        self._repository: MessageRepository = message_repository

    def get_messages(self, agent_id: str) -> Iterator[Message]:
        return self._repository.get_all(agent_id)

    def get_message_by_id(self, message_id: str) -> Message:
        return self._repository.get_by_id(message_id)

    def create_message(
        self,
        message_role: str,
        message_content: str,
        agent_id: str,
        attachment_id: str = None,
    ) -> Message:
        return self._repository.add(
            message_role=message_role,
            message_content=message_content,
            agent_id=agent_id,
            attachment_id=attachment_id,
        )

    def delete_message_by_id(self, message_id: str) -> None:
        return self._repository.delete_by_id(message_id)
