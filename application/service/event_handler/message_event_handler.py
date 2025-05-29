from application.domain.events.event import EventType, Event
from application.domain.tasks.task import Task, TaskType
from application.port.inbound.event_handler import EventHandler
from common.core.container.annotate import component
from application.port.outbound.task_port import TaskPort
from application.domain.conversation import Conversation, DialogSegment
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
        # 创建会话
        if not event.data['conversation_id']:
            conversation = Conversation()
            conversation.init()
            conversation.theme = event.data['content']
            event.data['conversation_id'] = conversation.id
            self.conversation_port.conversation_save(conversation=conversation)
            logger.info(f"首次发送消息创建会话：[ID：{conversation.id} - 主题：{conversation.theme}]")
        else:
            logger.info(f"历史会话消息：[ID：{event.data['conversation_id']}]")
        # 保存用户输入
        user_dialog_segment = DialogSegment(conversation_id=event.data['conversation_id'], id=event.data["id"])
        user_dialog_segment.make_user_message(content=event.data['content'])
        self.conversation_port.conversation_add(dialog_segment=user_dialog_segment)
        logger.info(f"保存用户对话片段：[ID：{user_dialog_segment.id} - 内容：{user_dialog_segment.content}]")
        # 构建LLM_CALL任务
        task = Task.from_singleton(task_type=TaskType.LLM_CALL, data=event.data)
        TaskPort.get_task_port().execute_task(task)
        logger.info(f"事件处理器[{EventType.USER_MESSAGE}]发起[{TaskType.LLM_CALL}]任务：[ID：{task.id}]")

    def type(self) -> str:
        return EventType.USER_MESSAGE.value