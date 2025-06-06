from typing import Any

from pydantic import BaseModel, Field
from typing_extensions import Dict


class ReadResourceParams(BaseModel):
    uri: str = Field(
        ...,
        description="The URI of the resource to read, e.g., 'agent-lab://conversations/agent_id'",
    )


class ReadResourceRequest(BaseModel):
    params: ReadResourceParams

    class Config:
        schema_extra = {
            "example": {"params": {"uri": "agent-lab://conversations/test_agent_123"}}
        }


class ToolCallParams(BaseModel):
    name: str = Field(..., description="The name of the tool to call")
    arguments: Dict[str, Any] = Field(
        ..., description="The arguments required by the tool"
    )


class ToolCallRequest(BaseModel):
    params: ToolCallParams
