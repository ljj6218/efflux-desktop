from enum import Enum
from pydantic import BaseModel
from common.utils.common_utils import create_uuid
from common.utils.time_utils import create_from_second_now_to_int
from typing import Any, Optional, List, Literal
from application.domain.generators.chat_chunk.chunk import ChatStreamingChunk

class EventType(Enum):
    USER_MESSAGE = "USER_MESSAGE" # 用户发送消息
    ASSISTANT_MESSAGE = "ASSISTANT_MESSAGE" # AI返回消息
    USER_CONFIRM = "USER_CONFIRM"
    TOOL = "TOOL"

class MessageEventDataType(Enum):
    # message
    MESSAGE = "MESSAGE"
    ASSISTANT_THINKING = "ASSISTANT_THINKING" # 思考
    TOOL_CALL = "TOOL_CALL" # 工具调用
    LLM_USAGE = "LLM_USAGE" # 用量
    ERROR = "ERROR" # 错误

    # tool
    TOOL_CALL_RESULT = "TOOL_CALL_RESULT"  # 工具调用结果

    # user_confirm
    TOOL_CALL_CONFiRM = "TOOL_CALL_CONFiRM" # 工具调用确认
    TASK_RESULT_CONFiRM = "TASK_RESULT_CONFiRM" # 任务执行结果确认

# class UserMessageEventData(BaseModel):
#     """二级消息体-用户消息"""
#     generator_id: str # 模型id
#     mcp_name_list: Optional[List[str]] = None # mcp_server_name 集合
#
#     @classmethod
#     def from_message(cls, generator_id: str, mcp_name_list: Optional[List[str]] = None) -> "UserMessageEventData":
#         return cls(generator_id=generator_id, mcp_name_list=mcp_name_list)

class AssistantMessageEventData(BaseModel):
    """二级消息体-AI消息"""
    model: str
    reasoning_content: Optional[str] = None
    created: int # 创建时间
    finish_reason: Optional[Literal["stop"]] = None

    @classmethod
    def from_message(cls, model: str, created: int, finish_reason: Optional[Literal["stop"]], reasoning_content: Optional[str]) -> "AssistantMessageEventData":
        return cls(model=model, created=created, reasoning_content=reasoning_content, finish_reason=finish_reason)

    @classmethod
    def from_error(cls) -> "AssistantMessageEventData":
        return cls(model="-", reasoning_content="-", finish_reason="stop", created=create_from_second_now_to_int())

class AssistantUsageEventData(BaseModel):
    """二级消息体-TOKEN用量"""
    completion_tokens: int
    prompt_tokens: int
    total_tokens: int
    model: str
    created: int  # 创建时间
    finish_reason: Optional[Literal["stop"]] = None

    @classmethod
    def from_init(cls, completion_tokens: int, prompt_tokens: int, total_tokens: int, model: str, created: int, finish_reason: Optional[Literal["stop"]] = None) -> "AssistantUsageEventData":
        return cls(completion_tokens=completion_tokens, prompt_tokens=prompt_tokens, total_tokens=total_tokens, model=model, created=created, finish_reason=finish_reason)

class ToolCalls(BaseModel):
    """二级消息体-工具调用"""
    id: str
    mcp_server_name: Optional[str] = None
    group_name: Optional[str] = None
    name: str
    description: Optional[str] = None
    arguments: str
    result: Optional[List[str]] = None

    @classmethod
    def from_init(cls, id: str, name: str, arguments: str, mcp_server_name: Optional[str] = None, group_name: Optional[str] = None, description: Optional[str] = None) -> "ToolCalls":
        return cls(id=id, mcp_server_name=mcp_server_name, group_name=group_name, name=name, arguments=arguments, description=description)

