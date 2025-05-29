from typing import Any, List, Optional

from application.domain.generators.tools import ToolInstance, Tool, ToolType
from application.port.outbound.tools_port import ToolsPort
from common.core.container.annotate import component
from adapter.tools.mcp.tools_adapter import McpToolsAdapter
from adapter.tools.local.tools_adapter import LocalToolsAdapter


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

    def save_instance(self, tool_instance: ToolInstance) -> ToolInstance:
        if tool_instance.type == ToolType.MCP:
            return self.mcp_tools_adapter.save_instance(tool_instance)
        if tool_instance.type == ToolType.LOCAL:
            return self.local_tools_adapter.save_instance(tool_instance)

    def load_instance(self, conversation_id: Optional[str] = None,
                      agent_task_id: Optional[str] = None,
                      dialog_segment_id: Optional[str] = None,
                      tool_call_id: Optional[str] = None) -> List[ToolInstance]:
        if conversation_id:
            return self.mcp_tools_adapter.load_instance(conversation_id=conversation_id, dialog_segment_id=dialog_segment_id, tool_call_id=tool_call_id)
        if agent_task_id:
            return self.local_tools_adapter.load_instance(agent_task_id=agent_task_id, dialog_segment_id=dialog_segment_id, tool_call_id=tool_call_id)

    def update_instance(self, tool_instance: ToolInstance) -> Optional[ToolInstance]:
        if tool_instance.type == ToolType.MCP:
            return self.mcp_tools_adapter.update_instance(tool_instance)
        if tool_instance.type == ToolType.LOCAL:
            return self.local_tools_adapter.update_instance(tool_instance)

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