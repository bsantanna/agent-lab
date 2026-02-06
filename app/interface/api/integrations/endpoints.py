from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Body, Depends, Response, status
from fastapi.security import HTTPBearer
from fastapi_keycloak_middleware import get_user
from typing_extensions import List

from app.core.container import Container
from app.infrastructure.auth.schema import User
from app.interface.api.integrations.schema import (
    IntegrationCreateRequest,
    Integration,
    integration_valid_types,
)
from app.services.integrations import IntegrationService

router = APIRouter()
bearer_scheme = HTTPBearer()


@router.get(
    "/list",
    dependencies=[Depends(bearer_scheme)],
    response_model=List[Integration],
    summary="List all integrations",
    description="""
    Returns all configured third-party AI service integrations.

    Integrations represent connections to external AI providers (OpenAI, Anthropic, xAI, Ollama).
    Each integration stores the API endpoint and credentials needed to make requests.
    """,
    response_description="List of all integrations",
    responses={
        200: {
            "description": "Successfully retrieved integrations",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": "int_openai_123",
                            "created_at": "2024-01-15T10:00:00Z",
                            "is_active": True,
                            "integration_type": "openai_api_v1",
                        },
                        {
                            "id": "int_anthropic_456",
                            "created_at": "2024-01-15T11:00:00Z",
                            "is_active": True,
                            "integration_type": "anthropic_api_v1",
                        },
                    ]
                }
            },
        }
    },
)
@inject
async def get_list(
    integration_service: IntegrationService = Depends(
        Provide[Container.integration_service]
    ),
    user: User = Depends(get_user),
):
    schema = user.id.replace("-", "_") if user is not None else "public"
    integrations = integration_service.get_integrations(schema)
    return [Integration.model_validate(integration) for integration in integrations]


@router.get(
    "/{integration_id}",
    dependencies=[Depends(bearer_scheme)],
    response_model=Integration,
    summary="Get integration by ID",
    description="""
    Returns information about a specific integration.

    Parameters:
    - `integration_id` (path): The unique identifier of the integration.
    """,
    response_description="Integration details",
    responses={
        200: {
            "description": "Successfully retrieved integration",
            "content": {
                "application/json": {
                    "example": {
                        "id": "int_openai_123",
                        "created_at": "2024-01-15T10:00:00Z",
                        "is_active": True,
                        "integration_type": "openai_api_v1",
                    }
                }
            },
        },
        404: {
            "description": "Integration not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Integration with ID 'int_openai_123' not found"}
                }
            },
        },
    },
)
@inject
async def get_by_id(
    integration_id: str,
    integration_service: IntegrationService = Depends(
        Provide[Container.integration_service]
    ),
    user: User = Depends(get_user),
):
    schema = user.id.replace("-", "_") if user is not None else "public"
    integration = integration_service.get_integration_by_id(integration_id, schema)
    return Integration.model_validate(integration)


@router.post(
    "/create",
    dependencies=[Depends(bearer_scheme)],
    status_code=status.HTTP_201_CREATED,
    response_model=Integration,
    summary="Create a new integration",
    description=f"""
    Creates a new connection to an external AI service provider.
    API keys are encrypted at storage.

    Available integration types: {integration_valid_types}

    Parameters (JSON body):
    - `integration_type`: One of the supported types listed above.
    - `api_endpoint`: The base URL of the API (e.g. "https://api.openai.com/v1").
    - `api_key`: The API key for authentication with the provider.
    """,
    response_description="The newly created integration",
    responses={
        201: {
            "description": "Integration created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "int_new_789",
                        "created_at": "2024-01-15T16:00:00Z",
                        "is_active": True,
                        "integration_type": "openai_api_v1",
                    }
                }
            },
        },
        400: {
            "description": "Invalid integration type",
            "content": {
                "application/json": {
                    "example": {
                        "detail": f"Field integration_type is invalid, reason: Invalid integration type, please use one of: {integration_valid_types}"
                    }
                }
            },
        },
        422: {
            "description": "Validation error",
            "content": {
                "application/json": {
                    "example": {"detail": "Field api_endpoint is invalid, reason: invalid url format"}
                }
            },
        },
    },
)
@inject
async def add(
    integration_data: IntegrationCreateRequest = Body(
        ...,
        description="Integration configuration data",
        example={
            "integration_type": "openai_api_v1",
            "api_endpoint": "https://api.openai.com/v1",
            "api_key": "an_api_key",
        },
    ),
    integration_service: IntegrationService = Depends(
        Provide[Container.integration_service]
    ),
    user: User = Depends(get_user),
):
    schema = user.id.replace("-", "_") if user is not None else "public"
    integration = integration_service.create_integration(
        integration_type=integration_data.integration_type,
        api_endpoint=integration_data.api_endpoint,
        api_key=integration_data.api_key,
        schema=schema,
    )
    return Integration.model_validate(integration)


@router.delete(
    "/delete/{integration_id}",
    dependencies=[Depends(bearer_scheme)],
    summary="Delete an integration",
    description="""
    Permanently removes an integration and its configuration.

    Deleting an integration will make all language models linked to it unavailable,
    and agents using those models will stop functioning.

    Parameters:
    - `integration_id` (path): The unique identifier of the integration to delete.
    """,
    response_description="Integration successfully deleted",
    responses={
        204: {"description": "Integration successfully deleted"},
        404: {
            "description": "Integration not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Integration with ID 'int_openai_123' not found"}
                }
            },
        },
    },
)
@inject
async def remove(
    integration_id: str,
    integration_service: IntegrationService = Depends(
        Provide[Container.integration_service]
    ),
    user: User = Depends(get_user),
):
    schema = user.id.replace("-", "_") if user is not None else "public"
    integration_service.delete_integration_by_id(integration_id, schema)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
