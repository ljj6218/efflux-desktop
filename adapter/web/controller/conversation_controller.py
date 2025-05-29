from fastapi import APIRouter, Depends
from common.core.logger import get_logger
from common.core.container.container import get_container
from application.port.inbound.conversation_case import ConversationCase
from application.domain.conversation import DialogSegment
from adapter.web.vo.base_response import BaseResponse
from adapter.web.vo.conversation_vo import DialogSegmentDelVo, ConversationDelVo

from typing import Optional
logger = get_logger(__name__)

router = APIRouter(prefix="/api/conversation", tags=["CONVERSATION"])

def conversation_case() -> ConversationCase:
    return get_container().get(ConversationCase)

@router.get("/list")
async def load_conversation_list(conversation_service: ConversationCase = Depends(conversation_case)) -> BaseResponse:
    return BaseResponse.from_success(data=await conversation_service.conversation_load_list())

@router.get("")
async def load_conversation(conversation_id: Optional[str] = None, conversation_service: ConversationCase = Depends(conversation_case)) -> BaseResponse:
    return BaseResponse.from_success(data=await conversation_service.conversation_load(conversation_id=conversation_id))

@router.put("/theme")
async def update_conversation_theme(conversation_id: str, conversation_theme: str, conversation_service: ConversationCase = Depends(conversation_case)) -> BaseResponse:
    return BaseResponse.from_success(data=await conversation_service.conversation_update_theme(conversation_id=conversation_id, theme=conversation_theme))

@router.delete("/list")
async def del_conversation_list(conversation_vo: ConversationDelVo, conversation_service: ConversationCase = Depends(conversation_case)) -> BaseResponse:
    return BaseResponse.from_success(data=await conversation_service.conversation_remove(conversation_vo.id_list))

@router.delete("/dialog_segment")
async def del_dialog_segment(dialog_segment_vo :DialogSegmentDelVo, conversation_service: ConversationCase = Depends(conversation_case)):
    return BaseResponse.from_success(data=await conversation_service.conversation_remove_dialog_segment(DialogSegment(id=dialog_segment_vo.id, conversation_id=dialog_segment_vo.conversation_id)))