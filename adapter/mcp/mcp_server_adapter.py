from application.domain.mcp_server import MCPServer
from application.port.outbound.mcp_server_port import MCPServerPort
from common.core.container.annotate import component

@component
class MCPServerAdapter(MCPServerPort):

    def save(self, mcp_server: MCPServer):
        pass

    def load(self, mcp_server: MCPServer):
        pass

    def delete(self, mcp_server: MCPServer):
        pass

    def load_all(self):
        pass