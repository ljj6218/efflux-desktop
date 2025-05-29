from application.port.outbound.ws_message_port import WsMessagePort
from common.utils.common_utils import set_cache, get_cache
from common.core.container.annotate import component

@component
class WsAdapter(WsMessagePort):

    async def send(self, message: str) -> None:
        """向所有连接的客户端广播消息"""
        if get_cache("active_websocket_connection"):
            await get_cache("active_websocket_connection").send_text(message)


    def check_connection(self) -> bool:
        if get_cache("active_websocket_connection"):
            return True
        return False