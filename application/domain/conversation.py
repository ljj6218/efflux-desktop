from datetime import datetime

from common.utils.common_utils import create_uuid
from common.utils.time_utils import create_from_second_now, create_from_timestamp, create_from_timestamp_to_int
from pydantic import BaseModel
from typing import Optional, List, Any, Literal
from application.domain.generators.chat_chunk.chunk import ChatCompletionMessageToolCall, ChatStreamingChunk, ChatCompletionMessageUserConfirm

class DialogSegment(BaseModel):
    """对话片段"""

    # 对话ID
    id: Optional[str] = None
    # 会话ID
    conversation_id: Optional[str] = None
    # 模型
    model: Optional[str] = None
    # 内容
    content: Optional[str] = None
    # 思考
    reasoning_content: Optional[str] = None
    finish_reason: Optional[str] = None
    # 类型
    role: Optional[str] = None
    # 工具调用集合
    tool_calls: Optional[List[ChatCompletionMessageToolCall]] = None
    # 用户确认
    user_confirm: Optional[ChatCompletionMessageUserConfirm] = None
    # 创建时间
    created: Optional[datetime] = None

    def __init__(self, /, conversation_id: str, **data: Any):
        super().__init__(**data)
        self.id = create_uuid()
        self.conversation_id = conversation_id

    def make_user_message(self, content: str):
        self.role = "user"
        self.content = content
        self.finish_reason = "stop"
        self.created = create_from_second_now()

    def make_assistant_message(self, content: str, reasoning_content: Optional[str], model: str, timestamp: int):
        self.role = "assistant"
        self.content = content
        self.reasoning_content = reasoning_content
        self.model = model
        self.finish_reason = "stop"
        self.created = create_from_timestamp(timestamp)

    def make_tool_calls(self, model: str, timestamp: int, tool_calls: List[ChatCompletionMessageToolCall]):
        self.role = "assistant"
        self.finish_reason = "tool_calls"
        self.created = create_from_timestamp(timestamp)
        self.model = model
        self.tool_calls = tool_calls

    def make_user_confirm(self, user_confirm_id: str, message: str, confirm_type: Literal["yes_or_no", "input", "select"] | None):
        self.role = "assistant"
        self.finish_reason = "user_confirm"
        self.user_confirm = ChatCompletionMessageUserConfirm(id=user_confirm_id, message=message, type=confirm_type)
        self.created = create_from_second_now()

    # 自定义处理模型转化为字典的方法
    def model_dump(self, **kwargs):
        # 使用 super() 获取字典格式
        data = super().model_dump()
        # 转换 datetime 字段为字符串（ISO 格式）
        data['created'] = self.created.isoformat() if self.created else None
        return data

    @classmethod
    def model_validate(cls, obj, **kwargs):
        # 确保将创建的字符串转换为 datetime 对象
        if 'created' in obj and isinstance(obj['created'], str):
            obj['created'] = datetime.fromisoformat(obj['created'])
        return super().model_validate(obj)

class Conversation(BaseModel):
    """chat bot 会话对象"""

    # 会话ID
    id: Optional[str] = None
    # 会话主题
    theme: Optional[str] = None
    # 创建时间
    created: Optional[datetime] = None
    # 当前会话最大长度
    max_length: int = 50
    # 对话片段集合
    dialog_segment_list: Optional[List[DialogSegment]] = None

    def init(self):
        self.id = create_uuid()
        self.created = create_from_second_now()
        self.dialog_segment_list = []

    def convert_sort_memory(self) -> List[ChatStreamingChunk]:
        rs_list: List[ChatStreamingChunk] = []
        for dialog_segment in self.dialog_segment_list:
            chat_streaming_chunk = ChatStreamingChunk(id=dialog_segment.id,
                                                      model=dialog_segment.model,
                                                      content=dialog_segment.content,
                                                      reasoning_content=dialog_segment.reasoning_content,
                                                      role=dialog_segment.role,
                                                      finish_reason=dialog_segment.finish_reason,
                                                      tool_calls=dialog_segment.tool_calls,
                                                      user_confirm=dialog_segment.user_confirm,
                                                      created=create_from_timestamp_to_int(dialog_segment.created)
                                                      )
            rs_list.append(chat_streaming_chunk)
        return rs_list

    # 自定义处理模型转化为字典的方法
    def model_dump(self, **kwargs):
        # 使用 super() 获取字典格式
        data = super().model_dump()
        # 转换 datetime 字段为字符串（ISO 格式）
        data['created'] = self.created.isoformat() if self.created else None
        return data

    @classmethod
    def model_validate(cls, obj, **kwargs):
        # 确保将创建的字符串转换为 datetime 对象
        if 'created' in obj and isinstance(obj['created'], str):
            obj['created'] = datetime.fromisoformat(obj['created'])
        return super().model_validate(obj)