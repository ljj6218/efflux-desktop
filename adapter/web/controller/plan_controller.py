from fastapi import APIRouter, Depends
from common.core.logger import get_logger
from common.core.container.container import get_container
from application.port.inbound.plan_case import PlanCase
from adapter.web.vo.base_response import BaseResponse
from adapter.web.vo.plan_vo import PlanVO
logger = get_logger(__name__)

router = APIRouter(prefix="/api/plan", tags=["Plan"])

def plan_case() -> PlanCase:
    return get_container().get(PlanCase)

@router.get("")
async def get_plan(conversation_id: str, plan_service: PlanCase = Depends(plan_case)):
    return BaseResponse.from_success(data= await plan_service.load(conversation_id=conversation_id))

@router.put("")
async def update_plan(plan_vo: PlanVO, plan_service: PlanCase = Depends(plan_case)):
    conversation_id =  await plan_service.update(
        plan=plan_vo.plan,
        client_id=plan_vo.client_id,
        generator_id=plan_vo.generator_id,
        agent_instance_id=plan_vo.agent_instance_id,
        is_update=plan_vo.is_update,
        is_replan=plan_vo.is_replan,
        content=plan_vo.content
    )
    return BaseResponse.from_success(data={"conversation_id": conversation_id})