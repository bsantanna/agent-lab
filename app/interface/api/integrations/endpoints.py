from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Body, Depends, Response, status
from fastapi.security import HTTPBearer
from fastapi_keycloak_middleware import get_user
from typing_extensions import List

from app.core.container import Container
from app.infrastructure.auth.schema import User
from app.infrastructure.database.sql import Database
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
    Retrieve a complete list of all configured third-party integrations.

    This endpoint returns all integrations configured in the system.
    Integrations are the foundation for connecting to external AI services.

    **Example Integration Types:**
    - OpenAI (GPT models)
    - Anthropic (Claude models)
    - Google (Gemini models)
    - xAI (Grok models)
    - Ollama (Local models)
    - Custom API endpoints

    **Use cases:**
    - Display available integrations in admin interface
    - System health monitoring and diagnostics
    - Integration selection for new language models
    - API connectivity validation
    - Audit and compliance reporting
    """,
    response_description="List of all configured integrations with their details",
    responses={
        200: {
            "description": "Successfully retrieved integrations",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": "int_openai_123",
                            "integration_type": "openai_api_v1",
                            "is_active": True,
                            "created_at": "2024-01-15T10:00:00Z",
                        },
                        {
                            "id": "int_anthropic_456",
                            "integration_type": "anthropic_api_v1",
                            "is_active": True,
                            "created_at": "2024-01-15T11:00:00Z",
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
    db: Database = Depends(Provide[Container.db]),
    user: User = Depends(get_user),
):
    """
    Get all configured integrations.

    Returns:
        List[Integration]: All integrations in the system
    """
    schema = db.sanitize_schema_name(user.id) if user is not None else "public"
    integrations = integration_service.get_integrations(schema)
    return [Integration.model_validate(integration) for integration in integrations]


@router.get(
    "/{integration_id}",
    dependencies=[Depends(bearer_scheme)],
    response_model=Integration,
    summary="Get integration details",
    description="""
    Retrieve information about a specific integration.
    """,
    response_description="Detailed integration information",
    responses={
        200: {
            "description": "Integration details retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "int_openai_123",
                        "integration_type": "openai_api_v1",
                        "is_active": True,
                        "created_at": "2024-01-15T10:00:00Z",
                    }
                }
            },
        },
        404: {"description": "Integration not found"},
    },
)
@inject
async def get_by_id(
    integration_id: str,
    integration_service: IntegrationService = Depends(
        Provide[Container.integration_service]
    ),
    db: Database = Depends(Provide[Container.db]),
    user: User = Depends(get_user),
):
    """
    Get information about a specific integration.

    Returns:
        Integration: Complete integration details

    """
    schema = db.sanitize_schema_name(user.id) if user is not None else "public"
    integration = integration_service.get_integration_by_id(integration_id, schema)
    return Integration.model_validate(integration)


@router.post(
    "/create",
    dependencies=[Depends(bearer_scheme)],
    status_code=status.HTTP_201_CREATED,
    response_model=Integration,
    summary="Create a new integration",
    description="""
    Create a new third-party service integration for AI language models.

    This endpoint establishes a connection to external AI services by configuring
    API endpoints, authentication credentials, and integration parameters.

    **Integration Types:**
    - `openai_api_v1`: OpenAI GPT models (GPT-4, GPT-3.5-turbo)
    - `anthropic_api_v1`: Anthropic Claude models (Claude-3, Claude-2)
    - `xai_api_v1`: xAI models (Grok-3, Grok-2-Vision)
    - `ollama_api_v1`: Ollama local models (Llama-3, Mistral)

    **Security Considerations:**
    - API keys are encrypted at storage

    **Post-Creation Steps:**
    1. Test integration connectivity
    2. Configure language models
    3. Set up usage monitoring
    4. Create agents using the integration
    """,
    response_description="Newly created integration configuration",
    responses={
        201: {
            "description": "Integration created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "int_new_789",
                        "integration_type": "openai_api_v1",
                        "is_active": True,
                        "created_at": "2024-01-15T16:00:00Z",
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
            "description": "Integration validation failed",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid integration data format"}
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
    db: Database = Depends(Provide[Container.db]),
    user: User = Depends(get_user),
):
    """
    Create a new integration with external AI service.

    Returns:
        Integration: Newly created integration
    """
    schema = db.sanitize_schema_name(user.id) if user is not None else "public"
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
    Permanently delete an integration and all its associated configurations.

    **Warning:** This action cannot be undone and will have cascading effects:

    **Immediate Effects:**
    - All associated language models become unavailable
    - Agents using this integration will fail to function

    **Data Impact:**
    - Historical messages and conversations are preserved
    - Language model settings are deleted
    - Integration usage logs are archived
    - Error logs and diagnostics are retained for audit

    **Pre-Deletion Checklist:**
    1. Identify all language models using this integration
    2. Migrate language models to alternative integrations
    3. Update or disable affected agents
    4. Test system functionality without this integration
    5. Export integration configuration for backup
    6. Notify team members of the planned deletion

    **Recovery:**
    - Deleted integrations can be recreated with same configuration
    - Historical usage data cannot be restored
    - Language models must be reconfigured manually
    """,
    response_description="Integration successfully deleted (no content returned)",
    responses={
        204: {"description": "Integration successfully deleted"},
        404: {"description": "Integration not found"},
    },
)
@inject
async def remove(
    integration_id: str,
    integration_service: IntegrationService = Depends(
        Provide[Container.integration_service]
    ),
    db: Database = Depends(Provide[Container.db]),
    user: User = Depends(get_user),
):
    """
    Delete an integration by ID.

    Returns:
        Response: 204 No Content on success

    """
    schema = db.sanitize_schema_name(user.id) if user is not None else "public"
    integration_service.delete_integration_by_id(integration_id, schema)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
