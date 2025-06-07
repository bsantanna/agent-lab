from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Body, Depends, Response, status, HTTPException
from typing_extensions import List

from app.core.container import Container
from app.domain.exceptions.base import NotFoundError
from app.domain.models import LanguageModel as DomainLanguageModel
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


@router.get(
    "/list",
    response_model=List[LanguageModel],
    summary="List all language models",
    description="""
    Retrieve a complete list of all configured language models in the system.

    This endpoint returns all language models regardless of their integration type
    or current status. Each model includes basic information like ID, tag, and
    integration details.

    **Use cases:**
    - Display available models in UI dropdowns
    - System administration and monitoring
    - Model selection for agents
    - Integration health checks
    """,
    response_description="List of all configured language models",
    responses={
        200: {
            "description": "Successfully retrieved language models",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": "lm_123",
                            "integration_id": "openai_int_456",
                            "language_model_tag": "gpt-4",
                            "is_active": True,
                            "created_at": "2024-01-15T10:00:00Z",
                        },
                        {
                            "id": "lm_789",
                            "integration_id": "anthropic_int_012",
                            "language_model_tag": "claude-3-sonnet",
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
    language_model_service: LanguageModelService = Depends(
        Provide[Container.language_model_service]
    ),
):
    """
    Get all configured language models.

    Args:
        language_model_service: Injected language model service

    Returns:
        List[LanguageModel]: All language models in the system
    """
    language_models = language_model_service.get_language_models()
    return [LanguageModel.model_validate(lm) for lm in language_models]


@router.get(
    "/{language_model_id}",
    response_model=LanguageModelExpanded,
    summary="Get language model details",
    description="""
    Retrieve detailed information about a specific language model including
    all its configuration settings.

    This endpoint returns an expanded view that includes:
    - Basic model information (ID, tag, integration)
    - All configuration settings (temperature, max_tokens, etc.)
    - Integration-specific parameters
    - Model capabilities and limitations

    **Use cases:**
    - Display model configuration in admin interface
    - Debug model behavior and settings
    - Export model configurations
    - Validate model setup before agent creation
    """,
    response_description="Detailed language model information with all settings",
    responses={
        200: {
            "description": "Language model details retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "lm_123",
                        "integration_id": "openai_int_456",
                        "language_model_tag": "gpt-4",
                        "is_active": True,
                        "created_at": "2024-01-15T10:00:00Z",
                        "lm_settings": [
                            {
                                "id": "setting_001",
                                "setting_key": "temperature",
                                "setting_value": "0.7",
                                "language_model_id": "lm_123",
                            },
                            {
                                "id": "setting_002",
                                "setting_key": "max_tokens",
                                "setting_value": "2048",
                                "language_model_id": "lm_123",
                            },
                        ],
                    }
                }
            },
        },
        404: {"description": "Language model not found"},
        400: {"description": "Invalid language model ID format"},
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
):
    """
    Get detailed information about a specific language model.

    Args:
        language_model_id: Unique identifier of the language model
        language_model_service: Injected language model service
        language_model_setting_service: Injected settings service

    Returns:
        LanguageModelExpanded: Complete model details with settings

    Raises:
        HTTPException: If model not found or invalid ID
    """
    try:
        language_model = language_model_service.get_language_model_by_id(
            language_model_id
        )
        return _format_expanded_response(language_model, language_model_setting_service)
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Language model with ID {language_model_id} not found",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid language model ID or data corruption: {str(e)}",
        )


