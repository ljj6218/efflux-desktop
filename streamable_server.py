from fastmcp.server import FastMCP
from fastmcp.server.dependencies import get_http_request

def create_server():
    server = FastMCP(name="SSE Demo Server", instructions="A simple SSE demo server.")

    # 添加一个工具
    @server.tool
    def get_headers_tool() -> dict[str, str]:
        """Get the HTTP headers from the request."""
        request = get_http_request()
        data = dict(request.headers)
        data['x'] = '2'
        return data

    # 添加一个资源
    @server.resource(uri="request://headers")
    async def get_headers_resource() -> dict[str, str]:
        request = get_http_request()
        data = dict(request.headers)
        data['x'] = '1'
        return data

    # 添加一个提示
    @server.prompt
    def get_headers_prompt() -> str:
        """Get the HTTP headers from the request."""
        request = get_http_request()
        data = dict(request.headers)
        data['x'] = '3'
        import json
        return json.dumps(data)

    return server

if __name__ == "__main__":
    create_server().run(transport="sse", host="0.0.0.0", port=8000, path="/sse")