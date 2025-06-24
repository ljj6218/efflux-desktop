from pydantic import BaseModel

from application.domain.events.event import Event, EventGroup, EventType, EventSubType, EventSource
from common.utils.common_utils import create_uuid
from common.utils.time_utils import create_from_second_now_to_int
from typing import Optional, List, Union, Iterable, Dict, Any
from typing_extensions import Literal, Required

class CompletionUsage(BaseModel):
    """块内的模型用量"""
    completion_tokens: int
    prompt_tokens: int
    total_tokens: int

class ChatCompletionMessageToolCall(BaseModel):
    """块内的tool结构"""
    id: Optional[str]
    mcp_server_name: Optional[str] = None
    group_name: Optional[str] = None
    name: Optional[str]
    description: Optional[str] = None
    arguments: Optional[str]

class ImageURL(BaseModel):
    url: str
    # """Either a URL of the image or the base64 encoded image data."""
    #
    # detail: Literal["auto", "low", "high"]

class ChatCompletionContentPartParam(BaseModel):
    type: Literal["image_url", "text"]
    text: Optional[str] = None
    image_url: Optional[ImageURL] = None

class ChatCompletionMessageUserConfirm(BaseModel):
    """块内用户确认结构"""
    id: Optional[str] = None
    message: Optional[str] = None
    type: Optional[Literal["yes_or_no", "input", "select"]] = None
    user_confirmation_result: Optional[bool | str | List[str]] = None

class ChatStreamingChunk(BaseModel):
    """流式块"""
    id: str
    conversation_id: Optional[str] = None
    agent_id: Optional[str] = None
    model: Optional[str] = None
    created: Optional[int] = None
    usage: Optional[CompletionUsage] = None
    """Choice"""
    finish_reason: Optional[Literal["stop", "length", "tool_calls", "content_filter", "function_call", "user_confirm"]] = None
    """ChoiceDelta"""
    content: Optional[Union[str, Iterable[ChatCompletionContentPartParam]]] = None
    reasoning_content:  Optional[str] = None
    role: Optional[Literal["developer", "system", "user", "assistant", "tool", "error"]]
    tool_calls: Optional[List[ChatCompletionMessageToolCall]] = None
    tool_call_id: Optional[str] = None
    user_confirm: Optional[ChatCompletionMessageUserConfirm] = None

    @classmethod
    def from_user(cls, message: Union[str, Iterable[ChatCompletionContentPartParam]]) -> "ChatStreamingChunk":
        return cls(id=create_uuid(), model=None, created=create_from_second_now_to_int(), usage=None, finish_reason="stop",
                                  content=message, reasoning_content=None, role='user', tool_calls=[])
    @classmethod
    def from_system(cls, message: str) -> "ChatStreamingChunk":
        return cls(id=create_uuid(), model=None, created=create_from_second_now_to_int(), usage=None, finish_reason="stop",
                                  content=message, reasoning_content=None, role='system', tool_calls=[])
    @classmethod
    def from_assistant(cls, id: str, model: str, created: int, content: str, reasoning_content: str,
                       role: Optional[Literal["developer", "system", "user", "assistant", "tool", "error"]],
                       finish_reason: Optional[Literal["stop", "length", "tool_calls", "content_filter", "function_call", "user_confirm"]] = None,
                       tool_calls: Optional[List[ChatCompletionMessageToolCall]] = None) -> "ChatStreamingChunk":
        return cls(id=id, model=model, created=created, finish_reason=finish_reason,
                                  content=content, reasoning_content= reasoning_content, role=role, tool_calls=tool_calls)
    @classmethod
    def from_tool_calls_result(cls, content: str, tool_call_id: str, tool_calls: List[ChatCompletionMessageToolCall]) -> "ChatStreamingChunk":
        return cls(id=create_uuid(), model=None, created=create_from_second_now_to_int(), usage=None, finish_reason="stop",
                                  content=content, tool_call_id=tool_call_id, reasoning_content=None, role='tool', tool_calls=tool_calls)
    @classmethod
    def from_tool_calls(cls, tool_calls: List[ChatCompletionMessageToolCall]) -> "ChatStreamingChunk":
        return cls(id=create_uuid(), model=None, created=create_from_second_now_to_int(), usage=None,
                                  finish_reason="tool_calls", content="", tool_call_id=None, reasoning_content=None, role='assistant', tool_calls=tool_calls)

    def to_assistant_message_event(self, id: str, client_id: str, conversation_id: str, dialog_segment_id: str, generator_id: str, event_group: EventGroup, payload: Dict[str, Any]) -> Event:
        return Event.from_init(
            client_id=client_id,
            event_type=EventType.ASSISTANT_MESSAGE,
            event_sub_type=EventSubType.MESSAGE,
            group=event_group,
            payload=payload,
            source=EventSource.LLM_HANDLER,
            data={
                "id": id,
                "conversation_id": conversation_id,
                "dialog_segment_id": dialog_segment_id,
                "generator_id": generator_id,
                "model": self.model,
                "content": self.content,
                "reasoning_content": self.reasoning_content,
                "created": self.created,
                "finish_reason": self.finish_reason,
            }
        )

    def to_tool_calls_message_event(self, id: str, client_id: str, conversation_id: str, dialog_segment_id: str, generator_id: str, payload: Dict[str, Any], event_group: Optional[EventGroup] = None) -> Event:
        tool_call_list = []
        for tool_call in self.tool_calls:
            tool_call_list.append(
                {
                    "id": tool_call.id,
                    "name": tool_call.name,
                    "description": tool_call.description,
                    "mcp_server_name": tool_call.mcp_server_name,
                    "group_name": tool_call.group_name,
                    "arguments": tool_call.arguments,
                }
            )
        return Event.from_init(
            client_id=client_id,
            event_type=EventType.TOOL,
            event_sub_type=EventSubType.TOOL_CALL,
            group=event_group,
            payload=payload,
            source=EventSource.LLM_HANDLER,
            data={
                "id": id,
                "conversation_id": conversation_id,
                "dialog_segment_id": dialog_segment_id,
                "generator_id": generator_id,
                "model": self.model,
                "created": self.created,
                "tool_calls": tool_call_list,
            }
        )

