from datetime import datetime

from pydantic import BaseModel, field_validator
from typing_extensions import Optional

from app.domain.exceptions.base import InvalidFieldError
from app.interface.api.attachments.schema import Attachment


class MessageBase(BaseModel):
    message_role: str
    message_content: str
    agent_id: str

    @field_validator("message_role")
    def validate_message_role(cls, v):
        valid_types = ["assistant", "human", "tool"]
        if v not in valid_types:
            raise InvalidFieldError("message_role", "not supported")
        return v


class MessageRequest(MessageBase):
    attachment_id: Optional[str] = None


class MessageListRequest(BaseModel):
    agent_id: str


class Message(MessageBase):
    id: Optional[str] = None
    is_active: Optional[bool] = None
    created_at: Optional[datetime] = None
    response_data: Optional[dict] = None
    replies_to: Optional[str] = None

    class Config:
        from_attributes = True


class MessageExpanded(Message):
    replies_to: Optional[Message]
    attachment: Optional[Attachment]
