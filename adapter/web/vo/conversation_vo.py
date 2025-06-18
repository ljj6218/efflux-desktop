from pydantic import BaseModel
from typing import List

class DialogSegmentDelVo(BaseModel):
    id: str
    conversation_id: str

class ConversationDelVo(BaseModel):
    id_list: List[str]