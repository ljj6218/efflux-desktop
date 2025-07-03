
import asyncio
from fastmcp import Client

async def example():
    async with Client("http://127.0.0.1:9000/mcp") as client:
        await client.ping()
        b = await client.call_tool('greet',{'name':'1111'})
        print(b)

if __name__ == "__main__":
    asyncio.run(example())

