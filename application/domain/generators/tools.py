from enum import Enum
from pydantic import BaseModel
from typing import Any, Optional, List, Dict
from application.domain.events.event import Event
from application.domain.tasks.task import Task
import json

class ToolType(Enum):
    """
    工具类型
    """
    MCP="MCP"
    LOCAL="LOCAL"

class Tool(BaseModel):
    """
    工具定义
    """
    # The name of the mcp server
    mcp_server_name: Optional[str] = None
    group_name: Optional[str] = None
    # The name of the tool
    name: Optional[str]
    # A human-readable description of the tool
    description: Optional[str] = None
    # Tool call input
    input_schema: Optional[Dict[str, Any]] = None
    # type
    type: ToolType

    def instance(self) -> "ToolInstance":
        return ToolInstance(
            mcp_server_name=self.mcp_server_name,
            group_name=self.group_name,
            name=self.name,
            description=self.description,
            input_schema=self.input_schema,
            type=self.type,
        )

    def model_dump(self, **kwargs):
        # 使用 super() 获取字典格式
        data = super().model_dump()
        # 类型转换为字符串，用于持久化
        if 'type' in data:
            data['type'] = data['type'].value
        return data

class ToolInstance(Tool):
    """
    工具调用实例
    """
    conversation_id: Optional[str] = None
    dialog_segment_id: Optional[str] = None
    # Tool call instance ID
    tool_call_id: Optional[str] = None
    # args of the tool instance
    arguments: Optional[Dict[str, Any]] = None
    # results of the tool instance
    result: Optional[List[str]] = None

    # 自定义处理模型转化为字典的方法
    def model_dump(self, **kwargs):
        # 使用 super() 获取字典格式
        data = super().model_dump()
        # 类型转换为字符串，用于持久化
        # if 'type' in data:
        #     data['type'] = data['type']
        # 忽略字段
        if 'input_schema' in data:
            del data['input_schema']
        return data

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> List["ToolInstance"]:
        tool_call_list = []
        for tool_call in data['tool_calls']:
            tool_type = None
            if tool_call['mcp_server_name']:
                tool_type = ToolType.MCP
            if tool_call['group_name']:
                tool_type = ToolType.LOCAL
            tool_call_list.append(
                ToolInstance(
                    conversation_id=data['conversation_id'],
                    dialog_segment_id=data['dialog_segment_id'],
                    tool_call_id=tool_call['id'],
                    mcp_server_name=tool_call['mcp_server_name'],
                    group_name=tool_call['group_name'],
                    name=tool_call['name'],
                    type=tool_type,
                    description=tool_call['description'],
                    arguments=json.loads(tool_call['arguments']),
                )
            )
        return tool_call_list

    @classmethod
    def from_event_data(cls, event: Event) -> "List[ToolInstance]":
        return cls.from_dict(event.data)

    @classmethod
    def from_task_data(cls, task: Task) -> "List[ToolInstance]":
        return cls.from_dict(task.data)
