from contextlib import AbstractContextManager
from typing import Callable, Iterator

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
            return session.query(LanguageModel).all()

    def get_by_id(self, language_model_id: int) -> LanguageModel:
        with self.session_factory() as session:
            language_model = (
                session.query(LanguageModel)
                .filter(LanguageModel.id == language_model_id)
                .first()
            )
            if not language_model:
                raise LanguageModelNotFoundError(language_model_id)
            return language_model

    def add(self, email: str, password: str, is_active: bool = True) -> LanguageModel:
        with self.session_factory() as session:
            language_model = LanguageModel(
                email=email, hashed_password=password, is_active=is_active
            )
            session.add(language_model)
            session.commit()
            session.refresh(language_model)
            return language_model

    def delete_by_id(self, language_model_id: int) -> None:
        with self.session_factory() as session:
            entity: LanguageModel = (
                session.query(LanguageModel)
                .filter(LanguageModel.id == language_model_id)
                .first()
            )
            if not entity:
                raise LanguageModelNotFoundError(language_model_id)
            session.delete(entity)
            session.commit()


class LanguageModelNotFoundError(NotFoundError):
    entity_name: str = "LanguageModel"


class LanguageModelSettingRepository:
    def __init__(
        self, session_factory: Callable[..., AbstractContextManager[Session]]
    ) -> None:
        self.session_factory = session_factory

    def get_all(self) -> Iterator[LanguageModelSetting]:
        with self.session_factory() as session:
            return session.query(LanguageModelSetting).all()

    def get_by_id(self, language_model_settings_id: int) -> LanguageModelSetting:
        with self.session_factory() as session:
            language_model_settings = (
                session.query(LanguageModelSetting)
                .filter(LanguageModelSetting.id == language_model_settings_id)
                .first()
            )
            if not language_model_settings:
                raise LanguageModelSettingNotFoundError(language_model_settings_id)
            return language_model_settings

    def add(
        self, email: str, password: str, is_active: bool = True
    ) -> LanguageModelSetting:
        with self.session_factory() as session:
            language_model_settings = LanguageModelSetting(
                email=email, hashed_password=password, is_active=is_active
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
