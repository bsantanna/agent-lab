from typing import Iterator

from app.application.services.integrations import IntegrationService
from app.domain.exceptions.base import InvalidFieldError
from app.domain.models import LanguageModel, LanguageModelSetting
from app.domain.repositories.integrations import IntegrationNotFoundError
from app.domain.repositories.language_models import (
    LanguageModelRepository,
    LanguageModelSettingRepository,
)


class LanguageModelSettingService:
    def __init__(
        self, language_model_setting_repository: LanguageModelSettingRepository
    ) -> None:
        self._repository: LanguageModelSettingRepository = (
            language_model_setting_repository
        )

    def get_language_model_settings(
        self, language_model_id: str
    ) -> Iterator[LanguageModelSetting]:
        return self._repository.get_all(model_id=language_model_id)

    def get_language_model_setting_by_id(
        self, language_model_setting_id: int
    ) -> LanguageModelSetting:
        return self._repository.get_by_id(language_model_setting_id)

    def create_language_model_setting(
        self, language_model_id: str, setting_key: str, setting_value: str
    ) -> LanguageModelSetting:
        return self._repository.add(
            language_model_id=language_model_id,
            setting_key=setting_key,
            setting_value=setting_value,
        )

    def delete_language_model_setting_by_id(
        self, language_model_setting_id: int
    ) -> None:
        return self._repository.delete_by_id(language_model_setting_id)


class LanguageModelService:
    def __init__(
        self,
        language_model_repository: LanguageModelRepository,
        language_model_setting_service: LanguageModelSettingService,
        integration_service: IntegrationService,
    ) -> None:
        self._repository: LanguageModelRepository = language_model_repository
        self._setting_service = language_model_setting_service
        self._integration_service = integration_service

    def get_language_models(self) -> Iterator[LanguageModel]:
        return self._repository.get_all()

    def get_language_model_by_id(self, language_model_id: int) -> LanguageModel:
        return self._repository.get_by_id(language_model_id)

    def create_language_model(
        self,
        integration_id: str,
        language_model_tag: str,
    ) -> LanguageModel:
        # verify integration
        try:
            self._integration_service.get_integration_by_id(integration_id)
        except IntegrationNotFoundError:
            raise InvalidFieldError(
                field_name="integration_id", reason="integration not found"
            )

        # create language model
        language_model = self._repository.add(
            integration_id=integration_id, language_model_tag=language_model_tag
        )

        # default temperature setting
        self._setting_service.create_language_model_setting(
            language_model_id=language_model.id,
            setting_key="temperature",
            setting_value="0.5",
        )

        return language_model

    def delete_language_model_by_id(self, language_model_id: int) -> None:
        return self._repository.delete_by_id(language_model_id)
