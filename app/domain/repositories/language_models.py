from contextlib import AbstractContextManager
from datetime import datetime
from typing import Callable, Iterator
from uuid import uuid4

from sqlalchemy.orm import Session

from app.domain.exceptions.base import NotFoundError
from app.domain.models import LanguageModel, LanguageModelSetting


class LanguageModelRepository:
    def __init__(
        self, session_factory: Callable[..., AbstractContextManager[Session]]
    ) -> None:
        self.session_factory = session_factory

    def get_all(self) -> Iterator[LanguageModel]:
        with self.session_factory() as session:
            return session.query(LanguageModel).filter(LanguageModel.is_active).all()

    def get_by_id(self, language_model_id: int) -> LanguageModel:
        with self.session_factory() as session:
            language_model = (
                session.query(LanguageModel)
                .filter(LanguageModel.id == language_model_id, LanguageModel.is_active)
                .first()
            )
            if not language_model:
                raise LanguageModelNotFoundError(language_model_id)
            return language_model

    def add(self, integration_id: str, language_model_tag: str) -> LanguageModel:
        gen_id = uuid4()
        with self.session_factory() as session:
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

    def delete_by_id(self, language_model_id: int) -> None:
        with self.session_factory() as session:
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
    def __init__(
        self, session_factory: Callable[..., AbstractContextManager[Session]]
    ) -> None:
        self.session_factory = session_factory

    def get_all(self, model_id: str) -> Iterator[LanguageModelSetting]:
        with self.session_factory() as session:
            return (
                session.query(LanguageModelSetting)
                .filter(LanguageModelSetting.language_model_id == model_id)
                .all()
            )

    def add(
        self, language_model_id: str, setting_key: str, setting_value: str
    ) -> LanguageModelSetting:
        gen_uid = uuid4()
        with self.session_factory() as session:
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

    def delete_by_id(self, language_model_settings_id: int) -> None:
        with self.session_factory() as session:
            entity: LanguageModelSetting = (
                session.query(LanguageModelSetting)
                .filter(LanguageModelSetting.id == language_model_settings_id)
                .first()
            )
            if not entity:
                raise LanguageModelSettingNotFoundError(language_model_settings_id)
            session.delete(entity)
            session.commit()


class LanguageModelSettingNotFoundError(NotFoundError):
    entity_name: str = "LanguageModelSetting"
