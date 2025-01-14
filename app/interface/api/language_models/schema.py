from pydantic import BaseModel


class LanguageModelCreateRequest(BaseModel):
    integration_id: str
    language_model_tag: str
