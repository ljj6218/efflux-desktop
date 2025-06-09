from application.domain.tasks.task import TaskType, Task, TaskState
from application.domain.events.event import EventType, Event, EventSubType, EventSource
from application.port.outbound.event_port import EventPort
from application.port.inbound.task_handler import TaskHandler
from common.core.container.annotate import component
from application.port.outbound.tools_port import ToolsPort
from application.port.outbound.mcp_server_port import MCPServerPort
from application.domain.generators.tools import ToolInstance
from common.core.logger import get_logger
from typing import Optional, Set, List, Dict, Any
import json
import asyncio
import injector

logger = get_logger(__name__)

@component
class ToolTaskHandler(TaskHandler):

    @injector.inject
    def __init__(self, tools_port: ToolsPort, mcp_server_port: MCPServerPort):
        self.tools_port = tools_port
        self.mcp_server_port = mcp_server_port

    def execute(self, task: Task):
        logger.info(f"工具调用任务：[任务：{task.id} - tool_id:{task.data['id']}]")
        # 收集未授权自动运行的mcp
        unauthorized_mcp_server_names: Set[str] = set()
        for tool_call in task.data['tool_calls']:
            if not self.mcp_server_port.is_authorized(tool_call['mcp_server_name']):
                unauthorized_mcp_server_names.add(tool_call['mcp_server_name'])
        # 判断是否有未授权的mcp server
        if len(unauthorized_mcp_server_names) > 0:
            # 判断用户是否确认工具使用

            # 发送用户授权请求事件

            # TODO
            # tool_call_list = []
            # for tool_call in task.data.tool_calls:
            #     tool_call_list.append(
            #         ToolCalls.from_init(id=tool_call.id, mcp_server_name=tool_call.mcp_server_name, name=tool_call.name,
            #                             arguments=tool_call.arguments))
            # event = Event.from_init(
            #     event_type=EventType.ASSISTANT_MESSAGE,
            #     event_data=ToolCallsEventData.from_tool_calls(id=task.data.id, model=task.data.model, conversation_id=task.data.conversation_id,
            #                                                   created=task.data.created, tool_calls=tool_call_list))
            # EventPort.get_event_port().emit_event()
            return
        else:
            tool_call_list: List[ToolInstance] = ToolInstance.from_task_data(task)
            asyncio.run(self._tools_call(tool_call_list))
            # 工具调用结果
            # 封装工具调用结果事件的工具结果
            event_tool_calls: List[Dict[str, Any]] = []
            for tool_call in tool_call_list:
                logger.info(f"工具调用结果：[{tool_call.mcp_server_name} - {tool_call.name} - {tool_call.tool_call_id} - {tool_call.arguments} - 结果：略]")
                # 转字典
                event_tool_calls.append(tool_call.model_dump())
            # 发送工具调用结果事件
            event = Event.from_init(
                client_id=task.client_id,
                event_type=EventType.TOOL,
                event_sub_type=EventSubType.TOOL_CALL_RESULT,
                source=EventSource.TOOL_HANDLER,
                data={
                    'id': task.data['id'],
                    'model': task.data['model'],
                    'dialog_segment_id':task.data['dialog_segment_id'],
                    'conversation_id': task.data['conversation_id'],
                    'generator_id': task.data['generator_id'],
                    'created': task.data['created'],
                    'tool_calls': event_tool_calls
                },
                payload=task.payload
            )
            logger.info(f"任务处理器[{self.type()}]发起[{event.type} - {event.sub_type}]事件：[ID：{event.id}]")
            EventPort.get_event_port().emit_event(event)

    def type(self) -> str:
        return TaskType.TOOL_CALL.value

    def state(self) -> TaskState:
        pass

    def set_state(self, state: TaskState):
        pass

    def check_stop_flag(self) -> bool:
        pass


    async def _tools_call(self, tool_call_list: List[ToolInstance]):
        tool_call_task_list = []
        for tool_call in tool_call_list:
            tool_call_task_list.append(self.tools_port.call_tools(tool_call))
            logger.info(f"需要调用工具：{tool_call.tool_call_id}-{tool_call.name}-{tool_call.arguments}")
        results = await asyncio.gather(*tool_call_task_list)
        logger.debug(f"工具调用结果：{results}")
        for tool_call_result in results:
            for tool_call in tool_call_list:
                if tool_call.tool_call_id == tool_call_result['id']:
                    tool_call.result = tool_call_result['result']
                    # 更新工具调用实例记录的结果
                    self.tools_port.update_instance(tool_call)