from pydantic import BaseModel
from typing import Optional

class PPTVo(BaseModel):
    client_id: str
    generator_id: str
    query: Optional[str] = None
    conversation_id: str
    agent_instance_id: str
    dialog_segment_id: str
    html_code: str