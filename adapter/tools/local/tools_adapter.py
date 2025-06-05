from typing import Optional, List, Any
from application.domain.generators.tools import Tool, ToolInstance, ToolType
from adapter.tools.local.browser.browser_tools_definitions import default_tools


class LocalToolsAdapter:

    # def save_instance(self, tool_instance: ToolInstance) -> ToolInstance:
    #     pass
    #
    # def load_instance(self, conversation_id: Optional[str] = None,
    #                   agent_task_id: Optional[str] = None,
    #                   dialog_segment_id: Optional[str] = None,
    #                   tool_call_id: Optional[str] = None) -> List[ToolInstance]:
    #     pass
    #
    # def update_instance(self, tool_instance: ToolInstance) -> Optional[ToolInstance]:
    #     pass

    async def load_tools(self, group_name: str) -> List[Tool]:
        tool_list: List[Tool] = []
        if group_name == "browser":
            for default_tool in default_tools:
                tool_list.append(Tool(name=default_tool["name"], description=default_tool['description'],
                                      input_schema=default_tool['parameters'], group_name=group_name, type=ToolType.LOCAL))
        return tool_list

    async def call_tools(self, tool_instance: ToolInstance) -> dict[str, Any]:
        pass
