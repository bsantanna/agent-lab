from typing import Iterator
from uuid import uuid4

from app.domain.models import LanguageModel, LanguageModelSetting
from app.domain.repositories.language_models import (
    LanguageModelRepository,
    LanguageModelSettingRepository,
)


class LanguageModelService:
    def __init__(self, language_model_repository: LanguageModelRepository) -> None:
        self._repository: LanguageModelRepository = language_model_repository

    def get_language_models(self) -> Iterator[LanguageModel]:
        return self._repository.get_all()

    def get_language_model_by_id(self, language_model_id: int) -> LanguageModel:
        return self._repository.get_by_id(language_model_id)

    def create_language_model(self) -> LanguageModel:
        uid = uuid4()
        return self._repository.add(email=f"{uid}@email.com", password="pwd")

    def delete_language_model_by_id(self, language_model_id: int) -> None:
        return self._repository.delete_by_id(language_model_id)


class LanguageModelSettingService:
    def __init__(
        self, language_model_setting_repository: LanguageModelSettingRepository
    ) -> None:
        self._repository: LanguageModelSettingRepository = (
            language_model_setting_repository
        )

    def get_language_model_settings(self) -> Iterator[LanguageModelSetting]:
        return self._repository.get_all()

    def get_language_model_setting_by_id(
        self, language_model_setting_id: int
    ) -> LanguageModelSetting:
        return self._repository.get_by_id(language_model_setting_id)

    def create_language_model_setting(self) -> LanguageModelSetting:
        uid = uuid4()
        return self._repository.add(email=f"{uid}@email.com", password="pwd")

    def delete_language_model_setting_by_id(
        self, language_model_setting_id: int
    ) -> None:
        return self._repository.delete_by_id(language_model_setting_id)
