import asyncio
import json

from dependency_injector.wiring import Provide, inject
from fastapi import (
    APIRouter,
    Body,
    Depends,
    status,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.security import HTTPBearer
from fastapi_keycloak_middleware import get_user
from typing_extensions import List

from app.core.container import Container
from app.domain.models import Agent as DomainAgent
from app.infrastructure.auth.schema import User
from app.interface.api.agents.schema import (
    AgentCreateRequest,
    AgentExpanded,
    Agent,
    AgentSetting,
    AgentSettingUpdateRequest,
    AgentUpdateRequest,
)
from app.services.agent_settings import AgentSettingService
from app.services.agent_types.registry import AgentRegistry
from app.services.agents import AgentService
from app.services.tasks import TaskNotificationService

from app.interface.api.agents.schema import valid_agent_types

router = APIRouter()
bearer_scheme = HTTPBearer()


@router.get(
    path="/list",
    dependencies=[Depends(bearer_scheme)],
    response_model=List[Agent],
    operation_id="get_agent_list",
    summary="Get all agents",
    description="""
    Retrieve a list of all agents in the platform.

    This endpoint returns all agents with information including:
    - Agent ID and name
    - Agent type
    - Creation timestamps
    - Agent summary

    **Use cases:**
    - Get information about all agents and corresponding capabilities
    - View agent types and their configurations
    - Retrieve agent summaries for quick reference
    - Identify potential agents for specific tasks
    """,
    response_description="List of all agents in the platform",
    responses={
        200: {
            "description": "Successfully retrieved agents list",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": "agent_123456789",
                            "agent_name": "Image Analyzer",
                            "agent_type": "vision_document",
                            "agent_summary": "Analyzes images and extracts information",
                            "language_model_id": "adeadeakdnekn",
                            "created_at": "2024-01-15T10:30:00Z",
                            "is_active": True,
                        },
                        {
                            "id": "agent_987654321",
                            "agent_name": "Customer Support Bot",
                            "agent_type": "agreement_planner",
                            "agent_summary": "Handles customer inquiries and support requests",
                            "language_model_id": "deafejfiejafje",
                            "created_at": "2024-01-14T15:20:00Z",
                            "is_active": True,
                        },
                    ]
                }
            },
        }
    },
)
@inject
async def get_list(
    agent_service: AgentService = Depends(Provide[Container.agent_service]),
    user: User = Depends(get_user),
):
    schema = user.id.replace("-", "_") if user is not None else "public"
    agents = agent_service.get_agents(schema)
    return [Agent.model_validate(agent) for agent in agents]


@router.get(
    path="/{agent_id}",
    dependencies=[Depends(bearer_scheme)],
    response_model=AgentExpanded,
    summary="Get agent by ID",
    description="Retrieve detailed information about a specific agent by its unique identifier.",
    response_description="Detailed agent information with settings",
    responses={
        200: {
            "description": "Successfully retrieved agent details",
            "content": {
                "application/json": {
                    "example": {
                        "id": "agent_123456789",
                        "agent_name": "Content Analyzer",
                        "agent_type": "analyzer",
                        "language_model_id": "gpt-4",
                        "created_at": "2024-01-15T10:30:00Z",
                        "is_active": True,
                        "ag_settings": [
                            {
                                "id": "setting_001",
                                "setting_key": "max_tokens",
                                "setting_value": "2048",
                            },
                            {
                                "id": "setting_002",
                                "setting_key": "temperature",
                                "setting_value": "0.7",
                            },
                        ],
                    }
                }
            },
        },
        404: {
            "description": "Agent not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Agent with ID 'agent_123456789' not found"}
                }
            },
        },
    },
)
@inject
async def get_by_id(
    agent_id: str,
    agent_service: AgentService = Depends(Provide[Container.agent_service]),
    agent_setting_service: AgentSettingService = Depends(
        Provide[Container.agent_setting_service]
    ),
    user: User = Depends(get_user),
):
    schema = user.id.replace("-", "_") if user is not None else "public"
    agent = agent_service.get_agent_by_id(agent_id, schema)
    return _format_expanded_response(agent, agent_setting_service, schema)


