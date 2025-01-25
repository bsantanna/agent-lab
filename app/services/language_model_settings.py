from typing import Iterator

from app.domain.models import LanguageModelSetting
from app.domain.repositories.language_models import LanguageModelSettingRepository


class LanguageModelSettingService:
    def __init__(
        self, language_model_setting_repository: LanguageModelSettingRepository
    ) -> None:
        self.repository: LanguageModelSettingRepository = (
            language_model_setting_repository
        )

    def get_language_model_settings(
        self, language_model_id: str
    ) -> Iterator[LanguageModelSetting]:
        return self.repository.get_all(model_id=language_model_id)

    def create_language_model_setting(
        self, language_model_id: str, setting_key: str, setting_value: str
    ) -> LanguageModelSetting:
        return self.repository.add(
            language_model_id=language_model_id,
            setting_key=setting_key,
            setting_value=setting_value,
        )

    def update_by_key(
        self, language_model_id: str, setting_key: str, setting_value: str
    ) -> LanguageModelSetting:
        return self.repository.update_by_key(
            language_model_id=language_model_id,
            setting_key=setting_key,
            setting_value=setting_value,
        )
