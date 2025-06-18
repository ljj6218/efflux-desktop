from fastapi import WebSocket
from abc import ABC, abstractmethod

class WsCase(ABC):

    @abstractmethod
    async def connect(self, websocket: WebSocket):
        pass

    @abstractmethod
    def disconnect(self, websocket: WebSocket):
        pass

    @abstractmethod
    async def send_message(self, message: str, websocket: WebSocket):
        pass

    @abstractmethod
    async def broadcast(self, message: str):
        pass