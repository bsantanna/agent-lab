from contextlib import AbstractContextManager
from typing import Callable, Iterator

from sqlalchemy.orm import Session

from app.domain.exceptions.base import NotFoundError
from app.domain.models import Message


class MessageRepository:
    def __init__(
        self, session_factory: Callable[..., AbstractContextManager[Session]]
    ) -> None:
        self.session_factory = session_factory

    def get_all(self) -> Iterator[Message]:
        with self.session_factory() as session:
            return session.query(Message).all()

    def get_by_id(self, message_id: int) -> Message:
        with self.session_factory() as session:
            message = session.query(Message).filter(Message.id == message_id).first()
            if not message:
                raise MessageNotFoundError(message_id)
            return message

    def add(self, email: str, password: str, is_active: bool = True) -> Message:
        with self.session_factory() as session:
            message = Message(
                email=email, hashed_password=password, is_active=is_active
            )
            session.add(message)
            session.commit()
            session.refresh(message)
            return message

    def delete_by_id(self, message_id: int) -> None:
        with self.session_factory() as session:
            entity: Message = (
                session.query(Message).filter(Message.id == message_id).first()
            )
            if not entity:
                raise MessageNotFoundError(message_id)
            session.delete(entity)
            session.commit()


class MessageNotFoundError(NotFoundError):
    entity_name: str = "Message"
