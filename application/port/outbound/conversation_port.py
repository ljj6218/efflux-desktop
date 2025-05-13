from abc import ABC, abstractmethod
from application.domain.conversation import Conversation, DialogSegment
from typing import List, Coroutine, Any

class ConversationPort(ABC):

    @abstractmethod
    async def conversation_save(self, conversation: Conversation) -> Conversation:
        """保存会话"""
        pass

    @abstractmethod
    async def conversation_add(self, dialog_segment: DialogSegment) -> DialogSegment:
        """增加对话片段"""
        pass

    @abstractmethod
    async def dialog_segment_remove(self, dialog_segment: DialogSegment) -> DialogSegment:
        """删除对话片段"""
        pass

    @abstractmethod
    async def conversation_load(self, conversation_id: str) -> Conversation:
        """获取会话"""
        pass

    @abstractmethod
    async def conversation_load_list(self, conversation_id: str) -> List[Conversation]:
        """获取会话列表"""
        pass

