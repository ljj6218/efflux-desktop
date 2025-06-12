from fastapi import APIRouter, Depends
from common.core.logger import get_logger
from common.core.container.container import get_container
from application.port.inbound.generators_case import GeneratorsCase
from adapter.web.vo.generators_vo import GeneratorsVo
from adapter.web.vo.base_response import BaseResponse
logger = get_logger(__name__)

def generators_case() -> GeneratorsCase:
    return get_container().get(GeneratorsCase)

router = APIRouter(prefix="/api/generators", tags=["GENERATORS_CASE"])

@router.post("/chat")
async def chat(generators_vo: GeneratorsVo, generators_service: GeneratorsCase = Depends(generators_case)):

    conversation_id, uuid = await generators_service.generate_stream(
        generator_id=generators_vo.generator_id,
        client_id=generators_vo.client_id,
        query=generators_vo.query,
        system=generators_vo.system,
        conversation_id=generators_vo.conversation_id,
        mcp_name_list=generators_vo.mcp_name_list,
        tools_group_name_list=generators_vo.tools_group_name_list,
        task_confirm=generators_vo.task_confirm
    )

    return BaseResponse.from_success(data={"conversation_id": conversation_id, "dialog_segment_id": uuid})

@router.put("/stop")
async def stop(conversation_id: str, client_id: str, generators_service: GeneratorsCase = Depends(generators_case)):
    return BaseResponse.from_success(data={"conversation_id": await generators_service.stop_generate(client_id=client_id, conversation_id=conversation_id)})


@router.post("/chat_test")
async def chat_test(generators_vo: GeneratorsVo, generators_service: GeneratorsCase = Depends(generators_case)):

    event_id = await generators_service.generate_test(
        generator_id=generators_vo.generator_id,
        query=generators_vo.query,
        conversation_id=generators_vo.conversation_id,
        mcp_name_list=generators_vo.mcp_name_list,
        tools_group_name_list=generators_vo.tools_group_name_list,
        task_confirm=generators_vo.task_confirm
    )

    return BaseResponse.from_success(data=event_id)
