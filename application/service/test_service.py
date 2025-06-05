from application.domain.tasks.task import Task, TaskType
from application.domain.conversation import Conversation
from application.port.outbound.conversation_port import ConversationPort
from common.core.container.annotate import component
from application.port.outbound.task_port import TaskPort
from application.port.inbound.test_case import TestCase
from application.port.outbound.event_port import EventPort
from application.port.outbound.cache_port import CachePort
from application.domain.events.event import Event, EventType, EventSubType
import injector
from common.utils.common_utils import create_uuid, CONVERSATION_STOP_FLAG_KEY
from common.core.logger import get_logger
from typing import Optional, List

logger = get_logger(__name__)


@component
class TestService(TestCase):

    @injector.inject
    def __init__(
        self,
        task_manager: TaskPort,
        conversation_port: ConversationPort,
        cache_port: CachePort,
        event_port: EventPort,
    ):
        self.task_manager = task_manager
        self.conversation_port = conversation_port
        self.cache_port = cache_port
        self.event_port = event_port

    async def test_task(self):
        task = Task.from_singleton(task_type=TaskType.LLM_CALL, data={})
        self.task_manager.execute_task(task=task)

    async def test_task_stop(self, task_id: str) -> bool:
        return self.task_manager.cancel_task(task_id=task_id)

    async def test_call_agent(self, query: str, generator_id: str, conversation_id: Optional[str] = None) -> tuple[str | None, str]:
        query_str = None
        if isinstance(query, List):
            for item in query:
                if item.type == 'text':
                    query_str = item.content
        # 创建会话
        if not conversation_id:
            conversation = Conversation()
            conversation.init()
            conversation.theme = query_str
            conversation.dialog_segment_list = []
            self.conversation_port.conversation_save(conversation=conversation)
            conversation_id = conversation.id
            logger.info(f"首次发送消息创建会话：[ID：{conversation.id} - 主题：{conversation.theme}]")
        else:
            logger.info(f"历史会话消息：[ID：{conversation_id}]")
        uuid = create_uuid()
        # 清除会话的停止状态
        self.cache_port.set_data(name=CONVERSATION_STOP_FLAG_KEY, key=conversation_id, value=False)
        event = Event.from_init(
            event_type=EventType.AGENT,
            event_sub_type=EventSubType.AGENT_CALL,
            data={
                "id": uuid,
                "agent_id": "4877f996-2fb5-400d-9b26-245a824e325f",
                "conversation_id": conversation_id,
                "generator_id": generator_id,
                "content": query,
            }
        )
        logger.info(f"[GeneratorService]发起[{EventType.AGENT} - {EventSubType.AGENT_CALL}]事件：[ID：{event.id}]")
        self.event_port.emit_event(event)
        return conversation_id, uuid