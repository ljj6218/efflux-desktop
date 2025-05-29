from pydantic import BaseModel
from typing import Optional, Dict, Any, List

class MCPServer(BaseModel):
    """mcp server 领域对象"""
    # mcp server ID
    # server_id: Optional[str]
    # mcp server 名字
    server_name: str = None
    # mcp server 描述
    server_description: Optional[str] = None
    # mcp server 是否应用
    applied: bool = False
    # mcp server 是否启用
    enabled: bool = True
    # tag
    server_tag: Optional[str] = None
    # 授权自动执行
    execute_authorization: bool = False
    # mcp server 配置 env list
    env: Dict[str, str] = None
    # mcp server 配置 arg list
    args: List[str] = None
    # mcp server 配置 command
    command: str = None

