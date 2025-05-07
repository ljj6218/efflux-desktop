from application.domain.generators.tools import Tool, ToolInstance
from application.port.outbound.generators_port import GeneratorsPort
from application.port.outbound.tools_port import ToolsPort
from application.domain.generators.chat_completion.chat_completion_message_param import ChatCompletionMessageParam
from application.domain.generators.chat_chunk.chunk import ChatStreamingChunk
from common.utils.auth import ApiKeySecret
from typing import List, AsyncGenerator, Optional
import asyncio
from common.core.logger import get_logger

logger = get_logger(__name__)


class AgentGenerator:

    def __init__(
            self,
            generator: GeneratorsPort,
            tools_port: ToolsPort,
            model: str,
            api_secret: ApiKeySecret,
            firm: str
            ):
        self.tools_port = tools_port
        self.system = None
        self.ID: int = 1
        self.tools: List[Tool] = []
        self.short_memory: List[ChatCompletionMessageParam] = []
        self.generator = generator
        self.model: str = model
        self.api_secret: ApiKeySecret = api_secret
        self.firm: str = firm

    def set_system(self, system: str):
        """set system prompt"""
        self.system = system

    def add_tool(self, tools: List[Tool]):
        """add tools"""
        for tool in tools:
            self.tools.append(tool)

    def set_short_memory(self, short_memory: List[ChatCompletionMessageParam]):
        """setting short_memory"""
        self.short_memory = short_memory

    def run(self, query_message: ChatCompletionMessageParam):
        """
        agent 请求
        :param query_message: 用户最新问题消息对象
        :return:
        """
        # message 封装
        messages: List[ChatCompletionMessageParam] = self._make_message(query_message)
        # TODO 判断是否使用tool
        self.generator.generate(model=self.model, api_secret=self.api_secret, firm=self.firm, messages=messages, tools=self.tools)

    async def run_stream(self, query_message: ChatCompletionMessageParam) -> AsyncGenerator[ChatStreamingChunk, None]:
        """
        agent 流式请求
        :param query_message: 用户最新问题消息对象
        :return:
        """
        # message 封装
        messages: List[ChatCompletionMessageParam] = self._make_message(query_message)
        # agent 配置的 generate 发起真正的模型请求
        async for chunk in self.generator.generate_stream(model=self.model, api_secret=self.api_secret, firm=self.firm, messages=messages, tools=self.tools):
            yield chunk
            # 工具调用 TODO 后续增加工具调用授权
            async for sub_chunk in self._tool_result_call_back(chunk, messages):
                yield sub_chunk

    def _make_message(self, query_message: ChatCompletionMessageParam) -> List[ChatCompletionMessageParam]:
        """
        模型请求消息集合封装
        :param query_message: 用户最新问题消息对象
        :return: 模型请求消息集合
        """
        messages: List[ChatCompletionMessageParam] = []
        # 系统提示词
        if self.system:
            messages.append({'role': 'system', 'content': self.system})
        # 拼装记忆
        if self.short_memory:
            messages.extend(self.short_memory)
        # 拼装query
        messages.append(query_message)
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
                tool_instance = ToolInstance(tool)
                tool_instance.arguments = arg
                tool_instance.tool_call_id = call_id
                return tool_instance
        return None

    async def _tool_result_call_back(self, chunk: ChatStreamingChunk, messages: List[ChatCompletionMessageParam]) -> AsyncGenerator[ChatStreamingChunk, None]:
        """
        递归调用收集所有的tools call PS：目前根据模型不同，多工具调用的时候可能出现（多个chuck每个chunk调用一个tools｜一个chunk，chunk内包含tools call数组）两种情况
        :param chunk: 返回的流式tools call chunk
        :param messages: 模型消息体集合
        :return: 流式chunk
        """
        # 判断工具调用
        if chunk and chunk.finish_reason == "tool_calls":
            tool_task_list = []
            for tool_call in chunk.tool_calls:
                tool_task_list.append(
                    self.tools_port.call_tools(self._get_tool_instances(tool_call.id, tool_call.name, tool_call.arguments)))
                logger.info(f"需要调用工具：{tool_call.id}-{tool_call.name}-{tool_call.arguments}")
            # 并行方法调用
            results = await asyncio.gather(*tool_task_list)
            logger.debug(f"工具调用结果：{results}")
            # 封装tool_calls集合
            tool_calls = []
            for tool_call in chunk.tool_calls:
                tool_calls.append(
                    {
                        "function": {
                            "arguments": tool_call.arguments,
                            "name": tool_call.name
                        },
                        "id": tool_call.id,
                        "type": "function"
                    }
                )
            messages.append({
                "role": "assistant",
                "tool_calls": tool_calls
            })
            # 封装tool_calls结果集合
            for tool_call_result in results:
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call_result['id'],
                    # "content": [{
                    #     "type": "text",
                    #     "text": str(tool_call_result['result'])
                    # }]
                    "content": str(tool_call_result['result'])
                })
            async for sub_chunk in self.generator.generate_stream(model=self.model, api_secret=self.api_secret,
                                                            firm=self.firm, messages=messages, tools=self.tools):
                yield sub_chunk
                # 此处需要返回给调用者chunk
                async for tool_call_result_chunk in self._tool_result_call_back(sub_chunk, messages):
                    yield tool_call_result_chunk