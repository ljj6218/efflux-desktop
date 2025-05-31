from abc import ABC, abstractmethod

class WsMessagePort(ABC):

    @abstractmethod
    def send(self, message: str) -> None:
        """
        发送消息
        :param message:
        :return:
        """