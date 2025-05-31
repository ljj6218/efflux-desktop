from abc import ABC, abstractmethod
from application.domain.tasks.task import Task
from common.core.container.container import get_container

class TaskPort(ABC):

    @abstractmethod
    def execute_task(self, task: Task):
        pass

    def cancel_task(self, task_id: str) -> bool:
        pass

    @abstractmethod
    def shutdown(self):
        pass

    @classmethod
    def get_task_port(cls) -> "TaskPort":
        return get_container().get(TaskPort)