from urllib.parse import urlparse

from pydantic import BaseModel, validator

from app.domain.exceptions.base import InvalidFieldError


class IntegrationCreateRequest(BaseModel):
    integration_type: str
    api_endpoint: str
    api_key: str

    @validator("api_endpoint")
    def validate_api_endpoint(cls, v):
        parsed = urlparse(v)
        if not all([parsed.scheme, parsed.netloc]):
            raise InvalidFieldError("api_endpoint", "invalid url format")
        return v

    @validator("integration_type")
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
