from mcp.types import CallToolResult
from mcp import ClientSession, types
from mcp.client.stdio import StdioServerParameters, stdio_client
import injector
import jsonlines
from common.utils.file_util import check_file_and_create, check_file
from common.core.container.annotate import component
from application.domain.generators.tools import Tool, ToolInstance, ToolType
from common.core.errors.system_exception import ThirdPartyServiceException, ThirdPartyServiceApiCode
from application.port.outbound.mcp_server_port import MCPServerPort
from application.domain.mcp_server import MCPServer
from typing import List, Optional
from datetime import timedelta
import json
from common.core.logger import get_logger
from fastmcp import Client
import traceback
logger = get_logger(__name__)

# mcp 访问超时时间
delta = timedelta(seconds=120)

@component
class McpToolsAdapter:
    """
    stdio 模式的 mcp server tools 调用
    """

    @injector.inject
    def __init__(self, mcp_server_port: MCPServerPort):
        self.mcp_server_port = mcp_server_port
        self.tool_calls_file_pre_url = "conversations/tool_calls_record/"

    # def save_instance(self, tool_instance: ToolInstance) -> ToolInstance:
    #     tool_calls_file = f"{self.tool_calls_file_pre_url}{tool_instance.conversation_id}.jsonl"
    #     check_file_and_create(tool_calls_file)
    #     with jsonlines.open(tool_calls_file, mode='a') as writer:
    #         writer.write(tool_instance.model_dump())
    #     return tool_instance
    #
    # def load_instance(self,
    #     conversation_id: str,
    #     dialog_segment_id: Optional[str] = None,
    #     tool_call_id: Optional[str] = None
    # ) -> List[ToolInstance]:
    #     tool_calls_file = f"{self.tool_calls_file_pre_url}{conversation_id}.jsonl"
    #     tool_calls_list : List[ToolInstance] = []
    #     if check_file(tool_calls_file):
    #         with jsonlines.open(tool_calls_file, mode='r') as reader:
    #             for obj in reader:
    #                 if dialog_segment_id is None and tool_call_id is None:
    #                     tool_calls_list.append(ToolInstance.model_validate(obj))
    #                 if obj['dialog_segment_id'] == dialog_segment_id:
    #                     tool_calls_list.append(ToolInstance.model_validate(obj))
    #                 if obj['tool_call_id'] == tool_call_id:
    #                     tool_calls_list.append(ToolInstance.model_validate(obj))
    #     return tool_calls_list
    #
    # def update_instance(self, tool_instance: ToolInstance) -> Optional[ToolInstance]:
    #     tool_calls_file = f"{self.tool_calls_file_pre_url}{tool_instance.conversation_id}.jsonl"
    #     updated = False
    #     updated_instance_list = []  # 用于存储更新后的工具实例
    #     with jsonlines.open(tool_calls_file, mode='r') as reader:
    #         # 读取所有现有的工具实例
    #         for obj in reader:
    #             old_tool_instance = ToolInstance.model_validate(obj)
    #             if old_tool_instance and old_tool_instance.tool_call_id == tool_instance.tool_call_id:
    #                 # 更新目标工具实例
    #                 old_tool_instance.result = tool_instance.result
    #                 updated = True
    #             # 将修改后的工具实例添加到列表中
    #             updated_instance_list.append(old_tool_instance)
    #     # 如果找到了匹配的工具实例并进行了更新
    #     if updated:
    #         # 将所有更新后的工具实例重新写入到 JSONL 文件
    #         with jsonlines.open(tool_calls_file, mode='w') as writer:
    #             for updated_instance in updated_instance_list:
    #                 writer.write(updated_instance.model_dump())  # 将对象写为字典
    #         return tool_instance  # 返回更新后的工具实例对象
    #     else:
    #         return None  # 如果没有找到匹配的工具实例对象，则返回 None

    async def load_tools(self, mcp_server_name: str) -> List[Tool]:
        stdio_server_parameters: StdioServerParameters = self._load_config(mcp_server_name)
        logger.info('load_tools ///////////////////////// 0')
        logger.info('stdio_server_parameters')
        logger.info(stdio_server_parameters)
        '''
        command='http' args=['http://127.0.0.1:9000/mcp']
        env={} cwd=None encoding='utf-8' encoding_error_handler='strict'
        '''
        tools = []
        if stdio_server_parameters.command == 'http':
            logger.info('load_tools ///////////////////////// 1')
            async with Client(stdio_server_parameters.args[0]) as client:
                logger.info('load_tools ///////////////////////// 1.1')
                await client.ping()
                logger.info('load_tools ///////////////////////// 1.2')
                http_tools = await client.list_tools()
                logger.info('load_tools ///////////////////////// 1.3')
                logger.info('http_tools')
                logger.info(http_tools)
                '''
                Tool(
                    name='greet',
                    title=None,
                    description=None,
                    inputSchema={
                        'properties': {
                            'name': {
                                'title': 'Name',
                                'type': 'string'
                            }
                        },
                        'required': ['name'],
                        'type': 'object'
                    },
                    outputSchema={
                        'properties': {
                            'result': {
                                'title': 'Result',
                                'type': 'string'
                            }
                        },
                        'required': ['result'],
                        'title': '_WrappedResult',
                        'type': 'object',
                        'x-fastmcp-wrap-result': True
                    },
                    annotations=None,
                    meta=None
                )
                '''
                # b = await client.call_tool('greet',{'name':'1111'})
                # logger.info(b)
                for mcp_tool in http_tools:
                    logger.info('mcp_tool')
                    logger.info(mcp_tool)
                    tool = Tool(
                        mcp_server_name=mcp_server_name,
                        name=mcp_tool.name,
                        description=mcp_tool.description,
                        input_schema=mcp_tool.inputSchema,
                        type=ToolType.HTTP
                    )
                    tools.append(tool)
        else:
            async with stdio_client(stdio_server_parameters) as (read, write):
                logger.info('load_tools ///////////////////////// 2')
                async with ClientSession(read_stream=read, write_stream=write, read_timeout_seconds=delta) as session:
                    await session.initialize()
                    tools_rs: types.ListToolsResult = await session.list_tools()
                    for mcp_tool in tools_rs.tools:
                        logger.debug(f"load Tool: {mcp_tool.name} Description: {mcp_tool.description} InputSchema: {mcp_tool.inputSchema} ModelConfig: {mcp_tool.model_config}")
                        tool = Tool(mcp_server_name=mcp_server_name,name=mcp_tool.name, description=mcp_tool.description, input_schema=mcp_tool.inputSchema, type=ToolType.MCP)
                        tools.append(tool)
        return tools

    async def call_tools(self, tool_instance: ToolInstance) -> dict[str, list[types.TextContent | types.ImageContent | types.EmbeddedResource] | str]:
        stdio_server_parameters: StdioServerParameters = self._load_config(tool_instance.mcp_server_name)
        if stdio_server_parameters.command == 'http':
            logger.info('load_tools ///////////////////////// 1')
            async with Client(stdio_server_parameters.args[0]) as client:
                logger.info('load_tools ///////////////////////// 1.1')
                try:
                    call_tool_result = await client.call_tool(
                        tool_instance.name,
                        tool_instance.arguments
                    )
                    '''
                    CallToolResult(
                        content=[
                            TextContent(
                                type='text',
                                text='Hello, 1111!',
                                annotations=None, meta=None
                            )
                        ],
                        structured_content={'result': 'Hello, 1111!'},
                        data='Hello, 1111!',
                        is_error=False)
                    '''
                    logger.info('call_tool_result ++++++++++----------')
                    logger.info(call_tool_result)
                    logger.info(dir(call_tool_result))
                except Exception as e:
                    logger.error(traceback.format_exc())
                    raise ThirdPartyServiceException(
                        error_code=ThirdPartyServiceApiCode.MCP_SERVER_API_ERROR,
                        dynamics_message=f"tools call: {tool_instance.mcp_server_name} {tool_instance.name} failed - message: ")
                if call_tool_result.is_error:
                    raise ThirdPartyServiceException(
                        error_code=ThirdPartyServiceApiCode.MCP_SERVER_API_ERROR,
                        dynamics_message=f"tools call: {tool_instance.mcp_server_name} {tool_instance.name} failed - message: {str(e)}")
                data_list = [call_tool_result.data]
                logger.info('data_list -------------------------')
                logger.info(data_list)
                return {"id": tool_instance.tool_call_id, "result": data_list}
        else:
            async with stdio_client(stdio_server_parameters) as (read, write):
                async with ClientSession(read_stream=read, write_stream=write, read_timeout_seconds=delta) as session:
                    await session.initialize()
                    logger.debug(f"工具调用参数：{tool_instance.arguments}")
                    try:
                        result: CallToolResult = await session.call_tool(name=tool_instance.name, arguments=tool_instance.arguments)
                    except Exception as e:
                        raise ThirdPartyServiceException(
                            error_code=ThirdPartyServiceApiCode.MCP_SERVER_API_ERROR,
                            dynamics_message=f"tools call: {tool_instance.mcp_server_name} {tool_instance.name} failed - message: {str(e)}")
                    if result.isError:
                        raise ThirdPartyServiceException(
                            error_code=ThirdPartyServiceApiCode.MCP_SERVER_API_ERROR,
                            dynamics_message=f"tools call: {tool_instance.mcp_server_name} {tool_instance.name} failed - message: {str(result.content)}")
                    data_list = []
                    for result_content in result.content:
                        data_list.append(result_content.model_dump_json())
                    return {"id": tool_instance.tool_call_id, "result": data_list}

    def _load_config(self, mcp_server_name: str) -> StdioServerParameters:
        mcp_server: MCPServer = self.mcp_server_port.load_applied(mcp_server_name)
        return StdioServerParameters(
            command= mcp_server.command,
            args= mcp_server.args,
            env= mcp_server.env,
        )