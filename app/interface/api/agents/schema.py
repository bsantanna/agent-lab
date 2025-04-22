import re
from datetime import datetime

from pydantic import BaseModel, field_validator
from typing_extensions import List, Optional

from app.domain.exceptions.base import InvalidFieldError


class AgentCreateRequest(BaseModel):
    agent_name: str
    agent_type: str
    language_model_id: str

    @field_validator("agent_name")
    def validate_agent_name(cls, v):
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise InvalidFieldError("agent_name", "contains invalid characters")
        return v

    @field_validator("agent_type")
    def validate_agent_type(cls, v):
        valid_types = [
            "adaptive_rag",
            "coordinator_planner_supervisor",
            "react_rag",
            "test_echo",
            "vision_document",
            "voice_memos",
            "azure_entra_id_voice_memos",
        ]
        if v not in valid_types:
            raise InvalidFieldError("agent_type", "not supported")
        return v


class AgentSetting(BaseModel):
    setting_key: str
    setting_value: str

    class Config:
        from_attributes = True


class Agent(BaseModel):
    id: str
    is_active: bool
    created_at: datetime
    agent_name: str
    agent_type: str
    agent_summary: str
    language_model_id: str

    class Config:
        from_attributes = True


class AgentExpanded(Agent):
    ag_settings: Optional[List[AgentSetting]] = None


class AgentUpdateRequest(BaseModel):
    agent_id: str
    agent_name: str


class AgentSettingUpdateRequest(BaseModel):
    agent_id: str
    setting_key: str
    setting_value: str
