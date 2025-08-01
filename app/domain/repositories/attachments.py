from datetime import datetime
from uuid import uuid4


from app.domain.exceptions.base import NotFoundError
from app.domain.models import Attachment
from app.infrastructure.database.sql import Database


class AttachmentRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def get_by_id(self, attachment_id: str, schema: str) -> Attachment:
        with self.db.session(schema_name=schema) as session:
            attachment = (
                session.query(Attachment)
                .filter(Attachment.id == attachment_id, Attachment.is_active)
                .first()
            )
            if not attachment:
                raise AttachmentNotFoundError(attachment_id)
            return attachment

    def add(
        self,
        file_name: str,
        raw_content: bytes,
        parsed_content: str,
        schema: str,
        attachment_id: str = None,
    ) -> Attachment:
        if attachment_id is None:
            attachment_id = str(uuid4())

        with self.db.session(schema_name=schema) as session:
            attachment = Attachment(
                id=attachment_id,
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

    def delete_by_id(self, attachment_id: str, schema: str) -> None:
        with self.db.session(schema_name=schema) as session:
            entity: Attachment = (
                session.query(Attachment)
                .filter(Attachment.id == attachment_id, Attachment.is_active)
                .first()
            )
            if not entity:
                raise AttachmentNotFoundError(attachment_id)
            session.delete(entity)
            session.commit()

    def update_attachment(
        self, attachment_id: str, embeddings_collection: str, schema: str
    ) -> Attachment:
        with self.db.session(schema_name=schema) as session:
            entity: Attachment = (
                session.query(Attachment)
                .filter(Attachment.id == attachment_id, Attachment.is_active)
                .first()
            )
            if not entity:
                raise AttachmentNotFoundError(attachment_id)

            entity.embeddings_collection = embeddings_collection
            session.commit()
            session.refresh(entity)
            return entity


class AttachmentNotFoundError(NotFoundError):
    entity_name: str = "Attachment"
