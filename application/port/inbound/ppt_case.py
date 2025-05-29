from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

class PPTCase(ABC):

    @abstractmethod
    async def generate(self,
        generator_id: str,
        query: str,
        conversation_id: str,
        mcp_name_list: List[str],
        task_confirm: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        ppt生成交互
        :param generator_id: 生成模型id
        :param query: 用户消息
        :param conversation_id: 会话id
        :param mcp_name_list: mcp名列表
        :param task_confirm: 任务确认
        :return:
        """

