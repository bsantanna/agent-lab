from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Response, status

from app.application.services.agents import AgentService, AgentSettingService
from app.core.container import Container
from app.domain.exceptions.base import NotFoundError
from app.domain.models import Agent
from app.interface.api.agents.schema import (
    AgentResponse,
    AgentExpandedResponse,
    AgentSettingResponse,
)

router = APIRouter()


@router.get("/list")
@inject
def get_list(
    agent_service: AgentService = Depends(Provide[Container.agent_service]),
):
    agents = agent_service.get_agents()
    return [AgentResponse.model_validate(agent) for agent in agents]


@router.get("/{agent_id}")
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


@router.post("/create", status_code=status.HTTP_201_CREATED)
@inject
def add(
    agent_service: AgentService = Depends(Provide[Container.agent_service]),
):
    return agent_service.create_agent()


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


def _format_expanded_response(
    agent: Agent, agent_setting_service: AgentSettingService
) -> AgentExpandedResponse:
    settings = agent_setting_service.get_agent_settings(agent_id=agent.id)
    response = AgentExpandedResponse.model_validate(agent)
    response.ag_settings = [
        AgentSettingResponse.model_validate(setting) for setting in settings
    ]
    return response
