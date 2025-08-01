from datetime import datetime
from uuid import uuid4

from typing_extensions import Iterator

from app.domain.exceptions.base import NotFoundError
from app.domain.models import Message
from app.infrastructure.database.sql import Database


class MessageRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def get_all(self, agent_id: str, schema: str) -> Iterator[Message]:
        with self.db.session(schema_name=schema) as session:
            return (
                session.query(Message)
                .filter(Message.agent_id == agent_id, Message.is_active)
                .all()
            )

    def get_by_id(self, message_id: str, schema: str) -> Message:
        with self.db.session(schema_name=schema) as session:
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
        schema: str,
        response_data: dict = None,
        attachment_id: str = None,
        replies_to: Message = None,
    ) -> Message:
        gen_id = uuid4()
        with self.db.session(schema_name=schema) as session:
            message = Message(
                id=str(gen_id),
                is_active=True,
                created_at=datetime.now(),
                message_role=message_role,
                message_content=message_content,
                agent_id=agent_id,
                response_data=response_data,
                attachment_id=attachment_id,
                replies_to=replies_to.id if replies_to is not None else None,
            )
            session.add(message)
            session.commit()
            session.refresh(message)
            return message

    def delete_by_id(self, message_id: str, schema: str) -> None:
        with self.db.session(schema_name=schema) as session:
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
