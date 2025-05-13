from openai import base_url

from application.port.outbound.generators_port import GeneratorsPort
from application.domain.generators.tools import Tool
from application.domain.generators.generator import LLMGenerator
from common.core.container.annotate import component
from typing import Iterable, Dict, AsyncGenerator, Any, List, Optional
from application.domain.generators.chat_chunk.chunk import ChatStreamingChunk
from common.utils.yaml_util import load_yaml
from adapter.model_sdk.client import ModelClient
from adapter.model_sdk.openai.client import OpenAIClient
from common.utils.json_file_util import JSONFileUtil
import asyncio

@component
class ClientManager(GeneratorsPort):

    def __init__(self, ):
        self.config: Dict[str, Any] = load_yaml('adapter/model_sdk/setting/openai/model.yaml')

    def load_generate(self, generate_id: str) -> Optional[LLMGenerator]:
        # 遍历项目内置支持的所有厂商
        for firm in self.config.keys():
            firm_model_config_url = f"adapter/model_sdk/setting/openai/{firm}_model.json"
            firm_model_config = JSONFileUtil(firm_model_config_url)
            # 遍历厂商启用的所有模型
            for model_name in firm_model_config.read().keys():
                firm_model_dict = firm_model_config.read_key(model_name)
                if firm_model_dict['id'] == generate_id:
                    return LLMGenerator.model_validate(firm_model_dict)
        return None

    def load_model_by_firm(self, firm_name: str) -> List[LLMGenerator]:
        model_list: List[str] = self.config[firm_name]['model_list']
        firm_model_config_url = f"adapter/model_sdk/setting/openai/{firm_name}_model.json"
        firm_model_config = JSONFileUtil(firm_model_config_url)
        generator_list: List[LLMGenerator] = []
        for model in model_list:
            firm_model_dict = firm_model_config.read_key(model)
            if firm_model_dict:
                generator_list.append(LLMGenerator.model_validate(firm_model_dict))
            else:
                generator_list.append(LLMGenerator.from_disabled(firm=firm_name, model=model))
        return generator_list

    def load_enabled_model_by_firm(self, firm_name: str) -> List[LLMGenerator]:
        firm_model_config_url = f"adapter/model_sdk/setting/openai/{firm_name}_model.json"
        firm_model_config = JSONFileUtil(firm_model_config_url)
        generator_list: List[LLMGenerator] = []
        for model in firm_model_config.read().keys():
            firm_model_dict = firm_model_config.read_key(model)
            if firm_model_dict:
                generator_list.append(LLMGenerator.model_validate(firm_model_dict))
        return generator_list

    def enable_or_disable_model(self, firm: str, model: str, enabled: bool) -> Optional[bool]:
        firm_model_config_url = f"adapter/model_sdk/setting/openai/{firm}_model.json"
        firm_model_config = JSONFileUtil(firm_model_config_url)
        if enabled:
            llm_generator: LLMGenerator = LLMGenerator.from_init(firm=firm, model=model)
            firm_model_config.update_key(model, llm_generator.model_dump())
        else:
            firm_model_config.delete(model)
        return True

    # def __init__(self, ):
    #     config: Dict[str, Any] = load_yaml('adapter/model_sdk/setting/openai/model.yaml')
    #
    #     self.model_map: Dict = load_yaml("adapter/model_sdk/setting/openai/model_position.yaml")
    #     self.base_url_map: Dict = load_yaml("adapter/model_sdk/setting/openai/model_base_url.yaml")

    def generate(self,
         llm_generator: LLMGenerator,
         tools: Iterable[Tool] = None,
         messages: Iterable[ChatStreamingChunk] = None
         # generation_kwargs: Optional[Dict[str, Any]] = None,
         # *,
         # tools: Optional[List[Tool]] = None,
         ) -> ChatStreamingChunk:
        client: ModelClient = OpenAIClient()
        url = self.config[llm_generator.firm]["base_url"]
        rs = client.generate(
            model=llm_generator.model,
            api_secret=llm_generator.api_key_secret,
            base_url=url,
            message_list=messages,
            tools=tools
        )
        print(rs)
        return rs

    async def generate_stream(self,
        llm_generator: LLMGenerator,
        tools: Iterable[Tool] = None,
        messages: Iterable[ChatStreamingChunk] = None
        ) -> AsyncGenerator[ChatStreamingChunk, None]:

        client: ModelClient = OpenAIClient()
        url = self.config[llm_generator.firm]["base_url"]
        for chunk in client.generate_stream(
            model=llm_generator.model,
            api_secret=llm_generator.api_key_secret,
            base_url=url,
            message_list=messages,
            tools=tools
        ):
            await asyncio.sleep(0.05) # 主动让出事件循环，避免流式响应时候其他接口的pending TODO 真特么丑陋，待优化吧
            yield chunk