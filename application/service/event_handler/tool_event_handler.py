from application.domain.events.event import Event, EventType, EventSubType
from application.port.outbound.event_port import EventHandler
from application.port.outbound.task_port import TaskPort
from common.core.container.annotate import component
from application.domain.tasks.task import Task, TaskType
from application.domain.generators.tools import ToolInstance
from application.domain.conversation import DialogSegment
from application.port.outbound.ws_message_port import WsMessagePort
from application.port.outbound.conversation_port import ConversationPort
from application.port.outbound.tools_port import ToolsPort
from typing import List
from common.core.logger import get_logger
import json
import asyncio
import injector

logger = get_logger(__name__)

@component
class ToolEventHandler(EventHandler):


    @injector.inject
    def __init__(
        self,
        ws_message_port: WsMessagePort,
        conversation_port: ConversationPort,
        tools_port: ToolsPort,
    ):
        self.ws_message_port = ws_message_port
        self.conversation_port = conversation_port
        self.tools_port = tools_port

    def handle(self, event: Event) -> None:
        # 如果是工具调用事件，创建工具调用任务
        if event.sub_type == EventSubType.TOOL_CALL:
            # 保存工具调用实例
            for tool_instance in ToolInstance.from_event_data(event):
                dialog_segment: DialogSegment = self.conversation_port.dialog_segment_find(
                    conversation_id=tool_instance.conversation_id, dialog_segment_id=tool_instance.dialog_segment_id)
                # 如果是单独的方法调用需要增加一个空的对话片段用于关联工具调用记录
                if not dialog_segment:
                    assistant_dialog_segment = DialogSegment.make_assistant_message(
                        conversation_id=tool_instance.conversation_id, id=tool_instance.dialog_segment_id,
                        content="", reasoning_content=None, model=event.data['model'], timestamp=event.data['created'])
                    self.conversation_port.conversation_add(dialog_segment=assistant_dialog_segment)
                self.tools_port.save_instance(tool_instance)
                logger.info(f"保存工具调用实例记录--->{tool_instance.name} - {tool_instance.tool_call_id}")
            # 构建TOOL_CALL任务
            task = Task.from_singleton(task_type=TaskType.TOOL_CALL, data=event.data)
            TaskPort.get_task_port().execute_task(task)
            logger.info(f"事件处理器[{self.type()}]发起[{TaskType.TOOL_CALL}]任务：[ID：{task.id}]")
            # 发送ws消息
            logger.info(f"事件处理器[{self.type()}]异步推送ws消息：[ID：{event.id}]")
            self.ws_message_port.send(event.model_dump_json())

        if event.sub_type == EventSubType.TOOL_CALL_RESULT:
            event.data['tools_call_result'] = True
            # 构建LLM_CALL任务
            task = Task.from_singleton(task_type=TaskType.LLM_CALL, data=event.data)
            TaskPort.get_task_port().execute_task(task)
            # ws返回
            self.ws_message_port.send(event.model_dump_json())

    def type(self) -> str:
        return EventType.TOOL.value