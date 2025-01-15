from typing import Iterator
from uuid import uuid4

from app.domain.models import Attachment
from app.domain.repositories.attachments import AttachmentRepository


class AttachmentService:
    def __init__(self, attachment_repository: AttachmentRepository) -> None:
        self._repository: AttachmentRepository = attachment_repository

    def get_attachments(self) -> Iterator[Attachment]:
        return self._repository.get_all()

    def get_attachment_by_id(self, attachment_id: int) -> Attachment:
        return self._repository.get_by_id(attachment_id)

    def create_attachment(self) -> Attachment:
        uid = uuid4()
        return self._repository.add(email=f"{uid}@email.com", password="pwd")

    def delete_attachment_by_id(self, attachment_id: int) -> None:
        return self._repository.delete_by_id(attachment_id)
