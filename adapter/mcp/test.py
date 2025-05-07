from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
from adapter.mcp.server_loader import load_config, StdioServerParameters
from typing import AsyncGenerator, List, Any
import asyncio


class StdioClientTest:


    def test(self):
        server_params: StdioServerParameters = asyncio.run(load_config("tmdb"))
        asyncio.run(convert_mcp_to_langchain_tools([server_params]))


async def convert_mcp_to_langchain_tools(server_params: List[StdioServerParameters]) -> List[Any]:
    """Convert MCP tools to LangChain tools."""
    langchain_tools = []

    for server_param in server_params:
        # cached_tools = get_cached_tools(server_param)
        #
        # if cached_tools:
        #     for tool in cached_tools:
        #         langchain_tools.append(create_langchain_tool(tool, server_param))
        #     continue

        async with stdio_client(server_param) as (read, write):
            async with ClientSession(read, write) as session:
                print(f"Gathering capability of {server_param.command} {' '.join(server_param.args)}")
                await session.initialize()
                tools_rs: types.ListToolsResult = await session.list_tools()
                # save_tools_cache(server_param, tools.tools)
                # prompt_rs: types.ListPromptsResult = await session.list_prompts()
                # rs_rs: types.ListResourcesResult = await session.list_resources()


                print("===========Tools=============")
                for tool in tools_rs.tools:
                    print(tool)
                # print("===========Prompt=============")
                # for prompt in prompt_rs.prompts:
                #     print(prompt)
                # print("===========Resource=============")
                # for resource in rs_rs.resources:
                #     print(resource)

    return langchain_tools