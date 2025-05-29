from application.domain.events.event import Event, EventType, EventSubType
from application.port.outbound.event_port import EventHandler
from common.core.container.annotate import component
from common.core.logger import get_logger
from application.port.outbound.task_port import TaskPort
from application.domain.tasks.task import Task, TaskType
import json
import asyncio
import injector

logger = get_logger(__name__)

@component
class AgentCallEventHandler(EventHandler):


    def handle(self, event: Event) -> None:

        task = Task.from_singleton(task_type=TaskType.AGENT_CALL, data=event.data)
        TaskPort.get_task_port().execute_task(task=task)


    def type(self) -> str:
        return EventType.AGENT.value