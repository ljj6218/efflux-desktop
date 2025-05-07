from pydantic import BaseModel
from typing import Optional, Dict, Any

class MCPServer(BaseModel):
    """mcp server 领域对象"""
    # mcp server ID
    server_id: Optional[str]
    # mcp server 名字
    server_name: Optional[str] = None
    # mcp server 描述
    server_description: Optional[str] = None
    # mcp server 图标
    server_icon: Optional[str] = None
    # 授权自动执行
    execute_authorization: bool = False
    # mcp server 配置json
    content: Optional[Dict[str, Any]] = None