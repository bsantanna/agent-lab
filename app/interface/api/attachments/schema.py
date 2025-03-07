from datetime import datetime

from pydantic import BaseModel
from typing_extensions import Optional


class AttachmentResponse(BaseModel):
    id: str
    is_active: bool
    created_at: datetime
    file_name: str
    parsed_content: str
    embeddings_collection: Optional[str]

    class Config:
        from_attributes = True
