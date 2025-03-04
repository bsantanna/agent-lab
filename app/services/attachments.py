import os
from uuid import uuid4

from fastapi import File
from markitdown import MarkItDown

from app.domain.models import Attachment
from app.domain.repositories.attachments import AttachmentRepository
from app.infrastructure.database.vectors import DocumentRepository
from app.services.language_model_settings import LanguageModelSettingService
from app.services.language_models import LanguageModelService


class AttachmentService:
    def __init__(
        self,
        attachment_repository: AttachmentRepository,
        document_repository: DocumentRepository,
        language_model_service: LanguageModelService,
        language_model_setting_service: LanguageModelSettingService,
        markdown: MarkItDown,
    ) -> None:
        self.attachment_repository = attachment_repository
        self.document_repository = document_repository
        self.language_model_service = language_model_service
        self.language_model_setting_service = language_model_setting_service
        self.markdown = markdown

    def get_attachment_by_id(self, attachment_id: str) -> Attachment:
        return self.attachment_repository.get_by_id(attachment_id)

    async def create_attachment(self, file: File) -> Attachment:
        temp_file_path = f"temp-{uuid4()}"

        with open(temp_file_path, "wb") as buffer:
            raw_content = await file.read()
            buffer.write(raw_content)

        parsed_content = self.markdown.convert(temp_file_path)

        attachment = self.attachment_repository.add(
            file_name=file.filename,
            raw_content=raw_content,
            parsed_content=parsed_content.text_content,
        )

        os.remove(temp_file_path)

        return attachment

    def delete_attachment_by_id(self, attachment_id: str) -> None:
        return self.attachment_repository.delete_by_id(attachment_id)

    def create_embeddings(
        self, attachment_id: str, language_model_id: str
    ) -> Attachment:
        # TODO get attachment, get language model, get language model setting, get embedding model
        # generate embedding, store embedding, format result
        pass
