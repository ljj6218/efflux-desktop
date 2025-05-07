from abc import ABC, abstractmethod
from common.utils.auth import Secret
from application.domain.generators.chat_chunk.chunk import ChatChunk, ChatStreamingChunk
from application.domain.generators.tools import Tool
from application.domain.generators.chat_completion.chat_completion_message_param import ChatCompletionMessageParam
from typing import Iterable, AsyncGenerator

class GeneratorsPort(ABC):

    @abstractmethod
    def generate(
        self,
        model: str = None,
        api_secret: Secret = None,
        firm: str = None,
        messages: Iterable[ChatCompletionMessageParam] = None,
        tools: Iterable[Tool] = None
    ) -> ChatChunk:
        """
        同步大模型消息接口
        :param messages: 消息集合
        :param tools: 工具数组
        :param model: 调用模型名称
        :param api_secret: 模型api_key
        :param firm: 模型厂商
        :return:
        """
        pass

    @abstractmethod
    async def generate_stream(
        self,
        model: str = None,
        api_secret: Secret = None,
        firm: str = None,
        messages: Iterable[ChatCompletionMessageParam] = None,
        tools:Iterable[Tool] = None
    ) -> AsyncGenerator[ChatStreamingChunk, None]:
        """
        流式大模型消息接口
        :param messages: 消息集合
        :param tools: 工具数组
        :param model: 调用模型名称
        :param api_secret: 模型api_key
        :param firm: 模型厂商
        :return:
        """
        pass