from fastapi import FastAPI
import os
import pkgutil
from importlib import import_module
from fastapi.middleware.cors import CORSMiddleware
from common.core.logger import get_logger, LOGGING_CONFIG
from common.core.container.container import get_container
from common.core.connection_manager import manager, dispatcher
from adapter.web.core.exception_registry import register_exception_handlers
from application.port.outbound.task_port import TaskPort
from application.port.outbound.event_port import EventPort
from application.port.outbound.cache_port import CachePort
from common.utils.common_utils import CONVERSATION_STOP_FLAG_KEY, SINGLETON_WEBSOCKET_CLIENT_ID, create_uuid, \
    CURRENT_CONVERSATION_AGENT_INSTANCE_ID
import uvicorn
import copy
import asyncio

logger = get_logger(__name__)
app = FastAPI()

async def startup():
    logger.info("app启动")
    # 启动容器
    get_container()
    # 设置会话停止缓存
    get_container().get(CachePort).set_data(name=CONVERSATION_STOP_FLAG_KEY, key="test", value=False)
    get_container().get(CachePort).set_data(name=CURRENT_CONVERSATION_AGENT_INSTANCE_ID, key="test", value=False)

async def shutdown():
    logger.info("app关闭")
    # 关闭task线程池
    get_container().get(TaskPort).shutdown()
    # 关闭事件总线
    get_container().get(EventPort).shutdown()

app.add_event_handler("startup", startup)
app.add_event_handler("shutdown", shutdown)
# 注册异常控制器
register_exception_handlers(app)

# origins = [
#     "http://127.0.0.1:3003",
#     "http://127.0.0.1:3000",
#     "http://127.0.0.1",
#     "http://47.236.204.213:3003",
#     "http://47.236.204.213:3000",
#     "http://47.236.204.213",
#     "http://47.236.204.213:3003",
#     "http://localhost:3000",
#     "http://localhost",
# ]

origins = [
    "*"
]

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # 允许所有源，或者指定特定源
    allow_credentials=False,
    allow_methods=["*"],  # 允许所有方法
    allow_headers=["*"],  # 允许所有头
)


def include_routers_from_package(package_name: str):
    """扫描指定包，动态导入所有模块，并注册路由
    
    Args:
        package_name: 包名，例如 'adapter.web.controller'
    """
    try:
        # 尝试直接导入包
        package = import_module(package_name)
        package_path = os.path.dirname(os.path.abspath(package.__file__))
        
        # 获取包中所有模块
        modules = []
        for item in os.listdir(package_path):
            full_path = os.path.join(package_path, item)
            # 跳过 __pycache__ 目录和非 .py 文件
            if item == '__pycache__' or not item.endswith('.py') or item.startswith('__'):
                continue
            module_name = item[:-3]  # 移除 .py 后缀
            modules.append(module_name)
        
        # 导入模块并注册路由
        for module_name in modules:
            try:
                full_module_name = f"{package_name}.{module_name}"
                module = import_module(full_module_name)
                if hasattr(module, 'router'):
                    app.include_router(module.router)
                    print(f"Successfully registered router from {full_module_name}")
            except Exception as e:
                print(f"Error importing {module_name}: {str(e)}")
                continue
                
    except Exception as e:
        print(f"Error in include_routers_from_package: {str(e)}")
        import traceback
        traceback.print_exc()

# 扫描指定包下的所有controller
include_routers_from_package('adapter.web.controller')

# # 程序入口
# if __name__ == "__main__":
#     # 配置 uvicorn 使用项目的日志配置
#     # 从 uvicorn 获取默认日志配置
#     uvicorn_log_config = copy.deepcopy(LOGGING_CONFIG)
#
#     # 确保 uvicorn 相关的日志器使用我们的配置
#     for logger_name in ['uvicorn', 'uvicorn.error', 'uvicorn.access']:
#         if logger_name not in uvicorn_log_config['loggers']:
#             uvicorn_log_config['loggers'][logger_name] = {
#                 'handlers': ['console', 'file'],
#                 'level': 'INFO',
#                 'propagate': False,
#             }
#
#     uvicorn.run("main:app",
#                 host="0.0.0.0",
#                 port=8000,
#                 workers=1,
#                 reload=False,
#                 log_level="info",
#                 log_config=uvicorn_log_config)

# # 停止服务的接口
# @app.post("/shutdown")
# async def shutdown_service():
#     logger.info("即将关闭服务...")
#     # 停止 WebSocket 服务器和 Uvicorn 服务器
#     stop_event.set()  # 停止事件
#
#     return {"message": "服务正在关闭"}
#
# # 在主程序中管理这些服务
# stop_event = asyncio.Event()

from websockets import serve

async def ws_handler(websocket):
    # 假设你在路径参数中指定了 client_id，例如 ws://localhost:8765/ws?client_id=abc
    query = dict((kv.split("=") for kv in websocket.request.path.split("?")[1].split("&")))
    client_id = query.get("client_id", create_uuid())
    # client_id = SINGLETON_WEBSOCKET_CLIENT_ID
    # client_id = create_uuid()
    manager.register(client_id, websocket)
    logger.info(f"connection open -> client_id[{client_id}]")
    try:
        async for message in websocket:
            print(f"Received from {client_id}: {message}")
            await websocket.send(f"Echo: {message}")
    except Exception as e:
        logger.error(f"Connection error: {e}")
    finally:
        logger.info(f"connection close -> client_id[{client_id}]")
        manager.unregister(client_id)

# 同时启动 FastAPI 和 WebSocket
async def main():
    # 1. 自定义 WebSocket server（关闭压缩）
    # ws_server = await serve(ws_handler, "0.0.0.0", 8765, compression=None, ping_interval=None)

    ws_server = await serve(ws_handler, "0.0.0.0", 8765, ping_interval=None)

    # 获取当前事件循环
    loop = asyncio.get_running_loop()

    # 启动消息派发器
    dispatcher.start(loop)

    # 2. 启动 FastAPI 应用（通过 uvicorn）
    uvicorn_log_config = copy.deepcopy(LOGGING_CONFIG)
    for logger_name in ['uvicorn', 'uvicorn.error', 'uvicorn.access']:
        if logger_name not in uvicorn_log_config['loggers']:
            uvicorn_log_config['loggers'][logger_name] = {
                'handlers': ['console'],
                'level': 'INFO',
                'propagate': False,
            }

    config = uvicorn.Config(
        app=app,
        host="0.0.0.0",
        port=8000,
        workers=1,
        reload=True,
        log_level="info",
        log_config=uvicorn_log_config
    )
    server = uvicorn.Server(config)

    # 并发运行两个服务
    await asyncio.gather(
        server.serve(),
        ws_server.wait_closed(),  # 保持 WebSocket 运行
    )

    # # 等待停止事件，终止应用
    # await stop_event.wait()  # 当停止事件被触发，进程将结束
    #
    # # 执行 shutdown 操作
    # await shutdown()

if __name__ == "__main__":
    asyncio.run(main())