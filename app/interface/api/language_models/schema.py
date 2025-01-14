from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel


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


class LanguageModelExpandedResponse(BaseModel):
    id: str
    created_at: datetime
    is_active: bool
    language_model_tag: str
    integration_id: str
    lm_settings: Optional[List[LanguageModelSettingResponse]] = None

    class Config:
        from_attributes = True
