from datetime import datetime

from common.utils.common_utils import create_uuid
from common.utils.file_util import open_and_base64
from common.utils.time_utils import create_from_second_now, create_from_timestamp, create_from_timestamp_to_int
from application.domain.generators.tools import ToolInstance
from pydantic import BaseModel
from typing import Optional, List, Literal
from application.domain.generators.chat_chunk.chunk import ChatStreamingChunk

class DialogSegmentContent(BaseModel):
    type: Literal["text", "image"]
    content: str

class DialogSegment(BaseModel):
    """对话片段"""

    # 对话ID
    id: str
    # 会话ID
    conversation_id: Optional[str] = None
    # agent id
    agent_id: Optional[str] = None
    # 模型
    model: Optional[str] = None
    # 内容
    content: Optional[str | List[DialogSegmentContent]] = None
    # 思考
    reasoning_content: Optional[str] = None
    finish_reason: Optional[str] = None
    # 类型
    role: Optional[str] = None
    # 工具调用集合
    tool_calls: Optional[List[ToolInstance]] = None
    # 创建时间
    created: Optional[datetime] = None

    @classmethod
    def make_user_message(cls, content: str | List[DialogSegmentContent], conversation_id: str, agent_id: Optional[str] = None, id: Optional[str] = None) -> "DialogSegment":
        return cls(
            id=id if id else create_uuid(),
            conversation_id=conversation_id,
            agent_id=agent_id,
            content=content,
            role="user",
            finish_reason="stop",
            created=create_from_second_now()
        )

    @classmethod
    def make_assistant_message(cls, content: str, conversation_id: str, reasoning_content: Optional[str], model: str, timestamp: int, agent_id: Optional[str] = None, id: Optional[str] = None):
        return cls(
            id=id if id else create_uuid(),
            conversation_id=conversation_id,
            agent_id=agent_id,
            content=content,
            reasoning_content=reasoning_content,
            model=model,
            role="assistant",
            finish_reason="stop",
            created = create_from_timestamp(timestamp)
        )

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
    # 最后对话片段
    last_dialog_segment: Optional[DialogSegment] = None
    # 当前会话最大长度
    max_length: int = 50
    # 对话片段集合
    dialog_segment_list: Optional[List[DialogSegment]] = None

    def init(self):
        self.id = create_uuid()
        self.created = create_from_second_now()
        self.dialog_segment_list = []

    @classmethod
    def from_update_theme(cls, id: str, theme: str):
        return cls(id=id, theme=theme)

    def convert_sort_memory(self) -> List[ChatStreamingChunk]:
        rs_list: List[ChatStreamingChunk] = []
        for i, dialog_segment in enumerate(self.dialog_segment_list):
            if i == len(self.dialog_segment_list) - 1:
                print(f"{dialog_segment} 是最后一个元素")
                chat_streaming_chunk = self._convert_chat_streaming_chunk(dialog_segment)
                rs_list.append(chat_streaming_chunk)
            else:
                if dialog_segment.role == 'user' and dialog_segment.content and isinstance(dialog_segment.content, List):
                    continue
                else:
                    chat_streaming_chunk = self._convert_chat_streaming_chunk(dialog_segment)
                    rs_list.append(chat_streaming_chunk)
        return rs_list

    @staticmethod
    def _convert_chat_streaming_chunk(dialog_segment: DialogSegment) -> ChatStreamingChunk:
        dialog_segment_content_copy = dialog_segment.content
        if dialog_segment.role == 'user' and dialog_segment.content and isinstance(dialog_segment.content, List):
            content_list = []
            for dialog_segment_content_item in dialog_segment.content:
                if dialog_segment_content_item.type == 'text':
                    content_list.append({'type': "text", 'text': dialog_segment_content_item.content})
                if dialog_segment_content_item.type == 'image':
                    base64_image = open_and_base64(dialog_segment_content_item.content)
                    content_list.append({
                    "type": "image_url",
                    "image_url":{
                        "url": f"data:image/jpeg;base64,{base64_image}"
                    }
                })
            dialog_segment_content_copy = content_list
        return ChatStreamingChunk(
            id=dialog_segment.id,
            model=dialog_segment.model,
            content=dialog_segment_content_copy,
            reasoning_content=dialog_segment.reasoning_content,
            role=dialog_segment.role,
            finish_reason=dialog_segment.finish_reason,
            created=create_from_timestamp_to_int(dialog_segment.created)
        )

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