class ToolCallsEventData(BaseModel):
    """一级消息体-TOOLS调用"""
    id: str
    model: str
    generator_id: str
    mcp_name_list: Optional[List[str]] = None  # mcp_server_name 集合
    group_name_list: Optional[List[str]] = None # 本地工具组名字集合
    created: int
    conversation_id: Optional[str] = None  # 会话id
    tool_calls: List[ToolCalls]
    type: MessageEventDataType

    @classmethod
    def from_tool_calls(cls, id: str, model: str, conversation_id: str, generator_id: str, tool_calls: List[ToolCalls], created: int, mcp_name_list: Optional[List[str]] = None, group_name_list: Optional[List[str]] = None) -> "ToolCallsEventData":
        return cls(id=id, model=model, conversation_id=conversation_id, generator_id=generator_id, mcp_name_list=mcp_name_list, tool_calls=tool_calls, created=created, type=MessageEventDataType.TOOL_CALL)

    @classmethod
    def from_tool_calls_result(cls, id: str, model: str, conversation_id: str, generator_id: str, mcp_name_list: Optional[List[str]] , tool_calls: List[ToolCalls], created: int) -> "ToolCallsEventData":
        return cls(id=id, model=model, conversation_id=conversation_id, generator_id=generator_id, mcp_name_list=mcp_name_list, tool_calls=tool_calls, created=created, type=MessageEventDataType.TOOL_CALL_RESULT)

class MessageEventData(BaseModel):
    """一级消息体"""
    id: str
    role: Optional[Literal["user", "assistant"]] = None
    generator_id: str  # 模型id
    mcp_name_list: Optional[List[str]] = None  # mcp_server_name 集合
    group_name_list: Optional[List[str]] = None # 本地工具组名集合
    content: Optional[str] = None # 内容
    conversation_id: Optional[str] = None # 会话id
    type: MessageEventDataType
    sub_data: Optional[Any] = None

    @classmethod
    def from_init(cls, id: str, role: Optional[Literal["user", "assistant"]], content: str, type: MessageEventDataType, generator_id: str ,
                  conversation_id: Optional[str] = None, mcp_name_list: Optional[List[str]] = None, sub_data: Optional[Any] = None) -> "MessageEventData":
        return cls(id=id, role=role, content=content, conversation_id=conversation_id, generator_id=generator_id, type=type, mcp_name_list=mcp_name_list, sub_data=sub_data)

    @classmethod
    def from_user_message(cls, content: str, generator_id: str, conversation_id: Optional[str] = None, mcp_name_list: Optional[List[str]] = None) -> "MessageEventData":
        return MessageEventData.from_init(id=create_uuid(), role="user", content=content, conversation_id=conversation_id,
                                          type=MessageEventDataType.MESSAGE, generator_id=generator_id, mcp_name_list=mcp_name_list)

    @classmethod
    def from_assistant_message(cls, id: str, conversation_id: str, model: str, content: str, generator_id: str,  created: int, reasoning_content: Optional[str], finish_reason: Optional[Literal["stop"]] = None, mcp_name_list: Optional[List[str]] = None, group_name_list: Optional[List[str]] = None) -> "MessageEventData":
        return MessageEventData.from_init(id=id, role="assistant", content=content, conversation_id=conversation_id, type=MessageEventDataType.MESSAGE, generator_id=generator_id, mcp_name_list=mcp_name_list, group_name_list=group_name_list,
                                          sub_data=AssistantMessageEventData.from_message(model=model, created=created, reasoning_content=reasoning_content, finish_reason=finish_reason))
    @classmethod
    def from_error(cls, content: str) -> "MessageEventData":
        return MessageEventData.from_init(id=create_uuid(), role="assistant", content=content, generator_id="-", type=MessageEventDataType.ERROR, sub_data=AssistantMessageEventData.from_error())

    @classmethod
    def from_usage(cls, id: str, completion_tokens: int, prompt_tokens: int, total_tokens: int, conversation_id: Optional[str], model: str, generator_id: str, created: int, finish_reason: Optional[Literal["stop"]] = None) -> "MessageEventData":
        return MessageEventData.from_init(id=id, role="assistant", content="-", conversation_id=conversation_id, generator_id=generator_id, type=MessageEventDataType.LLM_USAGE, sub_data=AssistantUsageEventData.from_init(completion_tokens=completion_tokens, prompt_tokens=prompt_tokens,total_tokens=total_tokens, model=model, created=created, finish_reason=finish_reason))

