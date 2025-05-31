from common.utils.markdown_util import read
from adapter.web.vo.base_response import BaseResponse
from fastapi import APIRouter, BackgroundTasks, Depends
from application.port.outbound.cache_port import CachePort
from common.core.container.container import get_container
from application.port.inbound.test_case import TestCase
from adapter.web.vo.test_vo import CachaVo
from application.port.outbound.event_port import EventPort
from application.domain.events.event import Event, EventType, EventSubType
from common.core.connection_manager import manager
from common.utils.common_utils import SINGLETON_WEBSOCKET_CLIENT_ID
import threading
from autogen_agentchat.teams._group_chat._base_group_chat_manager import (
    BaseGroupChatManager,
)

router = APIRouter(prefix="/api/test", tags=["TEST"])

def cache_port() -> CachePort:
    return get_container().get(CachePort)

def test_case() -> TestCase:
    return get_container().get(TestCase)

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

@router.get("/test123")
async def test_123() -> BaseResponse:
    event = Event.from_init(
        event_type=EventType.AGENT,
        event_sub_type=EventSubType.AGENT_CALL,
        data={
            "agent_id":"4877f996-2fb5-400d-9b26-245a824e325f",
            "conversation_id":"1"
        }
    )
    EventPort.get_event_port().emit_event(event=event)
    return BaseResponse.from_success(data=None)