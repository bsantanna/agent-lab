import asyncio
import json

from dependency_injector.wiring import Provide, inject
from fastapi import (
    APIRouter,
    Body,
    Depends,
    Response,
    status,
    WebSocket,
    WebSocketDisconnect,
)
from typing_extensions import List

from app.core.container import Container
from app.domain.exceptions.base import NotFoundError
from app.domain.models import Agent as DomainAgent
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

router = APIRouter()


@router.get("/list", response_model=List[Agent])
@inject
async def get_list(
    agent_service: AgentService = Depends(Provide[Container.agent_service]),
):
    agents = agent_service.get_agents()
    return [Agent.model_validate(agent) for agent in agents]


@router.get("/{agent_id}", response_model=AgentExpanded)
@inject
async def get_by_id(
    agent_id: str,
    agent_service: AgentService = Depends(Provide[Container.agent_service]),
    agent_setting_service: AgentSettingService = Depends(
        Provide[Container.agent_setting_service]
    ),
):
    try:
        agent = agent_service.get_agent_by_id(agent_id)

        return _format_expanded_response(agent, agent_setting_service)
    except NotFoundError:
        return Response(status_code=status.HTTP_404_NOT_FOUND)


@router.post("/create", status_code=status.HTTP_201_CREATED, response_model=Agent)
@inject
async def add(
    agent_data: AgentCreateRequest = Body(...),
    agent_service: AgentService = Depends(Provide[Container.agent_service]),
    agent_registry: AgentRegistry = Depends(Provide[Container.agent_registry]),
):
    agent = agent_service.create_agent(
        language_model_id=agent_data.language_model_id,
        agent_name=agent_data.agent_name,
        agent_type=agent_data.agent_type,
    )
    agent_registry.get_agent(agent_data.agent_type).create_default_settings(
        agent_id=agent.id
    )
    return Agent.model_validate(agent)


@router.delete("/delete/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def remove(
    agent_id: str,
    agent_service: AgentService = Depends(Provide[Container.agent_service]),
):
    try:
        agent_service.delete_agent_by_id(agent_id)
    except NotFoundError:
        return Response(status_code=status.HTTP_404_NOT_FOUND)
    else:
        return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(path="/update", response_model=Agent)
@inject
async def update(
    agent_data: AgentUpdateRequest = Body(...),
    agent_service: AgentService = Depends(Provide[Container.agent_service]),
):
    try:
        agent = agent_service.update_agent(
            agent_id=agent_data.agent_id,
            agent_name=agent_data.agent_name,
        )
        return Agent.model_validate(agent)
    except NotFoundError:
        return Response(status_code=status.HTTP_404_NOT_FOUND)


@router.post(path="/update_setting", response_model=AgentExpanded)
@inject
async def update_setting(
    agent_data: AgentSettingUpdateRequest = Body(...),
    agent_service: AgentService = Depends(Provide[Container.agent_service]),
    agent_setting_service: AgentSettingService = Depends(
        Provide[Container.agent_setting_service]
    ),
):
    try:
        agent_setting_service.update_by_key(
            agent_id=agent_data.agent_id,
            setting_key=agent_data.setting_key,
            setting_value=agent_data.setting_value,
        )

        agent = agent_service.get_agent_by_id(agent_id=agent_data.agent_id)

        return _format_expanded_response(agent, agent_setting_service)

    except NotFoundError:
        return Response(status_code=status.HTTP_404_NOT_FOUND)


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
    agent: DomainAgent, agent_setting_service: AgentSettingService
) -> AgentExpanded:
    settings = agent_setting_service.get_agent_settings(agent_id=agent.id)
    response = AgentExpanded.model_validate(agent)
    response.ag_settings = [
        AgentSetting.model_validate(setting) for setting in settings
    ]
    return response
