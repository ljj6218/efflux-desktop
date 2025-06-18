from abc import ABC, abstractmethod

from application.domain.events.event import Event


class WsMessagePort(ABC):

    @abstractmethod
    def send(self, event: Event) -> None:
        """
        发送消息
        :param message:
        :return:
        """