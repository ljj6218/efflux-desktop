from datetime import datetime

from pydantic import BaseModel
from typing import Optional

class Conversation(BaseModel):
    """chat bot 会话对象"""

    # 会话ID
    id: Optional[str] = None
    # 会话主题
    theme: Optional[str] = None
    # 创建时间
    created: Optional[datetime] = None
    # 当前会话最大长度
    max_length: int = 50

