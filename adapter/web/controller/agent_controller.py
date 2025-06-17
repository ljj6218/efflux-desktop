from fastapi import APIRouter, Depends
from common.core.logger import get_logger
from common.core.container.container import get_container
from application.port.inbound.agent_case import AgentCase
from adapter.web.vo.base_response import BaseResponse

from typing import Optional, Dict, Any
logger = get_logger(__name__)

router = APIRouter(prefix="/api/agent", tags=["AGENT"])

def agent_case() -> AgentCase:
    return get_container().get(AgentCase)

@router.post("/save")
async def save_agent(agent_dict: Dict[str, Any], agent_service: AgentCase = Depends(agent_case)) -> BaseResponse:
    return BaseResponse.from_success(data=await agent_service.save(agent_dict))

@router.get("/load")
async def load_agent_by_id(agent_id: str, agent_service: AgentCase = Depends(agent_case)) -> BaseResponse:
    return BaseResponse.from_success(data=await agent_service.load(agent_id))

@router.get("/load_all")
async def load_all(agent_service: AgentCase = Depends(agent_case)) -> BaseResponse:
    return BaseResponse.from_success(data=await agent_service.load_all())

