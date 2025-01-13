from pydantic import BaseModel


class IntegrationCreateRequest(BaseModel):
    integration_type: str
    api_endpoint: str
    api_key: str
