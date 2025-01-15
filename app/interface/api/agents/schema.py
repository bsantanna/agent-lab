from typing import List, Optional

from pydantic import BaseModel, validator

from app.domain.exceptions.base import InvalidFieldError


class AgentCreateRequest(BaseModel):
    agent_name: str
    agent_type: str
    language_model_id: str

    @validator("agent_type")
    def validate_agent_type(cls, v):
        valid_types = ["three_phase_react"]
        if v not in valid_types:
            raise InvalidFieldError("agent_type", "not supported")
        return v


class AgentSettingResponse(BaseModel):
    setting_key: str
    setting_value: str

    class Config:
        from_attributes = True


class AgentResponse(BaseModel):
    id: str
    is_active: bool
    agent_name: str
    agent_type: str
    agent_summary: str
    language_model_id: str

    class Config:
        from_attributes = True


class AgentExpandedResponse(BaseModel):
    id: str
    is_active: bool
    agent_name: str
    agent_type: str
    agent_summary: str
    language_model_id: str
    ag_settings: Optional[List[AgentSettingResponse]]

    class Config:
        from_attributes = True
