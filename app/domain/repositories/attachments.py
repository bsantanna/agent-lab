from contextlib import AbstractContextManager
from typing import Callable, Iterator

from sqlalchemy.orm import Session

from app.domain.exceptions.base import NotFoundError
from app.domain.models import Attachment


class AttachmentRepository:
    def __init__(
        self, session_factory: Callable[..., AbstractContextManager[Session]]
    ) -> None:
        self.session_factory = session_factory

    def get_all(self) -> Iterator[Attachment]:
        with self.session_factory() as session:
            return session.query(Attachment).all()

    def get_by_id(self, attachment_id: int) -> Attachment:
        with self.session_factory() as session:
            attachment = (
                session.query(Attachment).filter(Attachment.id == attachment_id).first()
            )
            if not attachment:
                raise AttachmentNotFoundError(attachment_id)
            return attachment

    def add(self, email: str, password: str, is_active: bool = True) -> Attachment:
        with self.session_factory() as session:
            attachment = Attachment(
                email=email, hashed_password=password, is_active=is_active
            )
            session.add(attachment)
            session.commit()
            session.refresh(attachment)
            return attachment

    def delete_by_id(self, attachment_id: int) -> None:
        with self.session_factory() as session:
            entity: Attachment = (
                session.query(Attachment).filter(Attachment.id == attachment_id).first()
            )
            if not entity:
                raise AttachmentNotFoundError(attachment_id)
            session.delete(entity)
            session.commit()


class AttachmentNotFoundError(NotFoundError):
    entity_name: str = "Attachment"
