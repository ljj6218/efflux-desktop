from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class PPTVo(BaseModel):
    generator_id: str
    query: Optional[str] = None
    conversation_id: Optional[str] = None
    mcp_name_list: Optional[List[str]] = None
    task_confirm: Optional[Dict[str, Any]] = None