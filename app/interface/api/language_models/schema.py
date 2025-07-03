import re
from datetime import datetime

from pydantic import BaseModel, field_validator
from typing_extensions import List, Optional

from app.domain.exceptions.base import InvalidFieldError

invalid_characters_description = "contains invalid characters"


class LanguageModelCreateRequest(BaseModel):
    integration_id: str
    language_model_tag: str

    @field_validator("language_model_tag")
    def validate_language_model_tag(cls, v: str):
        if not re.match(r"^[a-zA-Z0-9\\.:_-]+$", v):
            raise InvalidFieldError(
                "language_model_tag", invalid_characters_description
            )
        return v


class LanguageModelSetting(BaseModel):
    setting_key: str
    setting_value: str

    @field_validator("setting_key")
    def validate_setting_key(cls, v: str):
        if not re.match(r"^[a-zA-Z_-]+$", v):
            raise InvalidFieldError("setting_key", invalid_characters_description)
        return v

    @field_validator("setting_value")
    def validate_setting_value(cls, v: str):
        if not re.match(r"^[a-zA-Z0-9\\._-]+$", v):
            raise InvalidFieldError("setting_value", invalid_characters_description)
        return v

    class Config:
        from_attributes = True


class LanguageModel(BaseModel):
    id: str
    created_at: datetime
    is_active: bool
    language_model_tag: str
    integration_id: str

    class Config:
        from_attributes = True


class LanguageModelExpanded(LanguageModel):
    lm_settings: Optional[List[LanguageModelSetting]] = None


class LanguageModelUpdateRequest(BaseModel):
    language_model_id: str
    language_model_tag: str
    integration_id: str

    @field_validator("language_model_tag")
    def validate_language_model_tag(cls, v: str):
        if not re.match(r"^[a-zA-Z0-9\\.:_-]+$", v):
            raise InvalidFieldError(
                "language_model_tag", invalid_characters_description
            )
        return v


class LanguageModelSettingUpdateRequest(BaseModel):
    language_model_id: str
    setting_key: str
    setting_value: str

    @field_validator("setting_key")
    def validate_setting_key(cls, v: str):
        if not re.match(r"^[a-zA-Z_-]+$", v):
            raise InvalidFieldError("setting_key", invalid_characters_description)
        return v

    @field_validator("setting_value")
    def validate_setting_value(cls, v: str):
        if not re.match(r"^[a-zA-Z0-9\\._-]+$", v):
            raise InvalidFieldError("setting_value", invalid_characters_description)
        return v
