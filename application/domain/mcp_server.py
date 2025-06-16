from pydantic import BaseModel
from typing import Optional, Dict, Any, List

class MCPServer(BaseModel):
    """mcp server 领域对象"""
    # mcp server 名字
    server_name: str = None
    # mcp server 描述
    server_description: Optional[str] = None
    # mcp server 是否启用
    applied: Optional[bool] = False
    # mcp server 是否启用
    enabled: Optional[bool] = True
    # tag
    server_tag: Optional[str] = None
    # 授权自动执行
    execute_authorization: Optional[bool] = False
    # mcp server 配置 env list
    env: Optional[Dict[str, str]] = None
    # mcp server 配置 arg list
    args: Optional[List[str]] = None
    # mcp server 配置 command
    command: Optional[str] = None

