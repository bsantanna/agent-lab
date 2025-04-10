import os
from uuid import uuid4

import hvac
from fastapi import File
from langchain_community.document_loaders import UnstructuredMarkdownLoader
from langchain_ollama import OllamaEmbeddings
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import CharacterTextSplitter
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

        if not file.content_type.startswith("audio/"):
            parsed_content = raw_content.decode("utf-8").text_content
        else:
            parsed_content = ""

        attachment = self.attachment_repository.add(
            file_name=file.filename,
            raw_content=raw_content,
            parsed_content=parsed_content,
        )

        os.remove(temp_file_path)

        return attachment

    def delete_attachment_by_id(self, attachment_id: str) -> None:
        return self.attachment_repository.delete_by_id(attachment_id)

    async def create_embeddings(
        self, attachment_id: str, language_model_id: str, collection_name: str
    ) -> Attachment:
        language_model = self.language_model_service.get_language_model_by_id(
            language_model_id
        )
        lm_settings = self.language_model_setting_service.get_language_model_settings(
            language_model.id
        )
        lm_settings_dict = {
            setting.setting_key: setting.setting_value for setting in lm_settings
        }

        integration = self.integration_service.get_integration_by_id(
            language_model.integration_id
        )
        secrets = self.vault_client.secrets.kv.read_secret_version(
            path=f"integration_{integration.id}", raise_on_deleted_version=False
        )

        api_endpoint = secrets["data"]["data"]["api_endpoint"]
        api_key = secrets["data"]["data"]["api_key"]

        if integration.integration_type == "openai_api_v1":
            embeddings_model = OpenAIEmbeddings(
                model=lm_settings_dict["embeddings"],
                openai_api_base=api_endpoint,
                openai_api_key=api_key,
            )
        # not available
        # elif integration.integration_type == "xai_api_v1":
        #    embeddings_model = OpenAIEmbeddings(
        #       model=lm_settings_dict["embeddings"],
        #       base_url=api_endpoint,
        #       api_key=api_key
        #    )
        elif integration.integration_type == "ollama_api_v1":
            embeddings_model = OllamaEmbeddings(
                model=lm_settings_dict["embeddings"], base_url=api_endpoint
            )
        else:
            embeddings_model = OllamaEmbeddings(
                model=lm_settings_dict["embeddings"],
                base_url=f"{os.getenv('OLLAMA_ENDPOINT')}",
            )

        attachment = self.attachment_repository.get_by_id(attachment_id)
        temp_file_path = f"temp-{uuid4()}"
        with open(temp_file_path, "wb") as buffer:
            buffer.write(attachment.parsed_content.encode())

        loader = UnstructuredMarkdownLoader(temp_file_path)
        documents = loader.load_and_split(
            CharacterTextSplitter(chunk_size=512, chunk_overlap=64)
        )
        self.document_repository.add(embeddings_model, collection_name, documents)
        updated_attachment = self.attachment_repository.update_attachment(
            attachment_id, collection_name
        )

        os.remove(temp_file_path)
        return updated_attachment