@router.post(
    "/create",
    status_code=status.HTTP_201_CREATED,
    response_model=LanguageModel,
    summary="Create a new language model",
    description="""
    Create a new language model configuration linked to an existing integration.

    This endpoint creates a new language model entry that references an existing
    integration (OpenAI, Anthropic, etc.) and specifies which model to use
    (gpt-4, claude-3, etc.).

    **Prerequisites:**
    - Integration must already exist and be properly configured
    - Model tag must be supported by the integration
    - Integration must have valid API credentials

    **Post-Creation Steps:**
    - Configure model settings (temperature, max_tokens, etc.)
    - Test model connectivity
    - Assign to agents as needed

    **Example Model Tags by Integration:**
    - OpenAI: gpt-4, gpt-3.5-turbo, gpt-4-turbo
    - Anthropic: claude-3-opus, claude-3-sonnet, claude-3-haiku
    - xAI: grok-3, grok-2-vision,
    """,
    response_description="Newly created language model",
    responses={
        201: {
            "description": "Language model created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "lm_new_123",
                        "integration_id": "openai_int_456",
                        "language_model_tag": "gpt-4",
                        "is_active": True,
                        "created_at": "2024-01-15T12:00:00Z",
                    }
                }
            },
        },
        400: {"description": "Invalid request data or unsupported model tag"},
        404: {"description": "Integration not found"},
        409: {
            "description": "Language model with this tag already exists for integration"
        },
        422: {"description": "Integration not properly configured"},
    },
)
@inject
async def add(
    language_model_data: LanguageModelCreateRequest = Body(
        ...,
        description="Language model creation data",
        example={"integration_id": "openai_int_456", "language_model_tag": "gpt-4"},
    ),
    language_model_service: LanguageModelService = Depends(
        Provide[Container.language_model_service]
    ),
):
    """
    Create a new language model configuration.

    Args:
        language_model_data: Model creation request data
        language_model_service: Injected language model service

    Returns:
        LanguageModel: Newly created language model

    Raises:
        HTTPException: For various creation errors
    """
    try:
        language_model = language_model_service.create_language_model(
            integration_id=language_model_data.integration_id,
            language_model_tag=language_model_data.language_model_tag,
        )
        return LanguageModel.model_validate(language_model)
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Integration with ID {language_model_data.integration_id} not found",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create language model: {str(e)}",
        )


@router.delete(
    "/delete/{language_model_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a language model",
    description="""
    Permanently delete a language model configuration from the system.

    **Warning:** This action cannot be undone and will:
    - Remove the language model and all its settings
    - Disable any agents currently using this model
    - Break existing conversations that reference this model

    **Before deletion, ensure:**
    - No active agents are using this model
    - Important conversations are backed up
    - Alternative models are configured for affected agents

    **Safe Deletion Process:**
    1. Identify agents using this model
    2. Migrate agents to alternative models
    3. Test agent functionality with new models
    4. Proceed with deletion
    """,
    response_description="Language model successfully deleted (no content returned)",
    responses={
        204: {"description": "Language model successfully deleted"},
        404: {"description": "Language model not found"},
        409: {"description": "Cannot delete model - still in use by active agents"},
        400: {"description": "Invalid language model ID format"},
    },
)
@inject
async def remove(
    language_model_id: str,
    language_model_service: LanguageModelService = Depends(
        Provide[Container.language_model_service]
    ),
):
    """
    Delete a language model by ID.

    Args:
        language_model_id: Unique identifier of the language model to delete
        language_model_service: Injected language model service

    Returns:
        Response: 204 No Content on success

    Raises:
        HTTPException: If model not found or deletion fails
    """
    try:
        language_model_service.delete_language_model_by_id(language_model_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Language model with ID {language_model_id} not found",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot delete language model: {str(e)}",
        )


