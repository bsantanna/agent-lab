from typing import List

from dependency_injector.wiring import inject, Provide
from fastapi import APIRouter, Depends, Body

from app.core.container import Container
from app.interface.api.messages.schema import MessageBase, MessageListRequest
from app.services.messages import MessageService

router = APIRouter()


@router.post("/list", response_model=List[MessageBase])
@inject
def get_list(
    message_data: MessageListRequest = Body(...),
    message_service: MessageService = Depends(Provide[Container.message_service]),
):
    messages = message_service.get_messages(message_data.agent_id)
    return [MessageBase.model_validate(message) for message in messages]
