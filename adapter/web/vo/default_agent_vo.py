from pydantic import BaseModel
from typing import Optional, List

class DefaultAgentVo(BaseModel):
    firm: str
    model: str
    system: Optional[str]
    query: str
    mcp_name_list: Optional[List[str]]