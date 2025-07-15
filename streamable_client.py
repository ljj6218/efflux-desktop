import asyncio
from fastmcp.client import Client
from fastmcp.client.transports import SSETransport

async def main():
    server_url = "http://127.0.0.1:8000/sse/"
    async with Client(transport=SSETransport(server_url, headers={"X-DEMO-HEADER": "ABC"})) as client:
        # 测试读取资源
        raw_result = await client.read_resource("request://headers")
        import json
        json_result = json.loads(raw_result[0].text)
        print("Headers from resource:")
        print(raw_result)
        print(json_result)

        # 测试调用工具
        result = await client.call_tool("get_headers_tool")
        print("Headers from tool:")
        print(result.data)

        # 测试获取提示
        result = await client.get_prompt("get_headers_prompt")
        json_result = json.loads(result.messages[0].content.text)
        print("Headers from prompt:")
        print(json_result)

if __name__ == "__main__":
    asyncio.run(main())