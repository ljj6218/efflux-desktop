from pydantic import BaseModel
from typing import Optional, List, Dict, Any, Literal

class TaskConfirm(BaseModel):
    id: str
    agent_id: Optional[str] = None
    confirm_type: Literal["text", "options"]
    confirm_content: Optional[str] = None


class GeneratorsVo(BaseModel):
    generator_id: str
    query: Optional[str] = None
    conversation_id: Optional[str] = None
    mcp_name_list: Optional[List[str]] = None
    tools_group_name_list: Optional[List[str]] = None
    task_confirm: Optional[TaskConfirm] = None