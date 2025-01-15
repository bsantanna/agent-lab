from typing import List, Optional

from pydantic import BaseModel


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
