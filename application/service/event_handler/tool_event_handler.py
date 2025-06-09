from application.domain.events.event import Event, EventType, EventSubType, EventSource
from application.domain.generators.chat_chunk.chunk import ChatStreamingChunk
from application.port.outbound.event_port import EventHandler
from application.port.outbound.task_port import TaskPort
from common.core.container.annotate import component
from common.core.errors.business_error_code import GeneratorErrorCode
from common.core.errors.business_exception import BusinessException
from common.utils.time_utils import create_from_second_now_to_int
from application.domain.tasks.task import Task, TaskType
from application.domain.generators.tools import ToolInstance
from application.domain.conversation import DialogSegment
from application.port.outbound.ws_message_port import WsMessagePort
from application.port.outbound.conversation_port import ConversationPort
from application.port.outbound.tools_port import ToolsPort
from typing import List, Dict, Any, Optional
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
                # 如果是单独的方法调用需要增加一个空的对话片段用于关联工具调用记录 PS：例如qwen这类模型
                if not dialog_segment:
                    self._send_null_message_to_ws(
                        client_id=event.client_id, conversation_id=event.data['conversation_id'],
                        dialog_segment_id=tool_instance.dialog_segment_id, generator_id=event.data['generator_id'],
                        payload=event.payload, model=event.data['model'])
                    assistant_dialog_segment = DialogSegment.make_assistant_message(
                        conversation_id=tool_instance.conversation_id, id=tool_instance.dialog_segment_id,
                        content="", reasoning_content=None, model=event.data['model'], timestamp=event.data['created'])
                    self.conversation_port.conversation_add(dialog_segment=assistant_dialog_segment)
                self.tools_port.save_instance(tool_instance)
                logger.info(f"保存工具调用实例记录--->{tool_instance.name} - {tool_instance.tool_call_id}")
            # 构建TOOL_CALL任务
            task = Task.from_singleton(task_type=TaskType.TOOL_CALL, data=event.data, payload=event.payload, client_id=event.client_id)
            TaskPort.get_task_port().execute_task(task)
            logger.info(f"事件处理器[{self.type()}]发起[{TaskType.TOOL_CALL}]任务：[ID：{task.id}]")
            # 发送ws消息
            logger.info(f"事件处理器[{self.type()}]异步推送ws消息：[ID：{event.id}]")
            self.ws_message_port.send(event)

        if event.sub_type == EventSubType.TOOL_CALL_RESULT:
            if 'context_message_list' not in event.payload:
                system = event.payload['system'] if 'system' in event.payload else None
                conversation_id = event.data['conversation_id']
                message_list = self._make_message_list(system=system, conversation_id=conversation_id)
                event.payload['context_message_list'] = message_list

            event.data['tools_call_result'] = True
            # 构建LLM_CALL任务
            task = Task.from_singleton(task_type=TaskType.LLM_CALL, data=event.data, payload=event.payload, client_id=event.client_id)
            TaskPort.get_task_port().execute_task(task)
            # ws返回
            self.ws_message_port.send(event)

    def type(self) -> str:
        return EventType.TOOL.value

    def _send_null_message_to_ws(self, client_id: str, conversation_id: str, dialog_segment_id: str, generator_id: str, model: str, payload: Dict[str, Any]):
        """用于前端对话片段和工具调用的成对展示"""
        event = Event.from_init(
            client_id=client_id,
            event_type=EventType.ASSISTANT_MESSAGE,
            event_sub_type=EventSubType.MESSAGE,
            source=EventSource.TOOL_EVENT_HANDLER,
            data={
                "id": dialog_segment_id,
                "conversation_id": conversation_id,
                "dialog_segment_id": dialog_segment_id,
                "generator_id": generator_id,
                "model": model,
                "content": "",
                "reasoning_content": "",
                "created": create_from_second_now_to_int(),
                "finish_reason": "stop"
            },
            payload=payload
        )
        self.ws_message_port.send(event)

    def _make_message_list(self, conversation_id: str, system: Optional[str] = None) -> List[ChatStreamingChunk]:
        # 查询会话历史
        history_conversation = self.conversation_port.conversation_load(conversation_id=conversation_id)
        if not history_conversation:
            raise BusinessException(error_code=GeneratorErrorCode.NO_CONVERSATION_FOUND,
                                    dynamics_message=conversation_id)
        # message 封装
        messages: List[ChatStreamingChunk] = []
        # 拼装系统提示词
        if system:
            messages.append(ChatStreamingChunk.from_system(system))
        # 拼装对话上下文
        history_message_list = history_conversation.convert_sort_memory()
        messages.extend(history_message_list)
        return messages