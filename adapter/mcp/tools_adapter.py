from mcp.types import CallToolResult

from application.port.outbound.tools_port import ToolsPort
from mcp import ClientSession, types
from mcp.client.stdio import StdioServerParameters, stdio_client
import injector
from common.core.container.annotate import component
from application.domain.generators.tools import Tool, ToolInstance
from common.core.errors.system_exception import ThirdPartyServiceException, ThirdPartyServiceApiCode
from application.port.outbound.mcp_server_port import MCPServerPort
from application.domain.mcp_server import MCPServer
from typing import List
from datetime import timedelta
import json
from common.core.logger import get_logger

logger = get_logger(__name__)

# mcp 访问超时时间
delta = timedelta(seconds=10)

@component
class ToolsAdapter(ToolsPort):
    """
    stdio 模式的 mcp server tools 调用
    """


    @injector.inject
    def __init__(self, mcp_server_port: MCPServerPort):
        self.mcp_server_port = mcp_server_port


    async def load_tools(self, server_name) -> List[Tool]:
        stdio_server_parameters: StdioServerParameters = self._load_config(server_name)
        tools = []
        async with stdio_client(stdio_server_parameters) as (read, write):
            async with ClientSession(read_stream=read, write_stream=write, read_timeout_seconds=delta) as session:
                await session.initialize()
                tools_rs: types.ListToolsResult = await session.list_tools()
                for mcp_tool in tools_rs.tools:
                    logger.debug(f"load Tool: {mcp_tool.name} Description: {mcp_tool.description} InputSchema: {mcp_tool.inputSchema} ModelConfig: {mcp_tool.model_config}")
                    tool = Tool(server_name=server_name,name=mcp_tool.name, description=mcp_tool.description, inputSchema=mcp_tool.inputSchema)
                    tools.append(tool)
        return tools


    async def call_tools(self, tool_instance: ToolInstance) -> dict[str, list[types.TextContent | types.ImageContent | types.EmbeddedResource] | str]:
        stdio_server_parameters: StdioServerParameters = self._load_config(tool_instance.server_name)
        async with stdio_client(stdio_server_parameters) as (read, write):
            async with ClientSession(read_stream=read, write_stream=write, read_timeout_seconds=delta) as session:
                await session.initialize()
                logger.debug(f"工具调用参数：{tool_instance.arguments}")
                try:
                    result: CallToolResult = await session.call_tool(name=tool_instance.name, arguments=json.loads(tool_instance.arguments))
                except Exception as e:
                    raise ThirdPartyServiceException(
                        error_code=ThirdPartyServiceApiCode.MCP_SERVER_API_ERROR,
                        dynamics_message=f"tools call: {tool_instance.server_name} {tool_instance.name} failed - message: {str(e)}")
                if result.isError:
                    raise ThirdPartyServiceException(
                        error_code=ThirdPartyServiceApiCode.MCP_SERVER_API_ERROR,
                        dynamics_message=f"tools call: {tool_instance.server_name} {tool_instance.name} failed - message: {str(result.content)}")
                data_list = []
                for result_content in result.content:
                    data_list.append(result_content.model_dump_json())
                return {"id": tool_instance.tool_call_id, "result": data_list}

    def _load_config(self, server_name: str) -> StdioServerParameters:
        mcp_server: MCPServer = self.mcp_server_port.load_applied(server_name)
        return StdioServerParameters(
            command= mcp_server.command,
            args= mcp_server.args,
            env= mcp_server.env,
        )