from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class DefaultAgentVo(BaseModel):
    generator_id: str
    system: Optional[str] = None
    query: str
    conversation_id: Optional[str] = None
    mcp_name_list: Optional[List[str]] = None
    user_confirm: Optional[Dict[str, Any]] = None