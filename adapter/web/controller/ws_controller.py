from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from common.utils.common_utils import set_cache, get_cache


router = APIRouter(prefix="/api/web_socket", tags=["WS"])


async def handle_client_message(websocket: WebSocket):
    """处理单个客户端的消息"""
    try:
        while True:
            message = await websocket.receive_text()
            print(f"收到消息: {message}")

    except WebSocketDisconnect:
        # 当客户端断开时，移除该连接
        set_cache("active_websocket_connection", None)
        print("客户端断开连接")


@router.websocket("/connection")
async def websocket_endpoint(websocket: WebSocket):
    """处理 WebSocket 连接"""
    await websocket.accept()
    set_cache("active_websocket_connection", websocket)
    # 异步处理该客户端的消息
    await handle_client_message(websocket)