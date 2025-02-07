from contextlib import AbstractContextManager
from datetime import datetime
from typing_extensions import Callable
from uuid import uuid4

from sqlalchemy.orm import Session

from app.domain.exceptions.base import NotFoundError
from app.domain.models import Attachment


class AttachmentRepository:
    def __init__(
        self, session_factory: Callable[..., AbstractContextManager[Session]]
    ) -> None:
        self.session_factory = session_factory

    def get_by_id(self, attachment_id: str) -> Attachment:
        with self.session_factory() as session:
            attachment = (
                session.query(Attachment)
                .filter(Attachment.id == attachment_id, Attachment.is_active)
                .first()
            )
            if not attachment:
                raise AttachmentNotFoundError(attachment_id)
            return attachment

    def add(
        self, file_name: str, raw_content: bytes, parsed_content: str
    ) -> Attachment:
        gen_id = uuid4()
        with self.session_factory() as session:
            attachment = Attachment(
                id=str(gen_id),
                is_active=True,
                created_at=datetime.now(),
                file_name=file_name,
                raw_content=raw_content,
                parsed_content=parsed_content,
            )
            session.add(attachment)
            session.commit()
            session.refresh(attachment)
            return attachment

    def delete_by_id(self, attachment_id: str) -> None:
        with self.session_factory() as session:
            entity: Attachment = (
                session.query(Attachment)
                .filter(Attachment.id == attachment_id, Attachment.is_active)
                .first()
            )
            if not entity:
                raise AttachmentNotFoundError(attachment_id)
            session.delete(entity)
            session.commit()

    def update_attachment(self, attachment_id: str, embeddings_id: str) -> Attachment:
        with self.session_factory() as session:
            entity: Attachment = (
                session.query(Attachment)
                .filter(Attachment.id == attachment_id, Attachment.is_active)
                .first()
            )
            if not entity:
                raise AttachmentNotFoundError(attachment_id)

            entity.embeddings_id = embeddings_id
            session.commit()
            session.refresh(entity)
            return entity


class AttachmentNotFoundError(NotFoundError):
    entity_name: str = "Attachment"
