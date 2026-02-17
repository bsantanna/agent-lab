from unittest.mock import MagicMock, patch

import pytest

from app.domain.models import LanguageModel, LanguageModelSetting
from app.domain.repositories.language_models import (
    LanguageModelNotFoundError,
    LanguageModelRepository,
    LanguageModelSettingNotFoundError,
    LanguageModelSettingRepository,
)


@pytest.fixture
def mock_db():
    db = MagicMock()
    session = MagicMock()
    db.session.return_value.__enter__ = MagicMock(return_value=session)
    db.session.return_value.__exit__ = MagicMock(return_value=False)
    return db, session


class TestLanguageModelRepository:
    def test_get_all(self, mock_db):
        db, session = mock_db
        repo = LanguageModelRepository(db=db)
        expected = [MagicMock(spec=LanguageModel)]
        session.query.return_value.filter.return_value.all.return_value = expected

        result = repo.get_all(schema="test_schema")

        assert result == expected

    def test_get_by_id_found(self, mock_db):
        db, session = mock_db
        repo = LanguageModelRepository(db=db)
        lm = MagicMock(spec=LanguageModel)
        session.query.return_value.filter.return_value.first.return_value = lm

        result = repo.get_by_id(language_model_id="lm-1", schema="test_schema")

        assert result == lm

    def test_get_by_id_not_found(self, mock_db):
        db, session = mock_db
        repo = LanguageModelRepository(db=db)
        session.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(LanguageModelNotFoundError):
            repo.get_by_id(language_model_id="nonexistent", schema="test_schema")

    @patch("app.domain.repositories.language_models.uuid4")
    def test_add(self, mock_uuid, mock_db):
        db, session = mock_db
        repo = LanguageModelRepository(db=db)
        mock_uuid.return_value = "generated-uuid"

        repo.add(
            integration_id="int-1",
            language_model_tag="gpt-4",
            schema="test_schema",
        )

        session.add.assert_called_once()
        session.commit.assert_called_once()
        session.refresh.assert_called_once()

    def test_update_language_model_found(self, mock_db):
        db, session = mock_db
        repo = LanguageModelRepository(db=db)
        lm = MagicMock(spec=LanguageModel)
        session.query.return_value.filter.return_value.first.return_value = lm

        repo.update_language_model(
            language_model_id="lm-1",
            language_model_tag="gpt-4-turbo",
            integration_id="int-2",
            schema="test_schema",
        )

        assert lm.language_model_tag == "gpt-4-turbo"
        assert lm.integration_id == "int-2"
        session.commit.assert_called_once()
        session.refresh.assert_called_once()

    def test_update_language_model_not_found(self, mock_db):
        db, session = mock_db
        repo = LanguageModelRepository(db=db)
        session.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(LanguageModelNotFoundError):
            repo.update_language_model(
                language_model_id="nonexistent",
                language_model_tag="gpt-4-turbo",
                integration_id="int-2",
                schema="test_schema",
            )

    def test_delete_by_id_found(self, mock_db):
        db, session = mock_db
        repo = LanguageModelRepository(db=db)
        lm = MagicMock(spec=LanguageModel)
        session.query.return_value.filter.return_value.first.return_value = lm

        repo.delete_by_id(language_model_id="lm-1", schema="test_schema")

        assert lm.is_active is False
        session.commit.assert_called_once()

    def test_delete_by_id_not_found(self, mock_db):
        db, session = mock_db
        repo = LanguageModelRepository(db=db)
        session.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(LanguageModelNotFoundError):
            repo.delete_by_id(language_model_id="nonexistent", schema="test_schema")


class TestLanguageModelSettingRepository:
    def test_get_all(self, mock_db):
        db, session = mock_db
        repo = LanguageModelSettingRepository(db=db)
        expected = [MagicMock(spec=LanguageModelSetting)]
        session.query.return_value.filter.return_value.all.return_value = expected

        result = repo.get_all(model_id="lm-1", schema="test_schema")

        assert result == expected

    @patch("app.domain.repositories.language_models.uuid4")
    def test_add(self, mock_uuid, mock_db):
        db, session = mock_db
        repo = LanguageModelSettingRepository(db=db)
        mock_uuid.return_value = "generated-uuid"

        repo.add(
            language_model_id="lm-1",
            setting_key="temperature",
            setting_value="0.7",
            schema="test_schema",
        )

        session.add.assert_called_once()
        session.commit.assert_called_once()
        session.refresh.assert_called_once()

    def test_update_by_key_found(self, mock_db):
        db, session = mock_db
        repo = LanguageModelSettingRepository(db=db)
        setting = MagicMock(spec=LanguageModelSetting)
        session.query.return_value.filter.return_value.first.return_value = setting

        repo.update_by_key(
            language_model_id="lm-1",
            setting_key="temperature",
            setting_value="0.9",
            schema="test_schema",
        )

        assert setting.setting_value == "0.9"
        session.commit.assert_called_once()

    def test_update_by_key_not_found(self, mock_db):
        db, session = mock_db
        repo = LanguageModelSettingRepository(db=db)
        session.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(LanguageModelNotFoundError):
            repo.update_by_key(
                language_model_id="lm-1",
                setting_key="temperature",
                setting_value="0.9",
                schema="test_schema",
            )


class TestLanguageModelNotFoundError:
    def test_entity_name(self):
        assert LanguageModelNotFoundError.entity_name == "LanguageModel"

    def test_message(self):
        error = LanguageModelNotFoundError("test-id")
        assert error.status_code == 404
        assert "LanguageModel" in error.detail


class TestLanguageModelSettingNotFoundError:
    def test_entity_name(self):
        assert LanguageModelSettingNotFoundError.entity_name == "LanguageModelSetting"