@router.post(
    path="/create",
    dependencies=[Depends(bearer_scheme)],
    status_code=status.HTTP_201_CREATED,
    response_model=Agent,
    summary="Create a new agent",
    description=f"""
    Create a new agent with specified configuration.

    This endpoint creates a new agent instance with the provided settings and
    automatically initializes default configuration based on the agent type.

    Agent Types Available: {valid_agent_types}

    **Process:**
    1. Create and integration
    2. Create a language model linked to the integration
    3. Create an agent with the specified language model and agent type
    4. Call the agent using `post_message` operation
    """,
    response_description="Successfully created agent information",
    responses={
        201: {
            "description": "Agent successfully created",
            "content": {
                "application/json": {
                    "example": {
                        "id": "agent_123456789",
                        "agent_name": "Content Analyzer",
                        "agent_type": "analyzer",
                        "language_model_id": "shdehfuehfuef",
                        "created_at": "2024-01-15T10:30:00Z",
                        "is_active": True,
                    }
                }
            },
        },
        400: {
            "description": "Bad request - Invalid agent configuration",
            "content": {
                "application/json": {"example": {"detail": "Invalid agent type"}}
            },
        },
        404: {
            "description": "Language model not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Language model with ID 'lm_123456789' not found"
                    }
                }
            },
        },
        422: {
            "description": "Invalid data unprocessable entity",
        },
    },
)
@inject
async def add(
    agent_data: AgentCreateRequest = Body(...),
    agent_service: AgentService = Depends(Provide[Container.agent_service]),
    agent_registry: AgentRegistry = Depends(Provide[Container.agent_registry]),
    user: User = Depends(get_user),
):
    schema = user.id.replace("-", "_") if user is not None else "public"
    agent = agent_service.create_agent(
        language_model_id=agent_data.language_model_id,
        agent_name=agent_data.agent_name,
        agent_type=agent_data.agent_type,
        schema=schema,
    )
    agent_registry.get_agent(agent_data.agent_type).create_default_settings(
        agent_id=agent.id
    )
    return Agent.model_validate(agent)


@router.delete(
    path="/delete/{agent_id}",
    dependencies=[Depends(bearer_scheme)],
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an agent",
    description="This endpoint removes an agent from the system including",
    response_description="Agent successfully deleted",
    responses={
        204: {"description": "Agent successfully deleted"},
        404: {
            "description": "Agent not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Agent with ID 'agent_123456789' not found"}
                }
            },
        },
    },
)
@inject
async def remove(
    agent_id: str,
    agent_service: AgentService = Depends(Provide[Container.agent_service]),
    user: User = Depends(get_user),
):
    schema = user.id.replace("-", "_") if user is not None else "public"
    agent_service.delete_agent_by_id(agent_id, schema)


@router.post(
    path="/update",
    dependencies=[Depends(bearer_scheme)],
    response_model=Agent,
    summary="Update agent basic information",
    description="Update agent information such as name and configuration.",
    response_description="Updated agent information",
    responses={
        200: {
            "description": "Agent successfully updated",
            "content": {
                "application/json": {
                    "example": {
                        "id": "agent_123456789",
                        "agent_name": "Updated Content Analyzer",
                        "agent_type": "vision_document",
                        "language_model_id": "23232323",
                        "created_at": "2024-01-15T10:30:00Z",
                        "is_active": True,
                    }
                }
            },
        },
        404: {
            "description": "Agent or language model not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Agent with ID 'agent_123456789' not found"}
                }
            },
        },
        400: {
            "description": "Bad request - Invalid agent name",
            "content": {
                "application/json": {"example": {"detail": "Invalid agent name"}}
            },
        },
        422: {"description": "Validation error"},
    },
)
@inject
async def update(
    agent_data: AgentUpdateRequest = Body(...),
    agent_service: AgentService = Depends(Provide[Container.agent_service]),
    user: User = Depends(get_user),
):
    schema = user.id.replace("-", "_") if user is not None else "public"
    agent = agent_service.update_agent(
        agent_id=agent_data.agent_id,
        agent_name=agent_data.agent_name,
        language_model_id=agent_data.language_model_id,
        agent_summary=agent_data.agent_summary,
        schema=schema,
    )
    return Agent.model_validate(agent)


