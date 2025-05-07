from fastapi import APIRouter, Depends, BackgroundTasks
from sse_starlette.sse import EventSourceResponse
from common.core.logger import get_logger
from common.core.container.container import get_container
from application.port.inbound.agent_generators_case import AgentGeneratorsCase
from adapter.web.vo.default_agent_vo import DefaultAgentVo
import asyncio
logger = get_logger(__name__)

def get_agent_generators_case() -> AgentGeneratorsCase:
    return get_container().get(AgentGeneratorsCase)

router = APIRouter(prefix="/api/agent/chat", tags=["AgentChat"])



@router.post("/default_chat")
async def default_chat(agent_vo: DefaultAgentVo, background_tasks: BackgroundTasks, agent_generators_case: AgentGeneratorsCase = Depends(get_agent_generators_case)):
    # 定义一个异步生成器适配器，将异步生成器转化为可以迭代的流
    async def event_generator():
        async for chunk in agent_generators_case.generate(
                firm=agent_vo.firm,
                model=agent_vo.model,
                system=agent_vo.system,
                query=agent_vo.query,
                mcp_name_list=agent_vo.mcp_name_list
        ):
            yield chunk  # 逐个yield异步生成器的内容

    return EventSourceResponse(event_generator(), media_type="text/event-stream", ping=60)