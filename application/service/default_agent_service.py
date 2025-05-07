from common.core.container.annotate import component
from application.port.outbound.generators_port import GeneratorsPort
from application.port.outbound.tools_port import ToolsPort
from application.port.outbound.user_setting_port import UserSettingPort
from application.domain.generators.agent import AgentGenerator
from application.domain.generators.tools import Tool
from application.port.inbound.agent_generators_case import AgentGeneratorsCase
from application.domain.generators.chat_chunk.chunk import ChatStreamingChunk
from common.core.errors.business_exception import BusinessException
from common.core.errors.business_error_code import GeneratorErrorCode
from common.core.errors.common_exception import CommonException, handle_async_exception
from common.utils.auth import ApiKeySecret
from typing import List, AsyncGenerator
import asyncio
from common.utils.file_util import open_and_base64, extract_pdf_text, extract_table_like_text
import injector

@component
class DefaultAgentService(AgentGeneratorsCase):

    @injector.inject
    def __init__(self,
                 generators_port: GeneratorsPort,
                 tools_port: ToolsPort,
                 user_setting_port: UserSettingPort):
        self.generators_port = generators_port
        self.tools_port = tools_port
        self.user_setting_port = user_setting_port

    # 动态计算 default 值的函数，接收异常对象
    @staticmethod
    async def _calculate_default_value(exception: CommonException)-> AsyncGenerator[ChatStreamingChunk, None]:
        yield ChatStreamingChunk.from_exception(exception=exception).model_dump_json()

    @handle_async_exception(default_func=_calculate_default_value)
    async def generate(
            self,
            firm: str,
            model: str,
            system: str,
            query: str,
            mcp_name_list: List[str]
    ) -> AsyncGenerator[ChatStreamingChunk, None]:
        # 获取厂商api key
        api_key_secret: ApiKeySecret = self.user_setting_port.load_firm_model_key(firm)
        if not api_key_secret:
            raise BusinessException(error_code=GeneratorErrorCode.NO_APIKEY_FOUND, dynamics_message=firm)
        # 初始化agent
        agent: AgentGenerator = AgentGenerator(
            generator=self.generators_port,
            tools_port=self.tools_port,
            model=model,
            api_secret=api_key_secret,
            firm=firm)
        # 工具装载
        tools: List[Tool] = []
        for mcp_name in mcp_name_list:
            tools.extend(await self.tools_port.load_tools(mcp_name))
        # await asyncio.sleep(10)
        if tools:
            agent.add_tool(tools)
        #
        # file_name = "2502.01142v1.pdf"
        #
        # # file_base64 = open_and_base64(f"uploads/{file_name}")
        #
        # text = extract_table_like_text(f"uploads/{file_name}")
        #
        # print(text)
        if system:
            agent.set_system(system)
        async for chunk in agent.run_stream({"role": "user", "content": query}):
            yield chunk.model_dump_json()

