from dependency_injector.wiring import inject, Provide
from fastapi import APIRouter, Depends, Body, Response, status
from fastapi.security import HTTPBearer
from fastapi_keycloak_middleware import get_user
from typing_extensions import List

from app.core.container import Container
from app.domain.exceptions.base import NotFoundError
from app.domain.models import Message as DomainMessage
from app.infrastructure.auth.schema import User
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
bearer_scheme = HTTPBearer()


@router.post(
    "/list",
    dependencies=[Depends(bearer_scheme)],
    response_model=List[Message],
    operation_id="get_message_list",
    summary="Retrieve messages for an agent",
    description="""
    Retrieve a list of messages associated with a specific agent.

    This endpoint returns all messages (both human and assistant) for the given agent ID.
    Messages include content, role, timestamps, and relationships.

    **Use cases:**
    - Display conversation history
    - Load previous messages for context
    - Message thread reconstruction
    - Memory and history of dialogues
    - Chain-of-thought reasoning

    **Recommended Practices:**
    - Use structured information for details and chain-of-thought reasoning
    - When displaying messages use the format -role: content

    """,
    response_description="List of messages associated with the agent",
    responses={
        200: {
            "description": "Successfully retrieved messages",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": "msg_123",
                            "message_role": "human",
                            "message_content": "Hello, how can you help?",
                            "agent_id": "agent_456",
                            "created_at": "2024-01-15T10:30:00Z",
                            "is_active": True,
                        }
                    ]
                }
            },
        },
        404: {"description": "Agent not found"},
    },
)
@inject
async def get_list(
    message_data: MessageListRequest = Body(
        ...,
        description="Request containing the agent ID to retrieve messages for",
        example={"agent_id": "agent_456"},
    ),
    message_service: MessageService = Depends(Provide[Container.message_service]),
    user: User = Depends(get_user),
):
    """
    Get all messages for a specific agent.

    Args:
        message_data: Contains the agent_id to filter messages
        message_service: Injected message service dependency


    Returns:
        List[Message]: All messages associated with the agent
    """
    schema = user.id.replace("-", "_") if user is not None else "public"
    messages = message_service.get_messages(message_data.agent_id, schema)
    return [Message.model_validate(message) for message in messages]


@router.post(
    "/post",
    dependencies=[Depends(bearer_scheme)],
    response_model=Message,
    operation_id="post_message",
    summary="Send a message to an agent",
    description="""
    Send a new message to an AI agent and receive a response.

    This endpoint processes human messages through the appropriate agent type,
    stores both the human message and generated response, and returns the
    assistant's reply.

    **Message Processing Flow:**
    1. Validates the target agent exists
    2. Stores the incoming human message
    3. Routes message to appropriate agent processor
    4. Generates and stores assistant response
    5. Returns the assistant message

    **Use cases:**
    - Agent-to-agent interactions
    - Conversational AI applications
    - Task scheduling and automation through agents
    - Request of assistance from available agents
    - Question answering and information retrieval

    **Recommended Practices:**
    - Maintain a fluid conversation flow
    - Use structured information for details and chain-of-thought reasoning
    - When displaying messages, always present the agent message response to the user


    """,
    response_description="The assistant's response message",
    responses={
        200: {
            "description": "Message successfully processed and response generated",
            "content": {
                "application/json": {
                    "example": {
                        "id": "msg_789",
                        "message_role": "assistant",
                        "message_content": "I'd be happy to help you with that!",
                        "agent_id": "agent_456",
                        "created_at": "2024-01-15T10:31:00Z",
                        "is_active": True,
                        "replies_to": "msg_123",
                    }
                }
            },
        },
        400: {"description": "Invalid request data fields"},
        404: {"description": "Agent not found"},
        422: {"description": "Invalid request data unprocessable entity"},
    },
)
@inject
async def post_message(
    message_data: MessageRequest = Body(
        ...,
        description="The message to send to the agent",
        example={
            "agent_id": "agent_456",
            "message_role": "human",
            "message_content": "Can you help me write a Python function?",
            "attachment_id": None,
        },
    ),
    agent_service: AgentService = Depends(Provide[Container.agent_service]),
    agent_registry: AgentRegistry = Depends(Provide[Container.agent_registry]),
    message_service: MessageService = Depends(Provide[Container.message_service]),
    user: User = Depends(get_user),
):
    """
    Process a new message through an AI agent.

    Args:
        message_data: The message request containing content and agent info
        agent_service: Service for agent management
        agent_registry: Registry of available agent types
        message_service: Service for message persistence

    Returns:
        Message: The assistant's response message
    """
    schema = user.id.replace("-", "_") if user is not None else "public"
    agent = agent_service.get_agent_by_id(message_data.agent_id, schema)
    matching_agent = agent_registry.get_agent(agent.agent_type)

    # Store human message
    human_message = message_service.create_message(
        message_role=message_data.message_role,
        message_content=message_data.message_content,
        agent_id=message_data.agent_id,
        attachment_id=message_data.attachment_id,
        schema=schema,
    )

    # Process human message
    processed_message = matching_agent.process_message(message_data, schema)

    # Store assistant message
    assistant_message = message_service.create_message(
        message_role="assistant",
        message_content=processed_message.message_content,
        response_data=processed_message.response_data,
        agent_id=processed_message.agent_id,
        replies_to=human_message,
        schema=schema,
    )

    return Message.model_validate(assistant_message)