@router.post(
    path="/update_setting",
    dependencies=[Depends(bearer_scheme)],
    response_model=AgentExpanded,
    summary="Update agent setting",
    description="""
    Update a specific agent setting by key.

    This endpoint allows fine-grained control over agent behavior by modifying
    individual configuration settings.
    """,
    response_description="Updated agent with all current settings",
    responses={
        200: {
            "description": "Setting successfully updated",
            "content": {
                "application/json": {
                    "example": {
                        "id": "agent_123456789",
                        "agent_name": "Content Analyzer",
                        "agent_type": "vision_document",
                        "language_model_id": "dedeafefaeaf",
                        "created_at": "2024-01-15T10:30:00Z",
                        "is_active": True,
                        "ag_settings": [
                            {
                                "id": "setting_001",
                                "setting_key": "max_tokens",
                                "setting_value": "4096",
                            },
                            {
                                "id": "setting_002",
                                "setting_key": "temperature",
                                "setting_value": "0.5",
                            },
                        ],
                    }
                }
            },
        },
        404: {
            "description": "Agent not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Agent with ID 'agent_123456789' not found"}
                }
            },
        },
        400: {
            "description": "Bad request - Invalid setting key or value",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid value for setting xyz"}
                }
            },
        },
        422: {
            "description": "Invalid setting key or value",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Setting 'temperature' must be between 0.0 and 2.0"
                    }
                }
            },
        },
    },
)
@inject
async def update_setting(
    agent_data: AgentSettingUpdateRequest = Body(...),
    agent_service: AgentService = Depends(Provide[Container.agent_service]),
    agent_setting_service: AgentSettingService = Depends(
        Provide[Container.agent_setting_service]
    ),
    user: User = Depends(get_user),
):
    schema = user.id.replace("-", "_") if user is not None else "public"
    agent_setting_service.update_by_key(
        agent_id=agent_data.agent_id,
        setting_key=agent_data.setting_key,
        setting_value=agent_data.setting_value,
        schema=schema,
    )

    agent = agent_service.get_agent_by_id(agent_data.agent_id, schema)
    return _format_expanded_response(agent, agent_setting_service, schema)


@router.websocket("/ws/task_updates/{agent_id}")
@inject
async def task_updates_endpoint(
    websocket: WebSocket,
    agent_id: str,
    task_notification_service: TaskNotificationService = Depends(
        Provide[Container.task_notification_service]
    ),
):
    await websocket.accept()
    task_notification_service.subscribe()
    loop = asyncio.get_event_loop()

    def get_next_message():
        return next(task_notification_service.listen())

    try:
        while True:
            try:
                message = await asyncio.wait_for(
                    loop.run_in_executor(None, get_next_message), timeout=30
                )
            except asyncio.TimeoutError:
                break

            if message.get("type") != "message":
                continue
            try:
                data = json.loads(message["data"])
            except (ValueError, TypeError):
                continue
            if data.get("agent_id") == agent_id:
                await websocket.send_json(data)
                break
    except WebSocketDisconnect:
        pass
    finally:
        task_notification_service.close()


def _format_expanded_response(
    agent: DomainAgent, agent_setting_service: AgentSettingService, schema: str
) -> AgentExpanded:
    settings = agent_setting_service.get_agent_settings(agent.id, schema)
    response = AgentExpanded.model_validate(agent)
    response.ag_settings = [
        AgentSetting.model_validate(setting) for setting in settings
    ]
    return response
