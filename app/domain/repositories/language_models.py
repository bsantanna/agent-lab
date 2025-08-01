from datetime import datetime
from uuid import uuid4

from typing_extensions import Iterator

from app.domain.exceptions.base import NotFoundError
from app.domain.models import LanguageModel, LanguageModelSetting
from app.infrastructure.database.sql import Database


class LanguageModelRepository:
    def __init__(
        self,
        db: Database,
    ) -> None:
        self.db = db

    def get_all(self, schema: str) -> Iterator[LanguageModel]:
        with self.db.session(schema_name=schema) as session:
            return session.query(LanguageModel).filter(LanguageModel.is_active).all()

    def get_by_id(self, language_model_id: str, schema: str) -> LanguageModel:
        with self.db.session(schema_name=schema) as session:
            language_model = (
                session.query(LanguageModel)
                .filter(LanguageModel.id == language_model_id, LanguageModel.is_active)
                .first()
            )
            if not language_model:
                raise LanguageModelNotFoundError(language_model_id)
            return language_model

    def add(
        self, integration_id: str, language_model_tag: str, schema: str
    ) -> LanguageModel:
        gen_id = uuid4()
        with self.db.session(schema_name=schema) as session:
            language_model = LanguageModel(
                id=str(gen_id),
                is_active=True,
                created_at=datetime.now(),
                integration_id=integration_id,
                language_model_tag=language_model_tag,
            )
            session.add(language_model)
            session.commit()
            session.refresh(language_model)
            return language_model

    def update_language_model(
        self,
        language_model_id: str,
        language_model_tag: str,
        integration_id: str,
        schema: str,
    ) -> LanguageModel:
        with self.db.session(schema_name=schema) as session:
            entity: LanguageModel = (
                session.query(LanguageModel)
                .filter(LanguageModel.id == language_model_id, LanguageModel.is_active)
                .first()
            )
            if not entity:
                raise LanguageModelNotFoundError(language_model_id)

            entity.language_model_tag = language_model_tag
            entity.integration_id = integration_id
            session.commit()
            session.refresh(entity)
            return entity

    def delete_by_id(self, language_model_id: str, schema: str) -> None:
        with self.db.session(schema_name=schema) as session:
            entity: LanguageModel = (
                session.query(LanguageModel)
                .filter(LanguageModel.id == language_model_id, LanguageModel.is_active)
                .first()
            )
            if not entity:
                raise LanguageModelNotFoundError(language_model_id)

            entity.is_active = False
            session.commit()


class LanguageModelNotFoundError(NotFoundError):
    entity_name: str = "LanguageModel"


class LanguageModelSettingRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def get_all(self, model_id: str, schema: str) -> Iterator[LanguageModelSetting]:
        with self.db.session(schema_name=schema) as session:
            return (
                session.query(LanguageModelSetting)
                .filter(LanguageModelSetting.language_model_id == model_id)
                .all()
            )

    def add(
        self, language_model_id: str, setting_key: str, setting_value: str, schema: str
    ) -> LanguageModelSetting:
        gen_uid = uuid4()
        with self.db.session(schema_name=schema) as session:
            language_model_settings = LanguageModelSetting(
                id=str(gen_uid),
                language_model_id=language_model_id,
                setting_key=setting_key,
                setting_value=setting_value,
            )
            session.add(language_model_settings)
            session.commit()
            session.refresh(language_model_settings)
            return language_model_settings

    def update_by_key(
        self, language_model_id: str, setting_key: str, setting_value: str, schema: str
    ) -> LanguageModelSetting:
        with self.db.session(schema_name=schema) as session:
            entity: LanguageModelSetting = (
                session.query(LanguageModelSetting)
                .filter(
                    LanguageModelSetting.language_model_id == language_model_id,
                    LanguageModelSetting.setting_key == setting_key,
                )
                .first()
            )
            if not entity:
                raise LanguageModelNotFoundError(language_model_id)

            entity.setting_value = setting_value
            session.commit()
            session.refresh(entity)
            return entity


class LanguageModelSettingNotFoundError(NotFoundError):
    entity_name: str = "LanguageModelSetting"
