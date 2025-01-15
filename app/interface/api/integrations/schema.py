from datetime import datetime
from urllib.parse import urlparse

from pydantic import BaseModel, field_validator

from app.domain.exceptions.base import InvalidFieldError


class IntegrationCreateRequest(BaseModel):
    integration_type: str
    api_endpoint: str
    api_key: str

    @field_validator("api_endpoint")
    def validate_api_endpoint(cls, v):
        parsed = urlparse(v)
        if not all([parsed.scheme, parsed.netloc]):
            raise InvalidFieldError("api_endpoint", "invalid url format")
        return v

    @field_validator("integration_type")
    def validate_integration_type(cls, v):
        valid_types = [
            "anthropic_api_v1",
            "grok_api_v1",
            "openai_api_v1",
            "ollama_api_v1",
        ]
        if v not in valid_types:
            raise InvalidFieldError("integration_type", "not supported")
        return v


class IntegrationResponse(BaseModel):
    id: str
    created_at: datetime
    is_active: bool
    integration_type: str

    class Config:
        from_attributes = True
