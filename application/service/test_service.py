from application.domain.tasks.task import Task, TaskType
from common.core.container.annotate import component
from application.port.outbound.task_port import TaskPort
from application.port.inbound.test_case import TestCase
import injector

@component
class TestService(TestCase):

    @injector.inject
    def __init__(self, task_manager: TaskPort):
        self.task_manager = task_manager

    async def test_task(self):
        task = Task.from_singleton(task_type=TaskType.LLM_CALL, data={})
        self.task_manager.execute_task(task=task)

    async def test_task_stop(self, task_id: str) -> bool:
        return self.task_manager.cancel_task(task_id=task_id)

    def test(self):
        print("1111")