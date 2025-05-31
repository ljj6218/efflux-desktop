from starlette.websockets import WebSocket

from common.core.container.annotate import component
from application.port.inbound.ws_case import WsCase
from typing import List
import asyncio

@component
class WsManager(WsCase):

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        """
            向所有客户端广播消息
        """
        # 创建一个任务列表
        tasks = []
        for connection in self.active_connections:
            # 为每个连接发送消息，采用异步并发发送
            tasks.append(self.send_message(message, connection))
        # 等待所有任务完成
        await asyncio.gather(*tasks)