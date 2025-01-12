from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Response, status

from app.application.services.agent import AgentService
from app.core.container import Container
from app.domain.exceptions.base import NotFoundError

router = APIRouter()


@router.get("/list")
@inject
def get_list(
    agent_service: AgentService = Depends(Provide[Container.agent_service]),
):
    return agent_service.get_agents()


@router.get("/{agent_id}")
@inject
def get_by_id(
    agent_id: int,
    agent_service: AgentService = Depends(Provide[Container.agent_service]),
):
    try:
        return agent_service.get_agent_by_id(agent_id)
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
    agent_id: int,
    agent_service: AgentService = Depends(Provide[Container.agent_service]),
):
    try:
        agent_service.delete_agent_by_id(agent_id)
    except NotFoundError:
        return Response(status_code=status.HTTP_404_NOT_FOUND)
    else:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
