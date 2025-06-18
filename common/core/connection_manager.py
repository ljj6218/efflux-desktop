import asyncio
import threading
# connection_manager.py
class ConnectionManager:
    def __init__(self, loop):
        self.loop = loop
        self.active_connections: dict[str, object] = {}

    def register(self, client_id: str, websocket):
        self.active_connections[client_id] = websocket

    def unregister(self, client_id: str):
        self.active_connections.pop(client_id, None)

    def send_to_threadsafe(self, client_id: str, message: str):
        """从非 async 上下文 / 多线程中安全调用"""
        asyncio.run_coroutine_threadsafe(
            self.send_to(client_id, message),
            self.loop
        )

    async def send_to(self, client_id: str, message: str):
        websocket = self.active_connections.get(client_id)
        if websocket:
            await websocket.send(message)

    async def broadcast(self, message: str):
        for ws in self.active_connections.values():
            await ws.send(message)

# main.py
main_loop = asyncio.get_event_loop()
# ✅ 作为模块级单例
manager = ConnectionManager(main_loop)

class MessageDispatcher:
    def __init__(self):
        self.queue = asyncio.Queue()
        self.loop = None  # 主线程 loop
        self.thread_lock = threading.Lock()

    def start(self, loop):
        self.loop = loop
        # 启动异步消息处理协程
        asyncio.create_task(self._dispatch_loop())

    async def _dispatch_loop(self):
        while True:
            client_id, message = await self.queue.get()
            # 单点
            await manager.send_to(client_id, message)
            # 广播
            # await manager.broadcast(message)

    def enqueue_message(self, client_id, message):
        """线程安全地把消息加入主 loop 的 queue"""
        if not self.loop:
            raise RuntimeError("MessageDispatcher not started")
        self.loop.call_soon_threadsafe(self.queue.put_nowait, (client_id, message))

dispatcher = MessageDispatcher()