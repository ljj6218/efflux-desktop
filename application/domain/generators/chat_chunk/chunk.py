from pydantic import BaseModel
import time
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

class ChatStreamingChunk(BaseModel):
    """流式块"""
    id: str
    model: Optional[str] = None
    created: Optional[int] = None
    usage: Optional[CompletionUsage] = None
    """Choice"""
    finish_reason: Optional[Literal["stop", "length", "tool_calls", "content_filter", "function_call"]]
    """ChoiceDelta"""
    content: Optional[str] = None
    reasoning_content:  Optional[str] = None
    role: Optional[Literal["developer", "system", "user", "assistant", "tool", "error"]]
    tool_calls: Optional[List[ChatCompletionMessageToolCall]] = None

    @classmethod
    def from_exception(cls, exception: CommonException) -> "ChatStreamingChunk":
        return ChatStreamingChunk(id="1", model=None, created=int(time.time()), usage=None, finish_reason="stop",
                           content=str(exception), reasoning_content=None, role='error', tool_calls=[])

class ChatChunk(BaseModel):
    """普通块"""
    id: str
    model: Optional[str] = None
    created: Optional[int] = None
    usage: Optional[CompletionUsage] = None
    """Choice"""
    finish_reason: Literal["stop", "length", "tool_calls", "content_filter", "function_call"] = None
    """Message"""
    content: Optional[str] = None
    reasoning_content:  Optional[str] = None
    role: Literal["assistant"]
    tool_calls: Optional[List[ChatCompletionMessageToolCall]] = None

