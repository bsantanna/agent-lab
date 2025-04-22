from dependency_injector.wiring import inject, Provide
from fastapi import APIRouter, Depends, Body, Response, status
from typing_extensions import List

from app.core.container import Container
from app.domain.exceptions.base import NotFoundError
from app.domain.models import Message as DomainMessage
from app.interface.api.attachments.schema import Attachment
from app.interface.api.messages.schema import (
    MessageListRequest,
    MessageExpanded,
    Message,
    MessageRequest,
)
from app.services.agent_types.registry import AgentRegistry
from app.services.agents import AgentService
from app.services.attachments import AttachmentService
from app.services.messages import MessageService

router = APIRouter()


@router.post("/list", response_model=List[Message])
@inject
async def get_list(
    message_data: MessageListRequest = Body(...),
    message_service: MessageService = Depends(Provide[Container.message_service]),
):
    messages = message_service.get_messages(message_data.agent_id)
    return [Message.model_validate(message) for message in messages]


@router.post("/post", response_model=Message)
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
    human_message = message_service.create_message(
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
        response_data=processed_message.response_data,
        agent_id=processed_message.agent_id,
        replies_to=human_message,
    )

    return Message.model_validate(assistant_message)


@router.get("/{message_id}", response_model=MessageExpanded)
@inject
async def get_by_id(
    message_id: str,
    message_service: MessageService = Depends(Provide[Container.message_service]),
    attachment_service: AttachmentService = Depends(
        Provide[Container.attachment_service]
    ),
):
    try:
        assistant_message = message_service.get_message_by_id(message_id)
        human_message = message_service.get_message_by_id(assistant_message.replies_to)

        return _format_expanded_response(
            assistant_message, human_message, attachment_service
        )

    except NotFoundError:
        return Response(status_code=status.HTTP_404_NOT_FOUND)


@router.delete("/delete/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def remove(
    message_id: str,
    message_service: MessageService = Depends(Provide[Container.message_service]),
):
    try:
        message_service.delete_message_by_id(message_id)
    except NotFoundError:
        return Response(status_code=status.HTTP_404_NOT_FOUND)
    else:
        return Response(status_code=status.HTTP_204_NO_CONTENT)


def _format_expanded_response(
    agent_message: DomainMessage,
    human_message: DomainMessage,
    attachment_service: AttachmentService,
) -> MessageExpanded:
    attachment_response = None

    if human_message.attachment_id is not None:
        attachment = attachment_service.get_attachment_by_id(
            human_message.attachment_id
        )
        attachment_response = Attachment.model_validate(attachment)

    response = MessageExpanded(
        id=agent_message.id,
        is_active=agent_message.is_active,
        created_at=agent_message.created_at,
        agent_id=agent_message.agent_id,
        message_role=agent_message.message_role,
        message_content=agent_message.message_content,
        response_data=agent_message.response_data,
        replies_to=Message.model_validate(human_message),
        attachment=attachment_response,
    )

    return response
