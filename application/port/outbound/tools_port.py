from abc import ABC, abstractmethod
from typing import List, Any
from application.domain.generators.tools import Tool, ToolInstance

class ToolsPort(ABC):

    @abstractmethod
    async def load_tools(self, server_name: str) -> List[Tool]:
        """
        按 mcp server 名字获取工具集合
        :param server_name:  mcp server名字
        :return: 工具集合
        """
        pass

    @abstractmethod
    async def call_tools(self, tool_instance: ToolInstance) -> dict[str, Any]:
        """
        工具调用
        :param tool_instance: 工具实例对象
        :return: 工具调用结果
        """
        pass