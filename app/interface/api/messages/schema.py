from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator

from app.domain.exceptions.base import InvalidFieldError


class AttachmentResponse(BaseModel):
    id: str
    is_active: bool
    created_at: datetime
    file_name: str
    parsed_content: str
    embeddings_id: Optional[str]


class MessageBase(BaseModel):
    message_role: str
    message_content: str
    agent_id: str

    @field_validator("message_role")
    def validate_message_role(cls, v):
        valid_types = ["assistant", "human", "system", "tool"]
        if v not in valid_types:
            raise InvalidFieldError("message_role", "not supported")
        return v


class MessageRequest(MessageBase):
    attachment_id: str


class MessageListRequest(BaseModel):
    agent_id: str


class MessageResponse(MessageBase):
    id: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class MessageExpandedResponse(MessageResponse):
    attachment: AttachmentResponse
