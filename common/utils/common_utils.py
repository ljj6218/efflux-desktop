import uuid
from typing import Dict, Any

def create_uuid() -> str:
    return str(uuid.uuid4())

# 缓存name标识
CONVERSATION_STOP_FLAG_KEY = "CONVERSATION_STOP_FLAG" # 会话停止标记
STREAM_STOP_FLAG_KEY = "STREAM_STOP_FLAG" # 流式对话片段停止标记
CURRENT_CONVERSATION_AGENT_INSTANCE_ID = "CURRENT_CONVERSATION_AGENT_INSTANCE_ID" # 当前会话agent_instance_id

# 常量
SINGLETON_WEBSOCKET_CLIENT_ID = "SINGLETON_CLIENT" # ws会话单例ID
