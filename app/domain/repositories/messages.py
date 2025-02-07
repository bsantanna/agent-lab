from contextlib import AbstractContextManager
from datetime import datetime
from typing_extensions import Callable, Iterator
from uuid import uuid4

from sqlalchemy.orm import Session

from app.domain.exceptions.base import NotFoundError
from app.domain.models import Message


class MessageRepository:
    def __init__(
        self, session_factory: Callable[..., AbstractContextManager[Session]]
    ) -> None:
        self.session_factory = session_factory

    def get_all(self, agent_id: str) -> Iterator[Message]:
        with self.session_factory() as session:
            return (
                session.query(Message)
                .filter(Message.agent_id == agent_id, Message.is_active)
                .all()
            )

    def get_by_id(self, message_id: str) -> Message:
        with self.session_factory() as session:
            message = (
                session.query(Message)
                .filter(Message.id == message_id, Message.is_active)
                .first()
            )
            if not message:
                raise MessageNotFoundError(message_id)
            return message

    def add(
        self,
        message_content: str,
        message_role: str,
        agent_id: str,
        attachment_id: str = None,
        replies_to: Message = None,
    ) -> Message:
        gen_id = uuid4()
        with self.session_factory() as session:
            message = Message(
                id=str(gen_id),
                is_active=True,
                created_at=datetime.now(),
                message_role=message_role,
                message_content=message_content,
                agent_id=agent_id,
                attachment_id=attachment_id,
                replies_to=replies_to.id if replies_to is not None else None,
            )
            session.add(message)
            session.commit()
            session.refresh(message)
            return message

    def delete_by_id(self, message_id: str) -> None:
        with self.session_factory() as session:
            entity: Message = (
                session.query(Message)
                .filter(Message.id == message_id, Message.is_active)
                .first()
            )
            if not entity:
                raise MessageNotFoundError(message_id)

            entity.is_active = False
            session.commit()


class MessageNotFoundError(NotFoundError):
    entity_name: str = "Message"
