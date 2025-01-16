from pydantic import BaseModel


class MessageRequest(BaseModel):
    message_role: str
    message_content: str
    agent_id: str
    attachment_id: str


class MessageResponse(BaseModel):
    message_role: str
    message_content: str
    agent_id: str
