from datetime import datetime

from pydantic import BaseModel, ConfigDict
from typing_extensions import Optional


class EmbeddingsRequest(BaseModel):
    attachment_id: str
    language_model_id: str
    collection_name: str


class Attachment(BaseModel):
    id: str
    is_active: bool
    created_at: datetime
    file_name: str
    parsed_content: str
    embeddings_collection: Optional[str]

    model_config = ConfigDict(from_attributes=True)
