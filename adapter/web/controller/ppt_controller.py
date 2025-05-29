from fastapi import APIRouter, Depends
from common.core.logger import get_logger
from common.core.container.container import get_container
from application.port.inbound.ppt_case import PPTCase
from adapter.web.vo.ppt_vo import PPTVo
from adapter.web.vo.base_response import BaseResponse
logger = get_logger(__name__)

def ppt_case() -> PPTCase:
    return get_container().get(PPTCase)

router = APIRouter(prefix="/api/ppt_case", tags=["PPT_CASE"])

@router.post("/chat")
async def chat(ppt_vo: PPTVo, ppt_service: PPTCase = Depends(ppt_case)):

    event_id = await ppt_service.generate(
        generator_id=ppt_vo.generator_id,
        query=ppt_vo.query,
        conversation_id=ppt_vo.conversation_id,
        mcp_name_list=ppt_vo.mcp_name_list,
        task_confirm=ppt_vo.task_confirm
    )

    return BaseResponse.from_success(data=event_id)