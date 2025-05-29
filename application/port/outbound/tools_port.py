from abc import ABC, abstractmethod
from typing import List, Any, Optional
from application.domain.generators.tools import Tool, ToolInstance, ToolType

class ToolsPort(ABC):

    @abstractmethod
    def save_instance(self, tool_instance: ToolInstance) -> ToolInstance:
        """
        保存工具调用实例
        :param tool_instance: 工具调用实例
        :return:
        """

    @abstractmethod
    def load_instance(self,
                      conversation_id: Optional[str] = None,
                      agent_task_id: Optional[str] = None,
                      dialog_segment_id: Optional[str] = None,
                      tool_call_id: Optional[str] = None
                      ) -> List[ToolInstance]:
        """
        获取会话中的工具调用实例集合
        :param conversation_id: 会话id
        :param agent_task_id: agent 任务id
        :param dialog_segment_id: 对话片段id
        :param tool_call_id: 工具调用实例id
        :return:
        """

    @abstractmethod
    def update_instance(self, tool_instance: ToolInstance) -> Optional[ToolInstance]:
        """
        更新工具调用实例结果
        :param tool_instance: 工具调用实例
        :return:
        """

    @abstractmethod
    async def load_tools(self, group_name: str, tool_type: ToolType) -> List[Tool]:
        """
        按分组名字和类型获取工具集合
        :param group_name:  工具分组名字
        :param tool_type 工具类型
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