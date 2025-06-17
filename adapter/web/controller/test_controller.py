from application.domain.generators.chat_chunk.chunk import ChatStreamingChunk
from application.port.inbound.teams_case import TeamsCase
from common.utils.markdown_util import read
from adapter.web.vo.base_response import BaseResponse
from fastapi import APIRouter, BackgroundTasks, Depends
from application.port.outbound.cache_port import CachePort
from common.core.container.container import get_container
from application.port.inbound.test_case import TestCase
from adapter.web.vo.test_vo import CachaVo, AgentVo, PromptsVo
from application.port.outbound.event_port import EventPort
from application.domain.events.event import Event, EventType, EventSubType
from common.core.connection_manager import manager
from common.utils.common_utils import SINGLETON_WEBSOCKET_CLIENT_ID


import threading



router = APIRouter(prefix="/api/test", tags=["TEST"])

def cache_port() -> CachePort:
    return get_container().get(CachePort)

def test_case() -> TestCase:
    return get_container().get(TestCase)

def team_case() -> TeamsCase:
    return get_container().get(TeamsCase)

# 定义后台任务
def background_task(message: str):
    import time
    time.sleep(5)  # 模拟耗时任务
    print(f"任务完成: {message}")

@router.get("/test")
async def test():
    await manager.send_to(client_id=SINGLETON_WEBSOCKET_CLIENT_ID, message="test")

@router.get("/read_md")
async def load_mcp_server(back: BackgroundTasks) -> BaseResponse:
    print(read("system_prompt.md"))
    threading.Thread(target=background_task, args=("aaaaaa",)).start()
    return BaseResponse.from_success(data=None)

@router.get("/cacha")
async def load_cacha(cacha_name: str, cacha_key: str, cacha: CachePort = Depends(cache_port)) -> BaseResponse:
    # return BaseResponse.from_success(data=get_shared_cache(name=cacha_key))
    return BaseResponse.from_success(data=cacha.get_from_cache(name=cacha_name, key=cacha_key))

@router.post("/cacha")
async def set_cacha(cacha_data: CachaVo, cacha: CachePort = Depends(cache_port)) -> BaseResponse:
    # return BaseResponse.from_success(data=set_shared_cache(cacha_data.cacha_key, cacha_data.cacha_data))
    return BaseResponse.from_success(data=cacha.set_data(name=cacha_data.cacha_name, key=cacha_data.cacha_key, value=cacha_data.cacha_data))

@router.get("/task")
async def test_task(task_service: TestCase = Depends(test_case)) -> BaseResponse:
    return BaseResponse.from_success(data=await task_service.test_task())

@router.get("/task_stop")
async def test_task_stop(task_id:str, task_service: TestCase = Depends(test_case)) -> BaseResponse:
    return BaseResponse.from_success(data=await task_service.test_task_stop(task_id=task_id))

@router.post("/test_agent")
async def test_agent(agent_ve: AgentVo, task_service: TestCase = Depends(test_case)) -> BaseResponse:
    uuid, conversation_id  = await task_service.test_call_agent(query=agent_ve.query, generator_id=agent_ve.generator_id,  conversation_id=agent_ve.conversation_id)
    return BaseResponse.from_success(data={"uuid": uuid, "conversation_id": conversation_id})

@router.post("/team_test")
async def team_test(agent_ve: AgentVo, team_service: TeamsCase = Depends(team_case)) -> BaseResponse:
    await team_service.on_message(client_id=agent_ve.client_id, content=agent_ve.query, generator_id=agent_ve.generator_id, conversation_id=agent_ve.conversation_id)
    return BaseResponse.from_success(data=None)

@router.post("/test_prompt")
async def test_prompt(prompts_vo: PromptsVo, task_service: TestCase = Depends(test_case)) -> BaseResponse:
    messages = []
    for e in prompts_vo.prompt:
        if e.role == "system":
            messages.append(ChatStreamingChunk.from_system(e.content))
        if e.role == "user":
            messages.append(ChatStreamingChunk.from_user(e.content))
        if e.role == "assistant":
            messages.append(ChatStreamingChunk.from_assistant(e.content))
    return BaseResponse.from_success(data=await task_service.test_prompts(chunks=messages, generator_id=prompts_vo.generator_id))