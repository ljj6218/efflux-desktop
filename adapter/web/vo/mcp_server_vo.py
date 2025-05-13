from pydantic import BaseModel
from typing import Optional, Dict, List
from application.domain.mcp_server import MCPServer

class MCPServerVo(BaseModel):
    # mcp server 名字
    server_name: str = None
    # mcp server 描述
    server_description: Optional[str] = None
    # mcp server 是否启用
    applied: Optional[bool] = False
    # 授权自动执行
    execute_authorization: bool = False
    # mcp server 配置 env list
    env: Dict[str, str] = None
    # mcp server 配置 arg list
    args: List[str] = None
    # mcp server 配置 command
    command: str = None

    def convert_mcp_server(self) -> MCPServer:
        return MCPServer.model_validate(self.model_dump())

class MCPServerResultVo(BaseModel):
    # mcp server 名字
    server_name: str = None
    # mcp server 描述
    server_description: Optional[str] = None
    # tag
    server_tag: Optional[str] = None
    # mcp server 是否启用
    applied: Optional[bool] = False
    # 授权自动执行
    execute_authorization: bool = False
    # mcp server 配置 env list
    env: Dict[str, str] = None
    # mcp server 配置 arg list
    args: List[str] = None
    # mcp server 配置 command
    command: str = None

    @classmethod
    def from_mcp_server(cls, mcp_server: MCPServer):
        return cls.model_validate(mcp_server.model_dump())

class MCPServerAppliedResultVo(BaseModel):
    # mcp server 名字
    server_name: str = None
    # 授权自动执行
    execute_authorization: bool = False
    # mcp server 配置 env list
    env: Dict[str, str] = None
    # mcp server 配置 arg list
    args: List[str] = None
    # mcp server 配置 command
    command: str = None

    @classmethod
    def from_mcp_server(cls, mcp_server: MCPServer):
        return cls.model_validate(mcp_server.model_dump())