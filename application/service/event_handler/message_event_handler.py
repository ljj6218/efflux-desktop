from typing import List, Optional

from application.domain.events.event import EventType, Event
from application.domain.generators.chat_chunk.chunk import ChatStreamingChunk
from application.domain.tasks.task import Task, TaskType
from application.port.inbound.event_handler import EventHandler
from common.core.container.annotate import component
from application.port.outbound.task_port import TaskPort
from application.port.outbound.conversation_port import ConversationPort
from common.core.errors.business_error_code import GeneratorErrorCode
from common.core.errors.business_exception import BusinessException
from common.core.logger import get_logger
import injector

logger = get_logger(__name__)

@component
class MessageEventHandler(EventHandler):
    """
    用户事件处理器-普通消息
    """
    @injector.inject
    def __init__(self, conversation_port: ConversationPort):
        self.conversation_port = conversation_port

    def handle(self, event: Event) -> None:
        if 'context_message_list' not in event.payload:
            system = event.payload['system'] if 'system' in event.payload else None
            conversation_id = event.data['conversation_id']
            message_list = self._make_message_list(system=system, conversation_id=conversation_id)
            event.payload['context_message_list'] = message_list
        # 构建LLM_CALL任务
        task = Task.from_singleton(task_type=TaskType.LLM_CALL, data=event.data, payload=event.payload, client_id=event.client_id)
        TaskPort.get_task_port().execute_task(task)
        logger.info(f"事件处理器[{EventType.USER_MESSAGE}]发起[{TaskType.LLM_CALL}]任务：[ID：{task.id}]")

    def type(self) -> str:
        return EventType.USER_MESSAGE.value

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