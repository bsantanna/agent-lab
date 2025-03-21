from datetime import datetime
from typing_extensions import List, Optional

from pydantic import BaseModel, field_validator

from app.domain.exceptions.base import InvalidFieldError


class AgentCreateRequest(BaseModel):
    agent_name: str
    agent_type: str
    language_model_id: str

    @field_validator("agent_type")
    def validate_agent_type(cls, v):
        valid_types = [
            "adaptive_rag",
            "react_rag",
            "test_echo",
            "three_phase_react",
            "vision_document",
        ]
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
    created_at: datetime
    agent_name: str
    agent_type: str
    agent_summary: str
    language_model_id: str

    class Config:
        from_attributes = True


class AgentExpandedResponse(AgentResponse):
    ag_settings: Optional[List[AgentSettingResponse]] = None


class AgentUpdateRequest(BaseModel):
    agent_id: str
    agent_name: str


class AgentSettingUpdateRequest(BaseModel):
    agent_id: str
    setting_key: str
    setting_value: str
