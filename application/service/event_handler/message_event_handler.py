from application.domain.events.event import EventType, Event
from application.domain.tasks.task import Task, TaskType
from application.port.inbound.event_handler import EventHandler
from common.core.container.annotate import component
from application.port.outbound.task_port import TaskPort
from application.domain.conversation import DialogSegment
from application.port.outbound.conversation_port import ConversationPort
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
        # 保存用户输入
        user_dialog_segment = DialogSegment.make_user_message(
            content=event.data['content'], conversation_id=event.data['conversation_id'], id=event.data["dialog_segment_id"])
        self.conversation_port.conversation_add(dialog_segment=user_dialog_segment)
        logger.info(f"保存用户对话片段：[ID：{user_dialog_segment.id} - 内容：{user_dialog_segment.content}]")
        # 构建LLM_CALL任务
        task = Task.from_singleton(task_type=TaskType.LLM_CALL, data=event.data)
        TaskPort.get_task_port().execute_task(task)
        logger.info(f"事件处理器[{EventType.USER_MESSAGE}]发起[{TaskType.LLM_CALL}]任务：[ID：{task.id}]")

    def type(self) -> str:
        return EventType.USER_MESSAGE.value