from abc import ABC, abstractmethod
from typing import List, Optional
from application.domain.conversation import DialogSegmentContent

class TeamsCase(ABC):

    @abstractmethod
    async def do_work(
        self,
        generator_id: str,
        content: Optional[str | List[DialogSegmentContent]],
        conversation_id: str,
    )-> tuple[str, str]:
        """
        开始一个teams工作
        :param generator_id: 生成器ID
        :param content: 用户输入
        :param conversation_id: 会话ID
        :return:
        """