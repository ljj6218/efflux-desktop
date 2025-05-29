from abc import ABC, abstractmethod

class WsMessagePort(ABC):

    @abstractmethod
    async def send(self, message: str) -> None:
        """
        发送消息
        :param message:
        :return:
        """

    @abstractmethod
    def check_connection(self) -> bool:
        """
        检查连接状态
        :return:
        """