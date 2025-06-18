from pydantic import BaseModel

from typing import Optional, Dict, Any


class TeamsVo(BaseModel):
    query: str
    generator_id: str
    client_id: str
    agent_instance_id: str
    payload: Optional[Dict[str, Any]] = None
    conversation_id: Optional[str] = None