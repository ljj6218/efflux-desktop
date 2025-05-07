from abc import ABC, abstractmethod
from typing import AsyncGenerator, List
from application.domain.generators.chat_chunk.chunk import ChatStreamingChunk

class AgentGeneratorsCase(ABC):

    @abstractmethod
    async def generate(
            self,
            firm: str,
            model: str,
            system: str,
            query: str,
            mcp_name_list: List[str]
    ) -> AsyncGenerator[ChatStreamingChunk, None]:
        """
        默认agent生成（流式）
        :param firm: 模型厂商
        :param model: 模型名
        :param system: 系统提示词
        :param query: 当前问题
        :param mcp_name_list: mcp server 名字集合
        :return: 流式chunk
        """
        pass