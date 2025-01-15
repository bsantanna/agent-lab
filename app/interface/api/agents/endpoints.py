from typing import List

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Response, status, Body

from app.services.agents import AgentService, AgentSettingService
from app.core.container import Container
from app.domain.exceptions.base import NotFoundError
from app.domain.models import Agent
from app.interface.api.agents.schema import (
    AgentResponse,
    AgentExpandedResponse,
    AgentSettingResponse,
    AgentCreateRequest,
    AgentUpdateRequest,
    AgentSettingUpdateRequest,
)

router = APIRouter()


@router.get("/list", response_model=List[AgentResponse])
@inject
def get_list(
    agent_service: AgentService = Depends(Provide[Container.agent_service]),
):
    agents = agent_service.get_agents()
    return [AgentResponse.model_validate(agent) for agent in agents]


@router.get("/{agent_id}", response_model=AgentExpandedResponse)
@inject
def get_by_id(
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


@router.post(
    "/create", status_code=status.HTTP_201_CREATED, response_model=AgentResponse
)
@inject
def add(
    agent_data: AgentCreateRequest = Body(...),
    agent_service: AgentService = Depends(Provide[Container.agent_service]),
):
    agent = agent_service.create_agent(
        language_model_id=agent_data.language_model_id,
        agent_name=agent_data.agent_name,
        agent_type=agent_data.agent_type,
    )
    return AgentResponse.model_validate(agent)


@router.delete("/delete/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
@inject
def remove(
    agent_id: str,
    agent_service: AgentService = Depends(Provide[Container.agent_service]),
):
    try:
        agent_service.delete_agent_by_id(agent_id)
    except NotFoundError:
        return Response(status_code=status.HTTP_404_NOT_FOUND)
    else:
        return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(path="/update", response_model=AgentResponse)
@inject
def update(
    agent_data: AgentUpdateRequest = Body(...),
    agent_service: AgentService = Depends(Provide[Container.agent_service]),
):
    try:
        agent = agent_service.update_agent(
            agent_id=agent_data.agent_id,
            agent_name=agent_data.agent_name,
        )
        return AgentResponse.model_validate(agent)
    except NotFoundError:
        return Response(status_code=status.HTTP_404_NOT_FOUND)


@router.post(path="/update_setting", response_model=AgentExpandedResponse)
@inject
def update_setting(
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


def _format_expanded_response(
    agent: Agent, agent_setting_service: AgentSettingService
) -> AgentExpandedResponse:
    settings = agent_setting_service.get_agent_settings(agent_id=agent.id)
    response = AgentExpandedResponse.model_validate(agent)
    response.ag_settings = [
        AgentSettingResponse.model_validate(setting) for setting in settings
    ]
    return response
