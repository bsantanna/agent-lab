from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Body, Depends, Response, status
from fastapi.security import HTTPBearer
from fastapi_keycloak_middleware import get_user
from typing_extensions import List

from app.core.container import Container
from app.domain.models import LanguageModel as DomainLanguageModel
from app.infrastructure.auth.schema import User
from app.interface.api.language_models.schema import (
    LanguageModelCreateRequest,
    LanguageModelExpanded,
    LanguageModel,
    LanguageModelSetting,
    LanguageModelSettingUpdateRequest,
    LanguageModelUpdateRequest,
)
from app.services.language_model_settings import LanguageModelSettingService
from app.services.language_models import LanguageModelService

router = APIRouter()
bearer_scheme = HTTPBearer()


@router.get(
    "/list",
    dependencies=[Depends(bearer_scheme)],
    response_model=List[LanguageModel],
    summary="List all language models",
    description="""
    Returns all configured language models in the system.

    Each language model is linked to an integration and identified by a model tag
    (e.g. "gpt-4", "claude-sonnet-4-5", "grok-3").
    """,
    response_description="List of all language models",
    responses={
        200: {
            "description": "Successfully retrieved language models",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": "lm_123",
                            "created_at": "2024-01-15T10:00:00Z",
                            "is_active": True,
                            "language_model_tag": "gpt-4",
                            "integration_id": "int_openai_456",
                        },
                        {
                            "id": "lm_789",
                            "created_at": "2024-01-15T11:00:00Z",
                            "is_active": True,
                            "language_model_tag": "claude-sonnet-4-5",
                            "integration_id": "int_anthropic_012",
                        },
                    ]
                }
            },
        }
    },
)
@inject
async def get_list(
    language_model_service: LanguageModelService = Depends(
        Provide[Container.language_model_service]
    ),
    user: User = Depends(get_user),
):
    schema = user.id.replace("-", "_") if user is not None else "public"
    language_models = language_model_service.get_language_models(schema)
    return [LanguageModel.model_validate(lm) for lm in language_models]


@router.post(
    "/create",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(bearer_scheme)],
    response_model=LanguageModel,
    summary="Create a new language model",
    description="""
    Creates a new language model configuration linked to an existing integration.

    The model tag identifies which specific model to use within the integration provider
    (e.g. "gpt-4" for OpenAI, "claude-sonnet-4-5" for Anthropic).

    Prerequisites:
    - The integration must already exist and have valid API credentials.

    Parameters (JSON body):
    - `integration_id`: ID of an existing integration.
    - `language_model_tag`: The model identifier supported by the integration provider.
    """,
    response_description="The newly created language model",
    responses={
        201: {
            "description": "Language model created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "lm_new_123",
                        "created_at": "2024-01-15T12:00:00Z",
                        "is_active": True,
                        "language_model_tag": "gpt-4",
                        "integration_id": "int_openai_456",
                    }
                }
            },
        },
        400: {
            "description": "Invalid model tag",
            "content": {
                "application/json": {
                    "example": {"detail": "Field language_model_tag is invalid, reason: contains invalid characters"}
                }
            },
        },
        404: {
            "description": "Integration not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Integration with ID 'int_openai_456' not found"}
                }
            },
        },
        422: {"description": "Validation error"},
    },
)
@inject
async def add(
    language_model_data: LanguageModelCreateRequest = Body(
        ...,
        description="Language model creation data",
        example={"integration_id": "int_openai_456", "language_model_tag": "gpt-4"},
    ),
    language_model_service: LanguageModelService = Depends(
        Provide[Container.language_model_service]
    ),
    user: User = Depends(get_user),
):
    schema = user.id.replace("-", "_") if user is not None else "public"
    language_model = language_model_service.create_language_model(
        integration_id=language_model_data.integration_id,
        language_model_tag=language_model_data.language_model_tag,
        schema=schema,
    )
    return LanguageModel.model_validate(language_model)


@router.get(
    "/{language_model_id}",
    dependencies=[Depends(bearer_scheme)],
    response_model=LanguageModelExpanded,
    summary="Get language model by ID",
    description="""
    Returns detailed information about a specific language model, including all its
    configuration settings (e.g. temperature, max_tokens).

    Parameters:
    - `language_model_id` (path): The unique identifier of the language model.
    """,
    response_description="Language model details with settings",
    responses={
        200: {
            "description": "Successfully retrieved language model details",
            "content": {
                "application/json": {
                    "example": {
                        "id": "lm_123",
                        "created_at": "2024-01-15T10:00:00Z",
                        "is_active": True,
                        "language_model_tag": "gpt-4",
                        "integration_id": "int_openai_456",
                        "lm_settings": [
                            {
                                "setting_key": "temperature",
                                "setting_value": "0.7",
                            },
                            {
                                "setting_key": "max_tokens",
                                "setting_value": "2048",
                            },
                        ],
                    }
                }
            },
        },
        404: {
            "description": "Language model not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Language model with ID 'lm_123' not found"}
                }
            },
        },
    },
)
@inject
async def get_by_id(
    language_model_id: str,
    language_model_service: LanguageModelService = Depends(
        Provide[Container.language_model_service]
    ),
    language_model_setting_service: LanguageModelSettingService = Depends(
        Provide[Container.language_model_setting_service]
    ),
    user: User = Depends(get_user),
):
    schema = user.id.replace("-", "_") if user is not None else "public"
    language_model = language_model_service.get_language_model_by_id(
        language_model_id, schema
    )
    return _format_expanded_response(
        language_model, language_model_setting_service, schema
    )


