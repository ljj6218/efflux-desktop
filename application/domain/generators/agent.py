from application.domain.generators.tools import Tool, ToolInstance
from application.port.outbound.generators_port import GeneratorsPort
from application.port.outbound.tools_port import ToolsPort
from application.port.outbound.mcp_server_port import MCPServerPort
from application.domain.generators.chat_chunk.chunk import ChatStreamingChunk
from application.domain.generators.generator import LLMGenerator
from typing import List, AsyncGenerator, Generator, Optional, Set
import asyncio
from common.core.logger import get_logger

logger = get_logger(__name__)

class AgentGenerator:

    def __init__(
            self,
            generator_port: GeneratorsPort,
            tools_port: ToolsPort,
            mcp_server_port: MCPServerPort,
            llm_generator: LLMGenerator,
            ):
        self.tools_port = tools_port
        self.system = None
        self.ID: int = 1
        self.tools: List[Tool] = []
        self.short_memory: List[ChatStreamingChunk] = []
        self.generator_port = generator_port
        self.mcp_server_port: MCPServerPort = mcp_server_port
        self.llm_generator = llm_generator

    def set_system(self, system: str):
        """set system prompt"""
        self.system = system

    def add_tool(self, tools: List[Tool]):
        """add tools"""
        for tool in tools:
            self.tools.append(tool)

    def set_short_memory(self, short_memory: List[ChatStreamingChunk]):
        """setting short_memory"""
        self.short_memory = short_memory

    def add_short_memory(self, short_memory: ChatStreamingChunk):
        self.short_memory.append(short_memory)

    async def run(self, query_message: ChatStreamingChunk) -> ChatStreamingChunk:
        """
        agent 请求
        :param query_message: 用户最新问题消息对象
        :return:
        """
        # message 封装
        messages: List[ChatStreamingChunk] = self._make_message(query_message)
        # TODO 判断是否使用tool
        # generator = LLMGenerator(firm=self.firm, model=self.model, api_key_secret=self.api_secret)
        return self.generator_port.generate(llm_generator=self.llm_generator, messages=messages, tools=self.tools)
        # return self.generator.generate(model=self.model, api_secret=self.api_secret, firm=self.firm, messages=messages, tools=self.tools)

    async def run_stream(self, query_chunk: ChatStreamingChunk) -> AsyncGenerator[ChatStreamingChunk, None]:
        """
        agent 流式请求
        :param query_chunk: 用户最新问题消息对象
        :return:
        """
        # 用户确认工具调用
        if query_chunk.user_confirm:
            messages: List[ChatStreamingChunk] = self._make_message()
            tool_calls_chunk = messages.pop()
            # 判断用户授权结果
            if query_chunk.user_confirm.user_confirmation_result:
                # 工具调用
                async for sub_chunk in self._tool_result_call_back(tool_calls_chunk, messages):
                    yield sub_chunk
        else:
            # message 封装
            messages: List[ChatStreamingChunk] = self._make_message(query_chunk)
            # agent 配置的 generate 发起真正的模型请求
            async for chunk in self.generator_port.generate_stream(llm_generator=self.llm_generator, messages=messages, tools=self.tools):
                yield chunk
                # 判断工具调用
                if chunk and chunk.finish_reason == "tool_calls":
                    unauthorized_mcp_server_names: Set[str] = set()
                    for tool_call in chunk.tool_calls:
                        if not self.mcp_server_port.is_authorized(tool_call.mcp_server_name):
                            unauthorized_mcp_server_names.add(tool_call.mcp_server_name)
                    # 判断是否有未授权的mcp server
                    if len(unauthorized_mcp_server_names) > 0:
                        # 发送用户授权请求
                        yield ChatStreamingChunk.from_user_confirm(
                            message=f"是否授权工具[{"|".join(unauthorized_mcp_server_names)}]运行", model=self.llm_generator.model)
                    else:
                        # 工具调用
                        async for sub_chunk in self._tool_result_call_back(chunk, messages):
                            yield sub_chunk

    def _make_message(self, query_chunk: Optional[ChatStreamingChunk] = None) -> List[ChatStreamingChunk]:
        """
        模型请求消息集合封装
        :param query_chunk: 用户最新问题消息对象
        :return: 模型请求消息集合
        """
        messages: List[ChatStreamingChunk] = []
        # 系统提示词
        if self.system:
            messages.append(ChatStreamingChunk.from_system(self.system))
        # 拼装记忆
        if self.short_memory:
            messages.extend(self.short_memory)
        # 拼装query
        if query_chunk:
            messages.append(query_chunk)
        return messages

    def _get_tool_instances(self, call_id: str, name: str, arg: str) -> Optional[ToolInstance]:
        """
        根据tools名字转换tools实例对象
        :param call_id: tools call id
        :param name: tools 名字
        :param arg: tools 调用参数
        :return: 工具实例对象
        """
        for tool in self.tools:
            if tool.name == name:
                tool_instance = ToolInstance.from_init(name=tool.name, mcp_server_name=tool.server_name, description=tool.description, input_schema=tool.input_schema)
                tool_instance.arguments = arg
                tool_instance.tool_call_id = call_id
                return tool_instance
        return None

    async def _tool_result_call_back(self, chunk: ChatStreamingChunk, messages: List[ChatStreamingChunk]) -> AsyncGenerator[ChatStreamingChunk, None]:
        """
        递归调用收集所有的tools call PS：目前根据模型不同，多工具调用的时候可能出现（多个chuck每个chunk调用一个tools｜一个chunk，chunk内包含tools call数组）两种情况
        :param chunk: 返回的流式tools call chunk
        :param messages: 模型消息体集合
        :return: 流式chunk
        """
        # 判断工具调用
        if chunk and (chunk.finish_reason == "tool_calls"):
            # 上下文加入工具调用请求消息
            messages.append(chunk)
            tool_task_list = []
            for tool_call in chunk.tool_calls:
                tool_task_list.append(
                    self.tools_port.call_tools(self._get_tool_instances(tool_call.id, tool_call.name, tool_call.arguments)))
                logger.info(f"需要调用工具：{tool_call.id}-{tool_call.name}-{tool_call.arguments}")
            # 并行方法调用
            results = await asyncio.gather(*tool_task_list)
            logger.debug(f"工具调用结果：{results}")
            # 封装tool_calls结果集合
            for tool_call_result in results:
                messages.append(ChatStreamingChunk.from_tool_calls_result(content=str(tool_call_result['result']), tool_call_id=tool_call_result['id']))
            async for sub_chunk in self.generator_port.generate_stream(llm_generator=self.llm_generator, messages=messages, tools=self.tools):
                yield sub_chunk
                # 此处需要返回给调用者chunk
                async for tool_call_result_chunk in self._tool_result_call_back(sub_chunk, messages):
                    yield tool_call_result_chunk
