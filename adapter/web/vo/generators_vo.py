from pydantic import BaseModel
from typing import Optional, List, Literal
from application.domain.conversation import DialogSegmentContent

class TaskConfirm(BaseModel):
    id: str
    agent_id: Optional[str] = None
    confirm_type: Literal["text", "options"]
    confirm_content: Optional[str] = None

class GeneratorsVo(BaseModel):
    generator_id: str
    query: str | Optional[List[DialogSegmentContent]] = None
    system: Optional[str] = None
    conversation_id: Optional[str] = None
    mcp_name_list: Optional[List[str]] = None
    tools_group_name_list: Optional[List[str]] = None
    task_confirm: Optional[TaskConfirm] = None