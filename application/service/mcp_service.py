from typing import List, Optional

import injector
from common.core.container.annotate import component
from application.domain.mcp_server import MCPServer
from application.port.inbound.mcp_server_case import McpServerCase
from application.port.outbound.mcp_server_port import MCPServerPort

@component
class McpServerService(McpServerCase):

    @injector.inject
    def __init__(self, mcp_server_port: MCPServerPort):
        self.mcp_server_port = mcp_server_port

    async def apply(self, mcp_server: MCPServer) -> str:
        return self.mcp_server_port.apply(mcp_server)

    async def load(self, server_name: str) -> MCPServer:
        return self.mcp_server_port.load(server_name)

    async def load_applied(self, server_name: str) -> MCPServer:
        return self.mcp_server_port.load_applied(server_name)

    async def load_applied_list(self, server_name: Optional[str] = None) -> List[MCPServer]:
        return self.mcp_server_port.load_applied_list(server_name)

    async def load_enabled_list(self, server_name: Optional[str] = None) -> List[MCPServer]:
        return self.mcp_server_port.load_enabled_list(server_name)

    async def cancel_apply(self, server_name: str) -> str:
        return self.mcp_server_port.cancel_apply(server_name)

    async def load_list(self, server_name: Optional[str] = None, server_tag: Optional[str] = None) -> List[MCPServer]:
        return self.mcp_server_port.load_list(server_name=server_name, server_tag=server_tag)

    async def execute_authorization(self, server_name: str, execute_authorization: bool) -> str:
        return self.mcp_server_port.execute_authorization(server_name=server_name, execute_authorization=execute_authorization)

    async def enabled(self, server_name: str, enabled: bool) -> str:
        return self.mcp_server_port.enabled(server_name=server_name, enabled=enabled)