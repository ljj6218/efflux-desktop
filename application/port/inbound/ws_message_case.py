from abc import ABC, abstractmethod


class WsMessageCase(ABC):

    @abstractmethod
    async def receive(self, message: str) -> None:
        """
        接受消息
        :param message:
        :return:
        """