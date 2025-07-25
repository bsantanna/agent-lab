from typing_extensions import Iterator

from app.domain.models import LanguageModel
from app.domain.repositories.language_models import LanguageModelRepository
from app.services.integrations import IntegrationService
from app.services.language_model_settings import LanguageModelSettingService


class LanguageModelService:
    def __init__(
        self,
        language_model_repository: LanguageModelRepository,
        language_model_setting_service: LanguageModelSettingService,
        integration_service: IntegrationService,
    ) -> None:
        self.repository: LanguageModelRepository = language_model_repository
        self.setting_service = language_model_setting_service
        self.integration_service = integration_service

    def get_language_models(self) -> Iterator[LanguageModel]:
        return self.repository.get_all()

    def get_language_model_by_id(self, language_model_id: str) -> LanguageModel:
        return self.repository.get_by_id(language_model_id)

    def create_language_model(
        self,
        integration_id: str,
        language_model_tag: str,
    ) -> LanguageModel:
        # get integration
        integration = self.integration_service.get_integration_by_id(integration_id)

        # create language model
        language_model = self.repository.add(
            integration_id=integration.id, language_model_tag=language_model_tag
        )

        # default embeddings model setting
        if integration.integration_type == "openai_api_v1":
            self.setting_service.create_language_model_setting(
                language_model_id=language_model.id,
                setting_key="embeddings",
                setting_value="text-embedding-3-large",
            )
        else:
            self.setting_service.create_language_model_setting(
                language_model_id=language_model.id,
                setting_key="embeddings",
                setting_value="bge-m3",
            )

        return language_model

    def delete_language_model_by_id(self, language_model_id: str) -> None:
        return self.repository.delete_by_id(language_model_id)

    def update_language_model(
        self, language_model_id: str, language_model_tag: str, integration_id: str
    ) -> LanguageModel:
        integration = self.integration_service.get_integration_by_id(integration_id)
        return self.repository.update_language_model(
            language_model_id=language_model_id,
            language_model_tag=language_model_tag,
            integration_id=integration.id,
        )
