from abc import ABC, abstractmethod
from application.domain.conversation import Conversation, DialogSegment
from typing import List, Optional

class ConversationCase(ABC):

    @abstractmethod
    async def conversation_load_list(self) -> List[Conversation]:
        """获取会话列表"""

    @abstractmethod
    async def conversation_load(self, conversation_id: str) -> Optional[Conversation]:
        """获取会话"""

    @abstractmethod
    async def conversation_update_theme(self, conversation_id: str, theme: str) -> Conversation:
        """
        更新会话主题
        :param conversation_id: 会话id
        :param theme: 会话主题
        :return:
        """

    @abstractmethod
    async def conversation_remove_dialog_segment(self, conversation_id: str, dialog_segment_id: str) -> str:
        """
        删除对话片段
        :param conversation_id: 会话id
        :param dialog_segment_id: 对话片段id
        :return:
        """

    @abstractmethod
    async def conversation_remove(self, conversation_id_list: List[str]) -> int:
        """
        批量删除会话
        :param conversation_id_list: 会话id集合
        :return:
        """