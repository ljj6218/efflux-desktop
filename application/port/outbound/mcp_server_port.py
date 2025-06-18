from abc import ABC, abstractmethod
from application.domain.mcp_server import MCPServer
from typing import List, Optional

class MCPServerPort(ABC):

    @abstractmethod
    def apply(self, mcp_server: MCPServer) -> str:
        """
        应用mcp
        :param mcp_server:
        :return:
        """

    @abstractmethod
    def load(self, server_name: str) -> MCPServer:
        """
        获取mcp
        :param server_name:
        :return:
        """

    @abstractmethod
    def add(self, mcp_server: MCPServer) -> MCPServer:
        """
        添加mcp-server定义
        :param mcp_server:
        :return:
        """

    @abstractmethod
    def remove(self, server_name: str) -> str:
        """
        删除mcp-server定义
        :param server_name:
        :return:
        """


    @abstractmethod
    def load_applied(self, server_name: str) -> MCPServer:
        """
        获取已应用的mcp
        :param server_name:
        :return:
        """

    @abstractmethod
    def load_applied_list(self, server_name: Optional[str] = None) -> List[MCPServer]:
        """
        获取所有已应用的mcp
        :param server_name:
        :return:
        """

    @abstractmethod
    def load_enabled_list(self, server_name: Optional[str] = None) -> List[MCPServer]:
        """
        获取所有已启用的mcp
        :param server_name:
        :return:
        """

    @abstractmethod
    def cancel_apply(self, server_name: str) -> str:
        """
        取消指定mcp应用
        :param server_name:
        :return:
        """

    @abstractmethod
    def load_list(self, server_name: Optional[str] = None, server_tag: Optional[str] = None) -> List[MCPServer]:
        """
        获取所有的mcp
        :return:
        """

    @abstractmethod
    def is_authorized(self, server_name: str) -> str:
        """
        查询mcp server是否授权自动执行
        :param server_name: mcp server name
        :return: 是否授权
        """

    @abstractmethod
    def execute_authorization(self, server_name: str, execute_authorization: bool) -> str:
        """
        授权mcp server 自动执行
        :param server_name: mcp server name
        :param execute_authorization: 是否授权
        :return:
        """

    @abstractmethod
    def enabled(self, server_name: str, enabled: bool) -> str:
        """
        启用/禁用 mcp server
        :param server_name: mcp server name
        :param enabled: 是否启用
        :return:
        """