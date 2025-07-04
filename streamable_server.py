from fastmcp import FastMCP

mcp = FastMCP("My MCP Server")
# @mcp.custom_route("/health", methods=["GET"])
@mcp.tool()
def greet(name: str) -> str:
    print(1111)
    return f"Hello, {name}! 我是超人"

if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="127.0.0.1", port=9000)