@router.delete(
    "/delete/{language_model_id}",
    dependencies=[Depends(bearer_scheme)],
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a language model",
    description="""
    Permanently removes a language model and all its settings.

    Agents currently using this model will stop functioning. Reassign agents
    to a different model before deleting.

    Parameters:
    - `language_model_id` (path): The unique identifier of the language model to delete.
    """,
    response_description="Language model successfully deleted",
    responses={
        204: {"description": "Language model successfully deleted"},
        404: {
            "description": "Language model not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Language model with ID 'lm_123' not found"}
                }
            },
        },
    },
)
@inject
async def remove(
    language_model_id: str,
    language_model_service: LanguageModelService = Depends(
        Provide[Container.language_model_service]
    ),
    user: User = Depends(get_user),
):
    schema = user.id.replace("-", "_") if user is not None else "public"
    language_model_service.delete_language_model_by_id(language_model_id, schema)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/update",
    dependencies=[Depends(bearer_scheme)],
    response_model=LanguageModel,
    summary="Update a language model",
    description="""
    Updates the model tag or integration of an existing language model.

    Use this to switch model versions (e.g. "gpt-4" to "gpt-4-turbo") or
    reassign the model to a different integration. Existing settings and
    agent configurations are preserved.

    Parameters (JSON body):
    - `language_model_id`: The unique identifier of the language model to update.
    - `language_model_tag`: The new model tag.
    - `integration_id`: The integration to link to.
    """,
    response_description="Updated language model",
    responses={
        200: {
            "description": "Language model updated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "lm_123",
                        "created_at": "2024-01-15T10:00:00Z",
                        "is_active": True,
                        "language_model_tag": "gpt-4-turbo",
                        "integration_id": "int_openai_456",
                    }
                }
            },
        },
        400: {
            "description": "Invalid model tag",
            "content": {
                "application/json": {
                    "example": {"detail": "Field language_model_tag is invalid, reason: contains invalid characters"}
                }
            },
        },
        404: {
            "description": "Language model or integration not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Language model with ID 'lm_123' not found"}
                }
            },
        },
        422: {"description": "Validation error"},
    },
)
@inject
async def update(
    language_model_data: LanguageModelUpdateRequest = Body(
        ...,
        description="Language model update data",
        example={"language_model_id": "lm_123", "language_model_tag": "gpt-4-turbo", "integration_id": "int_openai_456"},
    ),
    language_model_service: LanguageModelService = Depends(
        Provide[Container.language_model_service]
    ),
    user: User = Depends(get_user),
):
    schema = user.id.replace("-", "_") if user is not None else "public"
    language_model = language_model_service.update_language_model(
        language_model_id=language_model_data.language_model_id,
        language_model_tag=language_model_data.language_model_tag,
        integration_id=language_model_data.integration_id,
        schema=schema,
    )
    return LanguageModel.model_validate(language_model)


@router.post(
    "/update_setting",
    dependencies=[Depends(bearer_scheme)],
    response_model=LanguageModelExpanded,
    summary="Update a language model setting",
    description="""
    Updates a single configuration setting for a language model by key.
    Returns the full language model with all current settings after the update.

    Parameters (JSON body):
    - `language_model_id`: The unique identifier of the language model.
    - `setting_key`: The setting key to update (e.g. "temperature", "max_tokens").
    - `setting_value`: The new value for the setting.
    """,
    response_description="Updated language model with all settings",
    responses={
        200: {
            "description": "Setting updated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "lm_123",
                        "created_at": "2024-01-15T10:00:00Z",
                        "is_active": True,
                        "language_model_tag": "gpt-4",
                        "integration_id": "int_openai_456",
                        "lm_settings": [
                            {
                                "setting_key": "temperature",
                                "setting_value": "0.9",
                            },
                            {
                                "setting_key": "max_tokens",
                                "setting_value": "2048",
                            },
                        ],
                    }
                }
            },
        },
        400: {
            "description": "Invalid setting key or value",
            "content": {
                "application/json": {
                    "example": {"detail": "Field setting_value is invalid, reason: contains invalid characters"}
                }
            },
        },
        404: {
            "description": "Language model not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Language model with ID 'lm_123' not found"}
                }
            },
        },
        422: {"description": "Validation error"},
    },
)
@inject
async def update_setting(
    language_model_data: LanguageModelSettingUpdateRequest = Body(
        ...,
        description="Language model setting update data",
        example={
            "language_model_id": "lm_123",
            "setting_key": "temperature",
            "setting_value": "0.9",
        },
    ),
    language_model_service: LanguageModelService = Depends(
        Provide[Container.language_model_service]
    ),
    language_model_setting_service: LanguageModelSettingService = Depends(
        Provide[Container.language_model_setting_service]
    ),
    user: User = Depends(get_user),
):
    schema = user.id.replace("-", "_") if user is not None else "public"
    language_model_setting_service.update_by_key(
        language_model_id=language_model_data.language_model_id,
        setting_key=language_model_data.setting_key,
        setting_value=language_model_data.setting_value,
        schema=schema,
    )

    language_model = language_model_service.get_language_model_by_id(
        language_model_id=language_model_data.language_model_id,
        schema=schema,
    )

    return _format_expanded_response(
        language_model, language_model_setting_service, schema
    )


def _format_expanded_response(
    language_model: DomainLanguageModel,
    language_model_setting_service: LanguageModelSettingService,
    schema: str,
) -> LanguageModelExpanded:
    settings = language_model_setting_service.get_language_model_settings(
        language_model.id, schema
    )
    response = LanguageModelExpanded.model_validate(language_model)
    response.lm_settings = [
        LanguageModelSetting.model_validate(setting) for setting in settings
    ]
    return response
