from openai import api_key

from application.port.outbound.generators_port import GeneratorsPort
from application.domain.generators.tools import Tool
from application.domain.generators.generator import LLMGenerator
from application.domain.generators.firm import GeneratorFirm
from common.core.container.annotate import component
from typing import Iterable, Dict, AsyncGenerator, Any, List, Optional, Generator, Callable
from application.domain.generators.chat_chunk.chunk import ChatStreamingChunk
from common.utils.yaml_util import load_yaml
from adapter.model_sdk.client import ModelClient
from adapter.model_sdk.openai.client import OpenAIClient
from common.utils.json_file_util import JSONFileUtil
import asyncio
import json
import re

@component
class ClientManager(GeneratorsPort):

    user_setting_file_url = "user_setting.json"

    def __init__(self):
        self.config: Dict[str, Any] = load_yaml('adapter/model_sdk/setting/openai/model.yaml')
        self.user_setting = JSONFileUtil(self.user_setting_file_url)

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

    def load_firm(self) -> List[GeneratorFirm]:
        firm_list: List[GeneratorFirm] = []
        for firm in self.config.keys():
            firm_list.append(GeneratorFirm.from_init(name=firm, base_url=self.config[firm]['base_url'], model_list=self.config[firm]['model_list']))
        return firm_list

    def load_model_by_firm(self, firm_name: str) -> List[LLMGenerator]:
        firm_dict = self.user_setting.read_key(firm_name)
        base_url = firm_dict['base_url']
        api_key = firm_dict['api_key']
        client: ModelClient = OpenAIClient()
        client.model_list(base_url=base_url, api_key=api_key)

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

    def load_enabled_model(self) -> List[LLMGenerator]:
        firm_list: List[GeneratorFirm] = []
        for firm in self.config.keys():
            firm_list.extend(self.load_enabled_model_by_firm(firm))
        return firm_list

    def enable_or_disable_model(self, firm: str, model: str, enabled: bool) -> Optional[bool]:
        firm_model_config_url = f"adapter/model_sdk/setting/openai/{firm}_model.json"
        firm_model_config = JSONFileUtil(firm_model_config_url)
        if enabled:
            llm_generator: LLMGenerator = LLMGenerator.from_init(firm=firm, model=model)
            firm_model_config.update_key(model, llm_generator.model_dump())
        else:
            firm_model_config.delete(model)
        return True

    def generate(self,
        llm_generator: LLMGenerator,
        tools: Iterable[Tool] = None,
        messages: Iterable[ChatStreamingChunk] = None,
        **generation_kwargs,
    ) -> ChatStreamingChunk:
        client: ModelClient = OpenAIClient()
        firm_setting = self.user_setting.read_key(llm_generator.firm)
        url = firm_setting["base_url"]
        rs = client.generate(
            model=llm_generator.model,
            api_secret=llm_generator.api_key_secret,
            base_url=url,
            message_list=messages,
            tools=tools,
            generation_kwargs=generation_kwargs
        )
        return rs

    def generate_json(
        self,
        llm_generator: LLMGenerator,
        validate_json: Optional[Callable[[Dict[str, Any]], bool]] = None,
        messages: Iterable[ChatStreamingChunk] = None,
        **generation_kwargs,
    ) -> Dict[str, Any] | None:
        retries = 0
        while retries < 1:
            contents = ""
            for chunk in self.generate_event(llm_generator=llm_generator, messages=messages, tools=[], **generation_kwargs):
                contents += chunk.content if chunk.content else ""
            try:
                print(contents)
                if contents.startswith("```json"):
                    # remove first and last line
                    response_lines = contents.split("\n")
                    response_lines = response_lines[1:-1]
                    contents = "\n".join(response_lines)
                json_response = json.loads(contents)
                # Use the validate_json function to check the response
                if validate_json and validate_json(json_response):
                    return json_response
                else:
                    return json_response
                    exception_message = "Validation failed for JSON response, retrying. You must return a valid JSON object parsed from the response."
            except json.JSONDecodeError as e:
                json_response = JSONFileUtil.extract_json_from_string(contents)
                if json_response is not None:
                    if validate_json and validate_json(json_response):
                        return json_response
                    else:
                        return json_response
                        exception_message = "Validation failed for JSON response, retrying. You must return a valid JSON object parsed from the response."
                else:
                    exception_message = f"Failed to parse JSON response, retrying. You must return a valid JSON object parsed from the response. Error: {e}"
                    return {"content": f"转换json失败 -> {contents}"}
            retries += 1
        raise ValueError("Failed to get a valid JSON response after multiple retries")

    def generate_event(self,
        llm_generator: LLMGenerator,
        messages: Iterable[ChatStreamingChunk] = None,
        tools: Iterable[Tool] = None,
        **generation_kwargs,
    ) -> Generator[ChatStreamingChunk, None, None]:
        client: ModelClient = OpenAIClient()
        firm_setting = self.user_setting.read_key(llm_generator.firm)
        url = firm_setting["base_url"]
        return client.generate_stream(
            model=llm_generator.model,
            api_secret=llm_generator.api_key_secret,
            base_url=url,
            message_list=messages,
            tools=tools,
            generation_kwargs=generation_kwargs
        )