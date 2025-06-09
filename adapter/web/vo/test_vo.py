from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class CachaVo(BaseModel):
    cacha_name: str
    cacha_key: str
    cacha_data: Any

class AgentVo(BaseModel):
    query: str
    generator_id: str
    client_id: str
    conversation_id: Optional[str] = None

class Message(BaseModel):
    role: str
    content: str

class PromptsVo(BaseModel):
    prompt: List[Message]
    generator_id: str