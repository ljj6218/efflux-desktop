from abc import ABC, abstractmethod
from application.domain.tasks.task import Task, TaskState

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

    @abstractmethod
    def state(self) -> TaskState:
        """
        获取当前状态
        :return:
        """

    @abstractmethod
    def set_state(self, state: TaskState):
        """
        设置当前状态
        :param state:
        :return:
        """

    @abstractmethod
    def check_stop_flag(self) -> bool:
        """
        检查停止点
        :return:
        """
    # @abstractmethod
    # def is_stopped(self) -> bool:
    #
    #
    # @abstractmethod
    # def is_running(self) -> bool: