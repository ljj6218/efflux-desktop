from abc import ABC, abstractmethod
from application.domain.events.event import Event

class EventHandler(ABC):
    """
    PS：为了避免循环依赖，在EventHandler的实现类中禁止注入TaskPort
    """

    @abstractmethod
    def handle(self, event: Event) -> None:
        """
        处理事件
        :param event:
        :return:
        """
        
    @abstractmethod
    def type(self) -> str:
        """
        处理事件类型
        :return:
        """