from application.port.outbound.generators_port import GeneratorsPort
from application.domain.generators.chat_completion.chat_completion_message_param import ChatCompletionMessageParam
from application.domain.generators.tools import Tool
from common.utils.auth import Secret
from common.core.container.annotate import component
from typing import Iterable, Dict, AsyncGenerator, Any
from application.domain.generators.chat_chunk.chunk import ChatChunk, ChatStreamingChunk
from common.utils.yaml_util import load_yaml
from adapter.model_sdk.client import ModelClient
from adapter.model_sdk.openai.client import OpenAIClient
import asyncio

@component
class ClientManager(GeneratorsPort):

    def __init__(self, ):
        config: Dict[str, Any] = load_yaml('adapter/model_sdk/setting/openai/model.yaml')

        self.model_map: Dict = load_yaml("adapter/model_sdk/setting/openai/model_position.yaml")
        self.base_url_map: Dict = load_yaml("adapter/model_sdk/setting/openai/model_base_url.yaml")

    def generate(self,
                model: str = None,
                api_secret: Secret = None,
                firm: str = None,
                tools: Iterable[Tool] = None,
                messages: Iterable[ChatCompletionMessageParam] = None
                # generation_kwargs: Optional[Dict[str, Any]] = None,
                # *,
                # tools: Optional[List[Tool]] = None,
                ) -> ChatChunk:
        client: ModelClient = OpenAIClient()
        url = self.base_url_map[firm]
        rs = client.generate(
            model=model,
            api_secret=api_secret,
            base_url=url,
            messages=messages,
            tools=tools
        )
        print(rs)
        return rs

    async def generate_stream(self,
                model: str = None,
                api_secret: Secret = None,
                firm: str = None,
                tools: Iterable[Tool] = None,
                messages: Iterable[ChatCompletionMessageParam] = None
                ) -> AsyncGenerator[ChatStreamingChunk, None]:

        client: ModelClient = OpenAIClient()
        url = self.base_url_map[firm]
        for chunk in client.generate_stream(
            model=model,
            api_secret=api_secret,
            base_url=url,
            messages=messages,
            tools=tools
        ):
            await asyncio.sleep(0.05) # 主动让出事件循环，避免流式响应时候其他接口的pending TODO 真特么丑陋，待优化吧
            yield chunk