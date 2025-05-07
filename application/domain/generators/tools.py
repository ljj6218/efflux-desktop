from pydantic import BaseModel
from typing import Any, Optional


class Tool(BaseModel):
    """
    工具定义
    """
    # The name of the mcp server
    server_name: Optional[str]
    # The name of the tool
    name: Optional[str]
    # A human-readable description of the tool
    description: Optional[str] = None
    # Tool call input
    inputSchema: Optional[dict[str, Any]]


class ToolInstance(Tool):
    """
    工具调用实例
    """
    # Tool call instance ID
    tool_call_id: Optional[str] = None
    # args of the tool instance
    arguments: Optional[dict[str, Any]] = None
    # results of the tool instance
    result: Optional[dict[str, Any]] = None

    def __init__(self, tool: Tool):
        super().__init__(
            name = tool.name,
            server_name = tool.server_name,
            description = tool.description,
            inputSchema = tool.inputSchema
        )