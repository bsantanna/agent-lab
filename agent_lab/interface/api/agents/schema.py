import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator
from typing_extensions import List, Optional

from agent_lab.domain.exceptions.base import InvalidFieldError
from agent_lab.services.agent_types.registration import is_registered

invalid_characters_description = "contains invalid characters"

setting_value_max_length = 16000
setting_value_too_long_description = (
    f"exceeds maximum length of {setting_value_max_length} characters"
)


class AgentCreateRequest(BaseModel):
    agent_name: str
    agent_type: str
    language_model_id: Optional[str] = None

    @field_validator("agent_name")
    def validate_agent_name(cls, v: str):
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise InvalidFieldError("agent_name", invalid_characters_description)
        return v

    @field_validator("agent_type")
    def validate_agent_type(cls, v: str):
        if not is_registered(v):
            raise InvalidFieldError("agent_type", "not supported")
        return v


class AgentSetting(BaseModel):
    setting_key: str

    @field_validator("setting_key")
    def validate_setting_key(cls, v: str):
        if not re.match(r"^[a-zA-Z_-]+$", v):
            raise InvalidFieldError("setting_key", invalid_characters_description)
        return v

    setting_value: str

    @field_validator("setting_value")
    def validate_setting_value(cls, v: str):
        if len(v) > setting_value_max_length:
            raise InvalidFieldError("setting_value", setting_value_too_long_description)
        return v

    model_config = ConfigDict(from_attributes=True)


class Agent(BaseModel):
    id: str
    is_active: bool
    created_at: datetime
    agent_name: str
    agent_type: str
    agent_summary: str
    language_model_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class AgentExpanded(Agent):
    ag_settings: Optional[List[AgentSetting]] = None


class AgentUpdateRequest(BaseModel):
    agent_id: str
    agent_name: str
    language_model_id: Optional[str] = None
    agent_summary: Optional[str] = None

    @field_validator("agent_name")
    def validate_agent_name(cls, v: str):
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise InvalidFieldError("agent_name", invalid_characters_description)
        return v


class AgentSettingUpdateRequest(BaseModel):
    agent_id: str
    setting_key: str
    setting_value: str

    @field_validator("setting_value")
    def validate_setting_value(cls, v: str):
        if len(v) > setting_value_max_length:
            raise InvalidFieldError("setting_value", setting_value_too_long_description)
        return v

    @field_validator("setting_key")
    def validate_setting_key(cls, v: str):
        if not re.match(r"^[a-zA-Z_-]+$", v):
            raise InvalidFieldError("setting_key", invalid_characters_description)
        return v
