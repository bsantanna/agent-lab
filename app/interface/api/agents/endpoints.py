from io import StringIO

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Body, Depends, Response, status
from fastapi.responses import StreamingResponse
from typing_extensions import List

from app.core.container import Container
from app.domain.exceptions.base import NotFoundError
from app.domain.models import Agent
from app.interface.api.agents.schema import (
    AgentCreateRequest,
    AgentExpandedResponse,
    AgentResponse,
    AgentSettingResponse,
    AgentSettingUpdateRequest,
    AgentUpdateRequest,
)
from app.services.agent_settings import AgentSettingService
from app.services.agent_types.registry import AgentRegistry
from app.services.agents import AgentService
from app.services.messages import MessageService

router = APIRouter()


@router.get("/list", response_model=List[AgentResponse])
@inject
async def get_list(
    agent_service: AgentService = Depends(Provide[Container.agent_service]),
):
    agents = agent_service.get_agents()
    return [AgentResponse.model_validate(agent) for agent in agents]


@router.get("/{agent_id}", response_model=AgentExpandedResponse)
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


@router.get("/dataset/{agent_id}", response_class=StreamingResponse)
@inject
async def get_dataset_format(
    agent_id: str,
    agent_service: AgentService = Depends(Provide[Container.agent_service]),
    message_service: MessageService = Depends(Provide[Container.message_service]),
):
    agent = agent_service.get_agent_by_id(agent_id)
    messages = message_service.get_messages(agent_id)

    json_content = StringIO()
    json_content.write("[")

    first_message = True
    message_dict = {}

    # Group messages by replies_to
    for message in messages:
        if message.message_role == "human":
            message_dict[message.id] = {
                "human": message.message_content,
                "assistant": None
            }
        elif message.message_role == "assistant" and message.replies_to:
            if message.replies_to in message_dict:
                message_dict[message.replies_to]["assistant"] = message.message_content

    # Write paired messages to JSON
    for msg_pair in message_dict.values():
        if msg_pair["assistant"]:  # Only write if we have both human and assistant messages
            if not first_message:
                json_content.write(",")
            json_content.write(
                f'{{"text": "Human: {msg_pair["human"]}\\nAgent: {msg_pair["assistant"]}"}}'
            )
            first_message = False

    json_content.write("]")
    json_content.seek(0)

    filename = f"{agent.agent_type}_{agent.agent_name}.json"
    return StreamingResponse(
        json_content,
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
        }
    )

@router.post(
    "/create", status_code=status.HTTP_201_CREATED, response_model=AgentResponse
)
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
    return AgentResponse.model_validate(agent)


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


@router.post(path="/update", response_model=AgentResponse)
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
        return AgentResponse.model_validate(agent)
    except NotFoundError:
        return Response(status_code=status.HTTP_404_NOT_FOUND)


@router.post(path="/update_setting", response_model=AgentExpandedResponse)
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


def _format_expanded_response(
    agent: Agent, agent_setting_service: AgentSettingService
) -> AgentExpandedResponse:
    settings = agent_setting_service.get_agent_settings(agent_id=agent.id)
    response = AgentExpandedResponse.model_validate(agent)
    response.ag_settings = [
        AgentSettingResponse.model_validate(setting) for setting in settings
    ]
    return response
