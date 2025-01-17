from fastapi import File
from markitdown import MarkItDown

from app.domain.models import Attachment
from app.domain.repositories.attachments import AttachmentRepository


class AttachmentService:
    def __init__(
        self, attachment_repository: AttachmentRepository, markdown: MarkItDown
    ) -> None:
        self._repository: AttachmentRepository = attachment_repository
        self._markdown: MarkItDown = markdown

    def get_attachment_by_id(self, attachment_id: str) -> Attachment:
        return self._repository.get_by_id(attachment_id)

    async def create_attachment(self, file: File) -> Attachment:
        temp_file_path = f"temp_{file.filename}"

        with open(temp_file_path, "wb") as buffer:
            raw_content = await file.read()
            buffer.write(raw_content)

        parsed_content = self._markdown.convert(temp_file_path)

        return self._repository.add(
            file_name=file.filename,
            raw_content=raw_content,
            parsed_content=parsed_content.text_content,
        )

    def delete_attachment_by_id(self, attachment_id: str) -> None:
        return self._repository.delete_by_id(attachment_id)
