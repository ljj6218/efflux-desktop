from pydantic import BaseModel
from common.utils.common_utils import create_uuid
from common.utils.time_utils import create_from_second_now_to_int
from typing import Optional, List
from typing_extensions import Literal
from common.core.errors.common_exception import CommonException

class CompletionUsage(BaseModel):
    """块内的模型用量"""
    completion_tokens: int
    prompt_tokens: int
    total_tokens: int

class ChatCompletionMessageToolCall(BaseModel):
    """块内的tool结构"""
    id: Optional[str]
    mcp_server_name: Optional[str] = None
    name: Optional[str]
    arguments: Optional[str]

class ChatCompletionMessageUserConfirm(BaseModel):
    """块内用户确认结构"""
    id: Optional[str] = None
    message: Optional[str] = None
    type: Optional[Literal["yes_or_no", "input", "select"]] = None
    user_confirmation_result: Optional[bool | str | List[str]] = None

    @classmethod
    def from_yes_or_no(cls, message: str) -> "ChatCompletionMessageUserConfirm":
        return ChatCompletionMessageUserConfirm(id=create_uuid(), message=message, type="yes_or_no")
    @classmethod
    def from_yes_or_no_result(cls, confirm_id: str, user_confirmation_result: bool) -> "ChatCompletionMessageUserConfirm":
        return ChatCompletionMessageUserConfirm(id=confirm_id, type="yes_or_no", user_confirmation_result=user_confirmation_result)

class ChatStreamingChunk(BaseModel):
    """流式块"""
    id: str
    conversation_id: Optional[str] = None
    model: Optional[str] = None
    created: Optional[int] = None
    usage: Optional[CompletionUsage] = None
    """Choice"""
    finish_reason: Optional[Literal["stop", "length", "tool_calls", "content_filter", "function_call", "user_confirm"]] = None
    """ChoiceDelta"""
    content: Optional[str] = None
    reasoning_content:  Optional[str] = None
    role: Optional[Literal["developer", "system", "user", "assistant", "tool", "error"]]
    tool_calls: Optional[List[ChatCompletionMessageToolCall]] = None
    tool_call_id: Optional[str] = None
    user_confirm: Optional[ChatCompletionMessageUserConfirm] = None

    @classmethod
    def from_exception(cls, exception: CommonException) -> "ChatStreamingChunk":
        return ChatStreamingChunk(id=create_uuid(), model=None, created=create_from_second_now_to_int(), usage=None, finish_reason="stop",
                           content=str(exception), reasoning_content=None, role='error', tool_calls=[])
    @classmethod
    def from_user(cls, message: str) -> "ChatStreamingChunk":
        return ChatStreamingChunk(id=create_uuid(), model=None, created=create_from_second_now_to_int(), usage=None, finish_reason="stop",
                                  content=message, reasoning_content=None, role='user', tool_calls=[])
    @classmethod
    def from_system(cls, message: str) -> "ChatStreamingChunk":
        return ChatStreamingChunk(id=create_uuid(), model=None, created=create_from_second_now_to_int(), usage=None, finish_reason="stop",
                                  content=message, reasoning_content=None, role='system', tool_calls=[])
    @classmethod
    def from_tool_calls_result(cls, content: str, tool_call_id: str) -> "ChatStreamingChunk":
        return ChatStreamingChunk(id=create_uuid(), model=None, created=create_from_second_now_to_int(), usage=None, finish_reason="stop",
                                  content=content, tool_call_id=tool_call_id, reasoning_content=None, role='tool', tool_calls=[])
    @classmethod
    def from_user_confirm(cls, message: str, model: str) -> "ChatStreamingChunk":
        return ChatStreamingChunk(id=create_uuid(), model=model, created=create_from_second_now_to_int(), usage=None, finish_reason="user_confirm",
                                  content=None, reasoning_content=None, role='assistant', tool_calls=[], user_confirm=ChatCompletionMessageUserConfirm.from_yes_or_no(message))
    @classmethod
    def from_user_confirm_result(cls, confirm_id: str, user_confirmation_result: bool) -> "ChatStreamingChunk":
        return ChatStreamingChunk(id=create_uuid(), model=None, created=create_from_second_now_to_int(), usage=None, finish_reason="user_confirm",
                                  content=None, reasoning_content=None, role='user', tool_calls=[], user_confirm=ChatCompletionMessageUserConfirm.from_yes_or_no_result(confirm_id=confirm_id, user_confirmation_result=user_confirmation_result))


class ChatChunk(BaseModel):
    """普通块"""
    id: str
    model: Optional[str] = None
    created: Optional[int] = None
    usage: Optional[CompletionUsage] = None
    """Choice"""
    finish_reason: Optional[Literal["stop", "length", "tool_calls", "content_filter", "function_call"]] = None
    """Message"""
    content: Optional[str] = None
    reasoning_content:  Optional[str] = None
    role: Literal["assistant"]
    tool_calls: Optional[List[ChatCompletionMessageToolCall]] = None

