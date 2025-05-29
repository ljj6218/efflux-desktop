from abc import ABC, abstractmethod
from application.domain.tasks.task import Task

class TaskHandler(ABC):
    """
    PS：为了避免循环依赖，在TaskHandler的实现类中禁止注入EventPort
    """

    @abstractmethod
    def execute(self, task: Task):
        """
        任务执行
        :param task: 任务对象
        :return:
        """

    @abstractmethod
    def type(self) -> str:
        """
        执行任务类型
        :return:
        """