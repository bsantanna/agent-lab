from typing import Optional

from fastmcp.server.dependencies import get_access_token
from pydantic import BaseModel, Field

from app.infrastructure.auth.user import get_schema


class AgentItem(BaseModel):
    """An AI agent registered on the Agent-Lab platform."""

    id: str = Field(description="Unique agent identifier")
    agent_name: str = Field(description="Human-readable agent name")
    agent_type: str = Field(description="Agent type key (e.g. react_rag, vision_document)")
    agent_summary: str = Field(description="Brief description of the agent's purpose and capabilities")
    language_model_id: str = Field(description="ID of the language model powering this agent")
    is_active: bool = Field(description="Whether the agent is currently active")


class MessageItem(BaseModel):
    """A message in an agent conversation."""

    id: str = Field(description="Unique message identifier")
    message_role: str = Field(description="Role: 'human' or 'assistant'")
    message_content: str = Field(description="Text content of the message")
    agent_id: str = Field(description="ID of the agent this message belongs to")
    response_data: Optional[str] = Field(default=None, description="Structured response data, if any")
    replies_to: Optional[str] = Field(default=None, description="ID of the message this replies to")


class PostMessageResult(BaseModel):
    """Result of sending a message to an agent."""

    id: str = Field(description="ID of the assistant's response message")
    message_content: str = Field(description="The assistant's response text")
    agent_id: str = Field(description="ID of the agent that processed the message")
    response_data: Optional[str] = Field(default=None, description="Structured response data, if any")


def _get_mcp_schema() -> str:
    """Derive the tenant DB schema from the MCP access token."""
    access_token = get_access_token()
    if access_token is None:
        return "public"
    sub = access_token.claims.get("sub")
    user_id = f"id_{sub}" if sub else None
    return get_schema(user_id)