@router.post(
    "/update",
    response_model=LanguageModel,
    summary="Update language model configuration",
    description="""
    Update the basic configuration of an existing language model.

    Currently supports updating the language model tag, which changes
    which specific model is used within the same integration.

    **Use cases:**
    - Upgrade to newer model versions (gpt-3.5 → gpt-4)
    - Switch between model variants (claude-3-sonnet → claude-3-opus)
    - Test different models without recreating the entire configuration

    **Important Notes:**
    - Model settings (temperature, max_tokens) are preserved
    - Existing conversations remain linked to the model
    - Agent configurations automatically use the new model
    - Ensure the new model tag is supported by the integration
    """,
    response_description="Updated language model configuration",
    responses={
        200: {
            "description": "Language model updated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "lm_123",
                        "integration_id": "openai_int_456",
                        "language_model_tag": "gpt-4-turbo",
                        "is_active": True,
                        "created_at": "2024-01-15T10:00:00Z",
                        "updated_at": "2024-01-15T15:30:00Z",
                    }
                }
            },
        },
        400: {"description": "Invalid request data or unsupported model tag"},
        404: {"description": "Language model not found"},
        422: {"description": "New model tag not supported by integration"},
    },
)
@inject
async def update(
    language_model_data: LanguageModelUpdateRequest = Body(
        ...,
        description="Language model update data",
        example={"language_model_id": "lm_123", "language_model_tag": "gpt-4-turbo"},
    ),
    language_model_service: LanguageModelService = Depends(
        Provide[Container.language_model_service]
    ),
):
    """
    Update an existing language model configuration.

    Args:
        language_model_data: Model update request data
        language_model_service: Injected language model service

    Returns:
        LanguageModel: Updated language model

    Raises:
        HTTPException: If model not found or update fails
    """
    try:
        language_model = language_model_service.update_language_model(
            language_model_id=language_model_data.language_model_id,
            language_model_tag=language_model_data.language_model_tag,
        )
        return LanguageModel.model_validate(language_model)
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Language model with ID {language_model_data.language_model_id} not found",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to update language model: {str(e)}",
        )


@router.post(
    "/update_setting",
    response_model=LanguageModelExpanded,
    summary="Update language model setting",
    description="""
    Update a specific configuration setting for a language model.

    Language models support various settings that control their behavior:

    **Common Settings:**
    - `temperature`: Controls randomness (0.0-1.0)
    - `max_tokens`: Maximum response length (1-4096+)
    - `top_p`: Nucleus sampling parameter (0.0-1.0)
    - `frequency_penalty`: Reduces repetition (-2.0 to 2.0)
    - `presence_penalty`: Encourages topic diversity (-2.0 to 2.0)

    **Best Practices:**
    - Test setting changes with sample conversations
    - Document setting purposes for team members
    - Use conservative values for production environments
    - Monitor token usage after max_tokens changes
    """,
    response_description="Updated language model with all settings",
    responses={
        200: {
            "description": "Setting updated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "lm_123",
                        "integration_id": "openai_int_456",
                        "language_model_tag": "gpt-4",
                        "is_active": True,
                        "created_at": "2024-01-15T10:00:00Z",
                        "lm_settings": [
                            {
                                "id": "setting_001",
                                "setting_key": "temperature",
                                "setting_value": "0.9",
                                "language_model_id": "lm_123",
                                "updated_at": "2024-01-15T16:00:00Z",
                            }
                        ],
                    }
                }
            },
        },
        400: {"description": "Invalid setting key or value"},
        404: {"description": "Language model not found"},
        422: {"description": "Setting value out of valid range"},
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
):
    """
    Update a specific setting for a language model.

    Args:
        language_model_data: Setting update request data
        language_model_service: Injected language model service
        language_model_setting_service: Injected settings service

    Returns:
        LanguageModelExpanded: Updated model with all settings

    Raises:
        HTTPException: If model not found or setting update fails
    """
    try:
        language_model_setting_service.update_by_key(
            language_model_id=language_model_data.language_model_id,
            setting_key=language_model_data.setting_key,
            setting_value=language_model_data.setting_value,
        )

        language_model = language_model_service.get_language_model_by_id(
            language_model_id=language_model_data.language_model_id
        )

        return _format_expanded_response(language_model, language_model_setting_service)

    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Language model with ID {language_model_data.language_model_id} not found",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid setting value: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update setting: {str(e)}",
        )


def _format_expanded_response(
    language_model: DomainLanguageModel,
    language_model_setting_service: LanguageModelSettingService,
) -> LanguageModelExpanded:
    """
    Format an expanded language model response with all settings.

    Args:
        language_model: The language model domain object
        language_model_setting_service: Service to retrieve settings

    Returns:
        LanguageModelExpanded: Complete model data with settings
    """
    settings = language_model_setting_service.get_language_model_settings(
        language_model.id
    )
    response = LanguageModelExpanded.model_validate(language_model)
    response.lm_settings = [
        LanguageModelSetting.model_validate(setting) for setting in settings
    ]
    return response
