from unittest.mock import MagicMock

import pytest

from app.domain.models import LanguageModelSetting
from app.services.language_model_settings import LanguageModelSettingService


@pytest.fixture
def lm_setting_service():
    repo = MagicMock()
    service = LanguageModelSettingService(language_model_setting_repository=repo)
    return service, repo


class TestLanguageModelSettingService:
    def test_get_language_model_settings(self, lm_setting_service):
        service, repo = lm_setting_service
        expected = [MagicMock(spec=LanguageModelSetting)]
        repo.get_all.return_value = expected

        result = service.get_language_model_settings(
            language_model_id="lm-1", schema="test"
        )

        assert result == expected
        repo.get_all.assert_called_once_with("lm-1", "test")

    def test_create_language_model_setting(self, lm_setting_service):
        service, repo = lm_setting_service
        setting = MagicMock(spec=LanguageModelSetting)
        repo.add.return_value = setting

        result = service.create_language_model_setting(
            language_model_id="lm-1",
            setting_key="temperature",
            setting_value="0.7",
            schema="test",
        )

        assert result == setting
        repo.add.assert_called_once_with(
            language_model_id="lm-1",
            setting_key="temperature",
            setting_value="0.7",
            schema="test",
        )

    def test_update_by_key(self, lm_setting_service):
        service, repo = lm_setting_service
        setting = MagicMock(spec=LanguageModelSetting)
        repo.update_by_key.return_value = setting

        result = service.update_by_key(
            language_model_id="lm-1",
            setting_key="temperature",
            setting_value="0.9",
            schema="test",
        )

        assert result == setting
        repo.update_by_key.assert_called_once_with(
            language_model_id="lm-1",
            setting_key="temperature",
            setting_value="0.9",
            schema="test",
        )
