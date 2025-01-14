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
