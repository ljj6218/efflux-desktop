from pydantic import BaseModel
from typing import Optional, Literal, Dict, Any


class ConfirmVo(BaseModel):
    client_id: str
    generator_id: str
    query: Optional[str] = None
    conversation_id: str
    agent_instance_id: str
    dialog_segment_id: str
    confirm_type: Literal["ppt", "tools_execute"]
    content: Dict[str, Any]