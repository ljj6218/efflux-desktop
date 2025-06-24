from typing import Any, List, Optional

from application.domain.generators.tools import ToolInstance, Tool, ToolType
from application.port.outbound.tools_port import ToolsPort
from common.core.container.annotate import component
from common.utils.file_util import check_file_and_create, check_file
from adapter.tools.mcp.tools_adapter import McpToolsAdapter
from adapter.tools.local.tools_adapter import LocalToolsAdapter

import jsonlines
import injector

@component
class ToolsManager(ToolsPort):

    @injector.inject
    def __init__(
        self,
        mcp_tools_adapter: McpToolsAdapter,
        local_tools_adapter: LocalToolsAdapter,
    ):
        self.mcp_tools_adapter = mcp_tools_adapter
        self.local_tools_adapter = local_tools_adapter
        self.tool_calls_file_pre_url = "conversations/tool_calls_record/"

    def save_instance(self, tool_instance: ToolInstance) -> ToolInstance:
        tool_calls_file = f"{self.tool_calls_file_pre_url}{tool_instance.conversation_id}.jsonl"
        check_file_and_create(tool_calls_file)
        with jsonlines.open(tool_calls_file, mode='a') as writer:
            writer.write(tool_instance.model_dump())
        return tool_instance

    def load_instance(self,
                      conversation_id: str,
                      dialog_segment_id: Optional[str] = None,
                      tool_call_id: Optional[str] = None
                      ) -> List[ToolInstance]:
        tool_calls_file = f"{self.tool_calls_file_pre_url}{conversation_id}.jsonl"
        tool_calls_list: List[ToolInstance] = []
        if check_file(tool_calls_file):
            with jsonlines.open(tool_calls_file, mode='r') as reader:
                for obj in reader:
                    if dialog_segment_id is None and tool_call_id is None:
                        tool_calls_list.append(ToolInstance.model_validate(obj))
                    if obj['dialog_segment_id'] == dialog_segment_id:
                        tool_calls_list.append(ToolInstance.model_validate(obj))
                    if tool_call_id and obj['tool_call_id'] == tool_call_id:
                        tool_calls_list.append(ToolInstance.model_validate(obj))
        return tool_calls_list

    def update_instance(self, tool_instance: ToolInstance) -> Optional[ToolInstance]:
        tool_calls_file = f"{self.tool_calls_file_pre_url}{tool_instance.conversation_id}.jsonl"
        updated = False
        updated_instance_list = []  # 用于存储更新后的工具实例
        with jsonlines.open(tool_calls_file, mode='r') as reader:
            # 读取所有现有的工具实例
            for obj in reader:
                old_tool_instance = ToolInstance.model_validate(obj)
                if old_tool_instance and old_tool_instance.tool_call_id == tool_instance.tool_call_id:
                    # 更新目标工具实例
                    old_tool_instance.result = tool_instance.result
                    updated = True
                # 将修改后的工具实例添加到列表中
                updated_instance_list.append(old_tool_instance)
        # 如果找到了匹配的工具实例并进行了更新
        if updated:
            # 将所有更新后的工具实例重新写入到 JSONL 文件
            with jsonlines.open(tool_calls_file, mode='w') as writer:
                for updated_instance in updated_instance_list:
                    writer.write(updated_instance.model_dump())  # 将对象写为字典
            return tool_instance  # 返回更新后的工具实例对象
        else:
            return None  # 如果没有找到匹配的工具实例对象，则返回 None

    # def save_instance(self, tool_instance: ToolInstance) -> ToolInstance:
    #     if tool_instance.type == ToolType.MCP:
    #         return self.mcp_tools_adapter.save_instance(tool_instance)
    #     if tool_instance.type == ToolType.LOCAL:
    #         return self.local_tools_adapter.save_instance(tool_instance)
    #
    # def load_instance(self, conversation_id: Optional[str] = None,
    #                   agent_task_id: Optional[str] = None,
    #                   dialog_segment_id: Optional[str] = None,
    #                   tool_call_id: Optional[str] = None) -> List[ToolInstance]:
    #     if conversation_id:
    #         return self.mcp_tools_adapter.load_instance(conversation_id=conversation_id, dialog_segment_id=dialog_segment_id, tool_call_id=tool_call_id)
    #     if agent_task_id:
    #         return self.local_tools_adapter.load_instance(agent_task_id=agent_task_id, dialog_segment_id=dialog_segment_id, tool_call_id=tool_call_id)
    #
    # def update_instance(self, tool_instance: ToolInstance) -> Optional[ToolInstance]:
    #     if tool_instance.type == ToolType.MCP:
    #         return self.mcp_tools_adapter.update_instance(tool_instance)
    #     if tool_instance.type == ToolType.LOCAL:
    #         return self.local_tools_adapter.update_instance(tool_instance)

    async def load_tools(self, group_name: str, tool_type: ToolType) -> List[Tool]:
        if tool_type == ToolType.MCP:
            return await self.mcp_tools_adapter.load_tools(mcp_server_name=group_name)
        if tool_type == ToolType.LOCAL:
            return await self.local_tools_adapter.load_tools(group_name=group_name)

    async def call_tools(self, tool_instance: ToolInstance) -> dict[str, Any]:
        if tool_instance.type == ToolType.MCP:
            return await self.mcp_tools_adapter.call_tools(tool_instance)
        if tool_instance.type == ToolType.LOCAL:
            return await self.local_tools_adapter.call_tools(tool_instance)