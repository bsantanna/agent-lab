import os
from uuid import uuid4

import hvac
from fastapi import File
from langchain_ollama import OllamaEmbeddings
from langchain_openai import OpenAIEmbeddings
from markitdown import MarkItDown

from app.domain.models import Attachment
from app.domain.repositories.attachments import AttachmentRepository
from app.infrastructure.database.vectors import DocumentRepository
from app.services.integrations import IntegrationService
from app.services.language_model_settings import LanguageModelSettingService
from app.services.language_models import LanguageModelService


class AttachmentService:
    def __init__(
        self,
        attachment_repository: AttachmentRepository,
        document_repository: DocumentRepository,
        language_model_service: LanguageModelService,
        language_model_setting_service: LanguageModelSettingService,
        integration_service: IntegrationService,
        vault_client: hvac.Client,
        markdown: MarkItDown,
    ) -> None:
        self.attachment_repository = attachment_repository
        self.document_repository = document_repository
        self.language_model_service = language_model_service
        self.language_model_setting_service = language_model_setting_service
        self.integration_service = integration_service
        self.vault_client = vault_client
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

        language_model = self.language_model_service.get_language_model_by_id(language_model_id)
        lm_settings=self.language_model_setting_service.get_language_model_settings(language_model.id)
        lm_settings_dict = { setting.setting_key: setting.setting_value for setting in lm_settings }

        integration = self.integration_service.get_integration_by_id(language_model.integration_id)
        secrets = self.vault_client.secrets.kv.read_secret_version(
            path=f"integration_{integration.id}", raise_on_deleted_version=False
        )

        api_endpoint = secrets["data"]["data"]["api_endpoint"]
        api_key = secrets["data"]["data"]["api_key"]

        if integration.integration_type == "openai_api_v1":
            embeddings = OpenAIEmbeddings(
                model=lm_settings_dict["embeddings"],
                openai_api_base=api_endpoint,
                openai_api_key=api_key,
            )
        # not available
        # if integration.integration_type == "xai_api_v1":
        #    embeddings = OpenAIEmbeddings(
        #       model=lm_settings_dict["embeddings"],
        #       base_url=api_endpoint,
        #       api_key=api_key
        #    )
        else:
            embeddings = OllamaEmbeddings(
                model=lm_settings_dict["embeddings"],
                base_url=f"{os.getenv('OLLAMA_ENDPOINT')}",
            )

        attachment = self.attachment_repository.get_by_id(attachment_id)

        # TODO generate embedding, store embedding, format result
        pass
