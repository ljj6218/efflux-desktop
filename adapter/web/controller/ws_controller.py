from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from application.port.inbound.ws_case import WsCase
from common.core.container.container import get_container

router = APIRouter(prefix="/api/web_socket", tags=["WS"])

def ws_case() -> WsCase:
    return get_container().get(WsCase)

async def handle_client_message(websocket: WebSocket, ws_manager: WsCase):
    """处理单个客户端的消息"""
    try:
        while True:
            message = await websocket.receive_text()
            print(f"收到消息: {message}")
            # 在这里可以处理消息或广播给其他客户端
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
        print("客户端断开连接")

# @router.websocket("/connection")
# async def websocket_endpoint(websocket: WebSocket, ws_manager: WsCase = Depends(ws_case)):
#     # """处理 WebSocket 连接"""
#     # await websocket.accept()
#     # set_cache("active_websocket_connection", websocket)
#     # # 异步处理该客户端的消息
#     # await handle_client_message(websocket)
#     """处理 WebSocket 连接"""
#     await ws_manager.connect(websocket)
#     try:
#         await handle_client_message(websocket, ws_manager=ws_manager)
#     except WebSocketDisconnect:
#         print("WebSocket 断开连接")