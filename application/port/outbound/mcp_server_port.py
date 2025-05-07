from abc import ABC, abstractmethod
from application.domain.mcp_server import MCPServer

class MCPServerPort(ABC):

    @abstractmethod
    def save(self, mcp_server: MCPServer):
        pass

    @abstractmethod
    def load(self, mcp_server: MCPServer):
        pass

    @abstractmethod
    def delete(self, mcp_server: MCPServer):
        pass

    @abstractmethod
    def load_all(self):
        pass