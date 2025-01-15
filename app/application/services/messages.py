from typing import Iterator
from uuid import uuid4

from app.domain.models import Message
from app.domain.repositories.messages import MessageRepository


class MessageService:
    def __init__(self, message_repository: MessageRepository) -> None:
        self._repository: MessageRepository = message_repository

    def get_messages(self) -> Iterator[Message]:
        return self._repository.get_all()

    def get_message_by_id(self, message_id: int) -> Message:
        return self._repository.get_by_id(message_id)

    def create_message(self) -> Message:
        uid = uuid4()
        return self._repository.add(email=f"{uid}@email.com", password="pwd")

    def delete_message_by_id(self, message_id: int) -> None:
        return self._repository.delete_by_id(message_id)
