from fastapi import APIRouter, Depends, BackgroundTasks, Query
from sse_starlette.sse import EventSourceResponse
from common.core.logger import get_logger
from common.core.container.container import get_container
from application.port.inbound.agent_generators_case import AgentGeneratorsCase
from adapter.web.vo.default_agent_vo import DefaultAgentVo
from typing import Optional, List
import asyncio
import json
logger = get_logger(__name__)

def get_agent_generators_case() -> AgentGeneratorsCase:
    return get_container().get(AgentGeneratorsCase)

router = APIRouter(prefix="/api/agent/chat", tags=["AGENT_CHAT"])



@router.post("/default_chat")
async def default_chat(agent_vo: DefaultAgentVo, background_tasks: BackgroundTasks, agent_generators_case: AgentGeneratorsCase = Depends(get_agent_generators_case)):

    return await agent_generators_case.generate(
        generator_id=agent_vo.generator_id,
        system=agent_vo.system,
        query=agent_vo.query,
        conversation_id=agent_vo.conversation_id,
        mcp_name_list=agent_vo.mcp_name_list,
        user_confirm=agent_vo.user_confirm
    )

@router.post("/default_chat_stream")
async def default_chat_stream(agent_vo: DefaultAgentVo, background_tasks: BackgroundTasks, agent_generators_case: AgentGeneratorsCase = Depends(get_agent_generators_case)) -> EventSourceResponse:
    # 定义一个异步生成器适配器，将异步生成器转化为可以迭代的流
    async def event_generator():
        async for chunk in agent_generators_case.generate_stream(
                generator_id=agent_vo.generator_id,
                system=agent_vo.system,
                query=agent_vo.query,
                conversation_id=agent_vo.conversation_id,
                mcp_name_list=agent_vo.mcp_name_list,
                user_confirm=agent_vo.user_confirm,
        ):
            yield chunk  # 逐个yield异步生成器的内容

    return EventSourceResponse(event_generator(), media_type="text/event-stream", ping=5)

@router.get("/default_chat_stream")
async def default_chat_stream(
        generator_id: str = Query(...),
        query: str = Query(...),
        system: Optional[str] = Query(None),
        conversation_id: Optional[str] = Query(None),
        mcp_name_list: Optional[List[str]] = Query(None),
        user_confirm: Optional[str] = Query(None),
        agent_generators_case: AgentGeneratorsCase = Depends(get_agent_generators_case)) -> EventSourceResponse:
    # 将传递的 user_confirm 字符串解析为字典
    parsed_user_confirm= json.loads(user_confirm) if user_confirm else {}

    # 创建 DefaultAgentVo 对象
    agent_vo = DefaultAgentVo(
        generator_id=generator_id,
        query=query,
        system=system,
        conversation_id=conversation_id,
        mcp_name_list=mcp_name_list,
        user_confirm=parsed_user_confirm  # 解析后的字典
    )

    # 定义一个异步生成器适配器，将异步生成器转化为可以迭代的流
    async def event_generator():
        async for chunk in agent_generators_case.generate_stream(
                generator_id=agent_vo.generator_id,
                system=agent_vo.system,
                query=agent_vo.query,
                conversation_id=agent_vo.conversation_id,
                mcp_name_list=agent_vo.mcp_name_list,
                user_confirm=agent_vo.user_confirm,
        ):
            yield chunk  # 逐个yield异步生成器的内容

    return EventSourceResponse(event_generator(), media_type="text/event-stream", ping=60)