class EventGroupStatus(Enum):
    STARTED = "STARTED"
    SENDING = "SENDING"
    ENDED = "ENDED"

class EventGroup(BaseModel):
    id: str # 组ID，标识属于同一组的事件
    status: EventGroupStatus # 组状态：'STARTED'表示组开始，'ENDED'表示组结束，'SENDING'表示组内事件

class Event(BaseModel):
    id: str
    type: EventType
    data: Any
    silent: Optional[bool] = False # 静默事件
    created: int
    # 组事件
    group: Optional[EventGroup] = None

    @classmethod
    def from_init(cls, event_type: EventType, event_data: Any, group_id: Optional[str] = None, group_status: Optional[EventGroupStatus] = EventGroupStatus.SENDING) -> "Event":
        if group_id:
            group = EventGroup(id=group_id, status=group_status)
            return cls(id=create_uuid(), type=event_type, data=event_data, created=create_from_second_now_to_int(), group=group)
        else:
            return cls(id=create_uuid(), type=event_type, data=event_data, created=create_from_second_now_to_int())

    @classmethod
    def from_tool_calls_chunk(cls, id: str, conversation_id: str, generator_id: str, chunk: ChatStreamingChunk, stream_id: str, group_status: EventGroupStatus, mcp_name_list: Optional[List[str]] = None, group_name_list: Optional[List[str]] = None) -> "Event":
        tool_call_list = []
        for tool_call in chunk.tool_calls:
            tool_call_list.append(
                ToolCalls.from_init(id=tool_call.id, mcp_server_name=tool_call.mcp_server_name, name=tool_call.name, group_name=tool_call.group_name,
                                    arguments=tool_call.arguments, description=tool_call.description))
        return Event.from_init(
            event_type=EventType.ASSISTANT_MESSAGE,
            event_data=ToolCallsEventData.from_tool_calls(
                id=id, model=chunk.model, conversation_id=conversation_id, group_name_list=group_name_list,
                generator_id=generator_id, mcp_name_list=mcp_name_list,
                created=chunk.created, tool_calls=tool_call_list),
            group_id=stream_id,
            group_status=group_status
        )

    @classmethod
    def from_message_chunk(cls, id: str, conversation_id: str, generator_id: str, chunk: ChatStreamingChunk, stream_id: str, group_status: EventGroupStatus, mcp_name_list: Optional[List[str]] = None, group_name_list: Optional[List[str]] = None) -> "Event":
        return Event.from_init(
            event_type=EventType.ASSISTANT_MESSAGE,
            group_id=stream_id,
            group_status=group_status,
            event_data=MessageEventData.from_assistant_message(
                id=id, model=chunk.model,
                conversation_id=conversation_id,
                generator_id=generator_id, mcp_name_list=mcp_name_list, group_name_list=group_name_list,
                content=chunk.content, reasoning_content=chunk.reasoning_content,
                created=chunk.created, finish_reason=chunk.finish_reason
            )
        )

    @classmethod
    def from_usage_chunk(cls, id: str, conversation_id: str, generator_id: str, chunk: ChatStreamingChunk, stream_id: str, group_status: EventGroupStatus) -> "Event":
        return Event.from_init(
            event_type=EventType.ASSISTANT_MESSAGE,
            event_data=MessageEventData.from_usage(
                id=id, model=chunk.model, conversation_id=conversation_id, generator_id=generator_id,
                completion_tokens=chunk.usage.completion_tokens,
                prompt_tokens=chunk.usage.prompt_tokens,
                total_tokens=chunk.usage.total_tokens,
                created=chunk.created, finish_reason=chunk.finish_reason
            ),
            group_id=stream_id,
            group_status=group_status
        )