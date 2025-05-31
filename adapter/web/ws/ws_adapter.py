from application.port.outbound.ws_message_port import WsMessagePort
from application.port.inbound.ws_case import WsCase
from common.core.container.annotate import component
from common.core.connection_manager import manager, dispatcher
from common.utils.common_utils import SINGLETON_WEBSOCKET_CLIENT_ID
import json
import injector
import time

@component
class WsAdapter(WsMessagePort):

    def send(self, message: str) -> None:
        # """向所有连接的客户端广播消息"""
        # if get_cache("active_websocket_connection"):
        #     await get_cache("active_websocket_connection").send_text(message)
        # await self.ws_case.broadcast(message)
        # manager.send_to_threadsafe(client_id=SINGLETON_WEBSOCKET_CLIENT_ID, message=message)

        dispatcher.enqueue_message(client_id=SINGLETON_WEBSOCKET_CLIENT_ID, message=message)
