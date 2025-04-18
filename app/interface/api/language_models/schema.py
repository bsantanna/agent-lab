from datetime import datetime

from pydantic import BaseModel
from typing_extensions import List, Optional


class LanguageModelCreateRequest(BaseModel):
    integration_id: str
    language_model_tag: str


class LanguageModelSettingResponse(BaseModel):
    setting_key: str
    setting_value: str

    class Config:
        from_attributes = True


class LanguageModelResponse(BaseModel):
    id: str
    created_at: datetime
    is_active: bool
    language_model_tag: str
    integration_id: str

    class Config:
        from_attributes = True


class LanguageModelExpandedResponse(LanguageModelResponse):
    lm_settings: Optional[List[LanguageModelSettingResponse]] = None


class LanguageModelUpdateRequest(BaseModel):
    language_model_id: str
    language_model_tag: str


class LanguageModelSettingUpdateRequest(BaseModel):
    language_model_id: str
    setting_key: str
    setting_value: str
