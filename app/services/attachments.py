import os
from uuid import uuid4

from fastapi import File
from markitdown import MarkItDown

from app.domain.models import Attachment
from app.domain.repositories.attachments import AttachmentRepository


class AttachmentService:
    def __init__(
        self, attachment_repository: AttachmentRepository, markdown: MarkItDown
    ) -> None:
        self.repository: AttachmentRepository = attachment_repository
        self.markdown: MarkItDown = markdown

    def get_attachment_by_id(self, attachment_id: str) -> Attachment:
        return self.repository.get_by_id(attachment_id)

    async def create_attachment(self, file: File) -> Attachment:
        temp_file_path = f"temp-{uuid4()}"

        with open(temp_file_path, "wb") as buffer:
            raw_content = await file.read()
            buffer.write(raw_content)

        parsed_content = self.markdown.convert(temp_file_path)

        attachment = self.repository.add(
            file_name=file.filename,
            raw_content=raw_content,
            parsed_content=parsed_content.text_content,
        )

        os.remove(temp_file_path)

        return attachment

    def delete_attachment_by_id(self, attachment_id: str) -> None:
        return self.repository.delete_by_id(attachment_id)
