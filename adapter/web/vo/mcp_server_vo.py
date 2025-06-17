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
    # mcp server 是否启用
    enabled: Optional[bool] = True
    # tag
    server_tag: Optional[str] = None
    # 授权自动执行
    execute_authorization: Optional[bool] = False
    # mcp server 配置 env list
    env: Optional[Dict[str, Optional[str]]] = None
    # mcp server 配置 arg list
    args: Optional[List[str]] = None
    # mcp server 配置 command
    command: Optional[str] = None

    def convert_mcp_server(self) -> MCPServer:
        vo_dict = self.model_dump()
        if "env" in vo_dict.keys() and not vo_dict['env']:
            vo_dict['env'] = {}
        if "args" in vo_dict.keys() and not vo_dict["args"]:
            vo_dict["args"] = []
        return MCPServer.model_validate(vo_dict)

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
    env: Dict[str, Optional[str]] = None
    # mcp server 配置 arg list
    args: Optional[List[str]] = None
    # mcp server 配置 command
    command: Optional[str] = None

    @classmethod
    def from_mcp_server(cls, mcp_server: MCPServer):
        return cls.model_validate(mcp_server.model_dump())

class MCPServerAppliedResultVo(BaseModel):
    # mcp server 名字
    server_name: str = None
    # 授权自动执行
    execute_authorization: bool = False
    # mcp server 是否启用
    enabled: bool = True
    # mcp server 配置 env list
    env: Dict[str, str] = None
    # mcp server 配置 arg list
    args: List[str] = None
    # mcp server 配置 command
    command: Optional[str] = None

    @classmethod
    def from_mcp_server(cls, mcp_server: MCPServer):
        return cls.model_validate(mcp_server.model_dump())