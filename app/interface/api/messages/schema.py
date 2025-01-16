from pydantic import BaseModel, field_validator

from app.domain.exceptions.base import InvalidFieldError


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
