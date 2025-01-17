from typing import List

from dependency_injector.wiring import inject, Provide
from fastapi import APIRouter, Depends, Body, Response, status, File

from app.core.container import Container
from app.domain.exceptions.base import NotFoundError
from app.domain.models import Message
from app.interface.api.messages.schema import (
    MessageBase,
    MessageListRequest,
    MessageExpandedResponse,
    AttachmentResponse,
    MessageResponse,
    MessageRequest,
)
from app.services.agent_types.registry import AgentRegistry
from app.services.agents import AgentService
from app.services.attachments import AttachmentService
from app.services.messages import MessageService

router = APIRouter()


@router.post("/list", response_model=List[MessageResponse])
@inject
async def get_list(
    message_data: MessageListRequest = Body(...),
    message_service: MessageService = Depends(Provide[Container.message_service]),
):
    messages = message_service.get_messages(message_data.agent_id)
    return [MessageBase.model_validate(message) for message in messages]


@router.post(
    "/attachment/upload",
    status_code=status.HTTP_201_CREATED,
    response_model=AttachmentResponse,
)
@inject
async def upload_attachment(
    file=File(...),
    attachment_service: AttachmentService = Depends(
        Provide[Container.attachment_service]
    ),
):
    attachment = await attachment_service.create_attachment(file=file)

    return AttachmentResponse.model_validate(attachment)


@router.post("/post", response_model=MessageResponse)
@inject
async def post_message(
    message_data: MessageRequest = Body(...),
    agent_service: AgentService = Depends(Provide[Container.agent_service]),
    agent_registry: AgentRegistry = Depends(Provide[Container.agent_registry]),
    message_service: MessageService = Depends(Provide[Container.message_service]),
):
    # search matching agent
    try:
        agent = agent_service.get_agent_by_id(message_data.agent_id)
        matching_agent = agent_registry.get_agent(agent.agent_type)
    except NotFoundError:
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    # store human message
    message_service.create_message(
        message_role=message_data.message_role,
        message_content=message_data.message_content,
        agent_id=message_data.agent_id,
        attachment_id=message_data.attachment_id,
    )

    # process human message
    processed_message = matching_agent.process_message(message_data)

    # store assistant message
    assistant_message = message_service.create_message(
        message_role="assistant",
        message_content=processed_message.message_content,
        agent_id=processed_message.agent_id,
    )

    return MessageResponse.model_validate(assistant_message)


@router.get("/{message_id}", response_model=MessageExpandedResponse)
@inject
async def get_by_id(
    message_id: str,
    message_service: MessageService = Depends(Provide[Container.message_service]),
    attachment_service: AttachmentService = Depends(
        Provide[Container.attachment_service]
    ),
):
    try:
        message = message_service.get_message_by_id(message_id)

        return _format_expanded_response(message, attachment_service)
    except NotFoundError:
        return Response(status_code=status.HTTP_404_NOT_FOUND)


def _format_expanded_response(
    message: Message, attachment_service: AttachmentService
) -> MessageExpandedResponse:
    response = MessageExpandedResponse.model_validate(message)

    if message.attachment_id is not None:
        attachment = attachment_service.get_attachment_by_id(message.attachment_id)
        response.att = AttachmentResponse.model_validate(attachment)

    return response