@router.get(
    "/{message_id}",
    dependencies=[Depends(bearer_scheme)],
    response_model=MessageExpanded,
    summary="Get expanded message details",
    description="""
    Retrieve detailed information about a specific message and its context.

    This endpoint returns an expanded view of an assistant message that includes:
    - The assistant message details
    - The original human message it replies to
    - Any attachments from the human message
    - Full conversation context

    **Use cases:**
    - Display complete message thread
    - Show message with attachments
    - Debug conversation flow
    - Export conversation data
    """,
    response_description="Expanded message with full context and attachments",
    responses={
        200: {
            "description": "Message details retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "msg_789",
                        "message_role": "assistant",
                        "message_content": "Here's the Python function you requested...",
                        "agent_id": "agent_456",
                        "created_at": "2024-01-15T10:31:00Z",
                        "is_active": True,
                        "replies_to": {
                            "id": "msg_123",
                            "message_role": "human",
                            "message_content": "Can you help me write a Python function?",
                            "created_at": "2024-01-15T10:30:00Z",
                        },
                        "attachment": {
                            "id": "att_456",
                            "filename": "requirements.txt",
                            "content_type": "text/plain",
                        },
                    }
                }
            },
        },
        404: {"description": "Message not found"},
    },
)
@inject
async def get_by_id(
    message_id: str,
    message_service: MessageService = Depends(Provide[Container.message_service]),
    attachment_service: AttachmentService = Depends(
        Provide[Container.attachment_service]
    ),
    user: User = Depends(get_user),
):
    """
    Get expanded details for a specific message.

    Args:
        message_id: Unique identifier of the message
        message_service: Injected message service
        attachment_service: Injected attachment service

    Returns:
        MessageExpanded: Complete message details with context
    """
    schema = user.id.replace("-", "_") if user is not None else "public"
    assistant_message = message_service.get_message_by_id(message_id, schema)
    human_message = message_service.get_message_by_id(
        assistant_message.replies_to, schema
    )

    return _format_expanded_response(
        assistant_message, human_message, attachment_service, schema
    )


@router.delete(
    "/delete/{message_id}",
    dependencies=[Depends(bearer_scheme)],
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a message",
    description="""
    Permanently delete a message from the system.

    **Warning:** This action cannot be undone. Deleting a message will:
    - Remove the message from all conversations
    - Break reply chains if other messages reference it
    - Not affect related attachments (they remain for other references)

    **Best Practices:**
    - Consider soft deletion (marking as inactive) instead
    - Ensure no critical conversation flow depends on this message
    - Back up important conversations before deletion
    """,
    response_description="Message successfully deleted (no content returned)",
    responses={
        204: {"description": "Message successfully deleted"},
        404: {"description": "Message not found"},
    },
)
@inject
async def remove(
    message_id: str,
    message_service: MessageService = Depends(Provide[Container.message_service]),
    user: User = Depends(get_user),
):
    """
    Delete a message by ID.

    Returns:
        Response: 204 No Content on success

    """
    schema = user.id.replace("-", "_") if user is not None else "public"
    message_service.delete_message_by_id(message_id, schema)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _format_expanded_response(
    agent_message: DomainMessage,
    human_message: DomainMessage,
    attachment_service: AttachmentService,
    schema: str,
) -> MessageExpanded:
    """
    Format an expanded message response with full context.

    Args:
        agent_message: The assistant message
        human_message: The original human message
        attachment_service: Service to retrieve attachment details

    Returns:
        MessageExpanded: Formatted response with all related data
    """
    attachment_response = None

    if human_message.attachment_id is not None:
        try:
            attachment = attachment_service.get_attachment_by_id(
                human_message.attachment_id, schema
            )
            attachment_response = Attachment.model_validate(attachment)
        except NotFoundError:
            # Attachment was deleted or corrupted, continue without it
            pass

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
