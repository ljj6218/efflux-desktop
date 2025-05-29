from typing import List, Optional, Dict, Any

from application.domain.generators.firm import GeneratorFirm
from application.domain.generators.generator import LLMGenerator
from application.port.outbound.generators_port import GeneratorsPort
from application.port.inbound.model_case import ModelCase
from application.domain.events.event import Event, EventType, EventSubType
from common.core.container.annotate import component
from common.utils.common_utils import create_uuid
from application.port.outbound.event_port import EventPort
from application.port.inbound.generators_case import GeneratorsCase
from application.port.outbound.user_setting_port import UserSettingPort
from application.domain.generators.chat_chunk.chunk import ChatStreamingChunk
from application.port.outbound.tools_port import ToolsPort
from application.domain.generators.tools import Tool, ToolInstance, ToolType
from adapter.tools.local.browser.web_surfer import WebSurfer
from common.utils.markdown_util import read
import injector
import asyncio
import json

from common.core.logger import get_logger

logger = get_logger(__name__)

@component
class GeneratorService(ModelCase, GeneratorsCase):


    @injector.inject
    def __init__(self,
                 generators_port: GeneratorsPort,
                 event_port: EventPort,
                 tools_port: ToolsPort,
                 user_setting_port: UserSettingPort,
        ):
        self.generators_port = generators_port
        self.event_port = event_port
        self.tools_port = tools_port
        self.user_setting_port = user_setting_port

    async def firm_list(self) -> List[GeneratorFirm]:
        return self.generators_port.load_firm()

    async def model_list(self, firm: str) -> List[LLMGenerator]:
        return self.generators_port.load_model_by_firm(firm)

    async def enabled_model_list(self, firm: str) -> List[LLMGenerator]:
        if firm:
            return self.generators_port.load_enabled_model_by_firm(firm)
        return self.generators_port.load_enabled_model()

    async def enable_or_disable_model(self, firm: str, model: str, enabled: bool) -> Optional[bool]:
        return self.generators_port.enable_or_disable_model(firm, model, enabled)

    async def generate_test(
        self,
        generator_id: str,
        query: str,
        conversation_id: str,
        mcp_name_list: List[str],
        tools_group_name_list: Optional[List[str]] = None,
        task_confirm: Optional[Dict[str, Any]] = None
    ) -> str:
        # 获取LLMGenerator
        llm_generator: LLMGenerator = self._llm_generator(generator_id)

        message_list = []
        message_list.append(ChatStreamingChunk.from_user(message=query))
        ws = WebSurfer(generators_port=self.generators_port, name="test")

        await ws.on_messages_stream(chunk_list=message_list, generator=llm_generator)


        return "ok"

    async def generate(
        self,
        generator_id: str,
        query: str,
        conversation_id: str,
        mcp_name_list: Optional[List[str]] = None,
        tools_group_name_list: Optional[List[str]] = None,
        task_confirm: Optional[Dict[str, Any]] = None,
    ) -> str:

        # 获取LLMGenerator
        llm_generator: LLMGenerator = self._llm_generator(generator_id)
        # 工具装载
        tools: List[Tool] = []
        for mcp_name in mcp_name_list:
            tools.extend(await self.tools_port.load_tools(group_name=mcp_name, tool_type=ToolType.MCP))
        message_list = []
        message_list.append(ChatStreamingChunk.from_system(message=read("test_prompt.md")))
        message_list.append(ChatStreamingChunk.from_user(message=query))

        # chunk: ChatStreamingChunk = self.generators_port.generate(llm_generator=llm_generator, messages=message_list, tools=tools)
        chunk: ChatStreamingChunk = await self._tool_call(chunk_list=message_list, llm_generator=llm_generator, tools=tools)

        return chunk.content

    async def _tool_call(self, chunk_list: [ChatStreamingChunk], llm_generator: LLMGenerator, tools: List[Tool]) -> ChatStreamingChunk:
        chunk: ChatStreamingChunk = self.generators_port.generate(llm_generator=llm_generator, messages=chunk_list,
                                                                  tools=tools)
        if chunk.finish_reason == "tool_calls":
            # 上下文加入工具调用请求消息
            chunk_list.append(chunk)
            tool_task_list = []
            for tool_call in chunk.tool_calls:
                tool_task_list.append(
                    self.tools_port.call_tools(
                        self._get_tool_instances(tool_call.id, tool_call.name, tool_call.arguments, tools)))
                logger.info(f"需要调用工具：{tool_call.id}-{tool_call.name}-{tool_call.arguments}")
            # 并行方法调用
            results = await asyncio.gather(*tool_task_list)
            logger.debug(f"工具调用结果：{results}")
            for tool_call_result in results:
                chunk_list.append(ChatStreamingChunk.from_tool_calls_result(content=str(tool_call_result['result']), tool_call_id=tool_call_result['id']))
                return await self._tool_call(chunk_list, llm_generator, tools)

        return chunk

    async def generate_stream(
        self,
        generator_id: str,
        query: str,
        system: str,
        conversation_id: str,
        mcp_name_list: Optional[List[str]] = None,
        tools_group_name_list: Optional[List[str]] = None,
        task_confirm: Optional[Dict[str, Any]] = None,
    ) -> str:

        if task_confirm:
            event_data: Dict[str, Any] = {
                'generator_id': generator_id,
                'conversation_id': conversation_id,
                'mcp_name_list': mcp_name_list,
            }
            return self.event_port.emit_event(Event.from_init(event_type=EventType.TOOL_CALL_CONFiRM, event_data=event_data))
        else:
            event = Event.from_init(
                event_type=EventType.USER_MESSAGE,
                event_sub_type=EventSubType.MESSAGE,
                data={
                    "id": create_uuid(),
                    "conversation_id": conversation_id,
                    "generator_id": generator_id,
                    "content": query,
                    "system": system,
                    "mcp_name_list": mcp_name_list,
                    "tools_group_name_list": tools_group_name_list,
                }
            )
            logger.info(f"[GeneratorService]发起[{EventType.USER_MESSAGE} - {EventSubType.MESSAGE}]事件：[ID：{event.id}]")
            return self.event_port.emit_event(event)


            # return self.event_port.emit_event(
            #     Event.from_init(
            #         event_type=EventType.USER_MESSAGE,
            #         event_data=MessageEventData.from_user_message(
            #             content=query, generator_id=generator_id,
            #             conversation_id=conversation_id, mcp_name_list=mcp_name_list
            #         )
            #     )
            # )


    def _llm_generator(self, generator_id: str) -> LLMGenerator:
        # 获取厂商api key
        llm_generator: LLMGenerator = self.generators_port.load_generate(generator_id)
        firm: GeneratorFirm = self.user_setting_port.load_firm_setting(llm_generator.firm)
        llm_generator.set_api_key_secret(firm.api_key)
        llm_generator.check_firm_api_key()
        return llm_generator

    @staticmethod
    def _get_tool_instances(call_id: str, name: str, arg: str, tools: List[Tool]) -> Optional[ToolInstance]:
        """
        根据tools名字转换tools实例对象
        :param call_id: tools call id
        :param name: tools 名字
        :param arg: tools 调用参数
        :return: 工具实例对象
        """
        for tool in tools:
            if tool.name == name:
                tool_instance: ToolInstance = tool.instance()
                tool_instance.arguments = json.loads(arg)
                tool_instance.tool_call_id = call_id
                return tool_instance
        return None