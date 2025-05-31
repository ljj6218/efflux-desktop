from enum import Enum
from pydantic import BaseModel
from common.utils.common_utils import create_uuid
from common.utils.time_utils import create_from_second_now_to_int
from typing import Dict, Any, Optional, List, Literal

class EventType(Enum):
    USER_MESSAGE = "USER_MESSAGE" # 用户发送消息事件
    ASSISTANT_MESSAGE = "ASSISTANT_MESSAGE" # AI返回事件
    TOOL = "TOOL" # 工具调用事件
    AGENT = "AGENT" # agent事件
    LLM_USAGE = "LLM_USAGE" # Token用量事件
    SYSTEM = "SYSTEM"  # 系统事件

class EventSubType(Enum):
    # message
    MESSAGE = "MESSAGE" # 普通文字消息事件
    ASSISTANT_THINKING = "ASSISTANT_THINKING" # 思考消息事件
    # tool
    TOOL_CALL = "TOOL_CALL" # 工具调用
    TOOL_CALL_RESULT = "TOOL_CALL_RESULT"  # 工具调用结果
    # system
    ERROR = "ERROR" # 错误
    HEARTBEAT = "HEARTBEAT" # 心跳事件
    STOP = "STOP"
    # user_confirm
    TOOL_CALL_CONFiRM = "TOOL_CALL_CONFiRM" # 工具调用确认
    TASK_RESULT_CONFiRM = "TASK_RESULT_CONFiRM" # 任务执行结果确认
    # agent
    AGENT_CALL = "AGENT_CALL"
    LLM_CALL = "LLM_CALL"

    AGENT_CALL_RESULT = "AGENT_CALL_RESULT"
    AGENT_TOOL_CALL = "AGENT_TOOL_CALL"
    AGENT_TOOL_CALL_RESULT = "AGENT_TOOL_CALL_RESULT"

class EventGroupStatus(Enum):
    STARTED = "STARTED"
    SENDING = "SENDING"
    ENDED = "ENDED"
    STOPPED = "STOPPED"

class EventGroup(BaseModel):
    id: str # 组ID，标识属于同一组的事件
    status: EventGroupStatus # 组状态：'STARTED'表示组开始，'ENDED'表示组结束，'SENDING'表示组内事件

class Event(BaseModel):
    id: str
    type: EventType
    sub_type: EventSubType
    data: Dict[str, Any]
    created: int
    silent: Optional[bool] = False # 静默事件
    group: Optional[EventGroup] = None # 组事件

    @classmethod
    def from_init(cls, data:Dict[str, Any], event_type: EventType, event_sub_type: EventSubType, group: Optional[EventGroup] = None, silent: Optional[bool] = False) -> "Event":
        return Event(id=create_uuid(), type=event_type, sub_type=event_sub_type, data=data, group=group, silent=silent, created=create_from_second_now_to_int())

    @classmethod
    def from_stop(cls, data:Dict[str, Any], group: Optional[EventGroup] = None, silent: Optional[bool] = False):
        return Event(id=create_uuid(), type=EventType.SYSTEM, sub_type=EventSubType.STOP, data=data, group=group, silent=silent,
                     created=create_from_second_now_to_int())