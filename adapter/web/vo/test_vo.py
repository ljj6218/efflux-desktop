from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class CachaVo(BaseModel):
    cacha_name: str
    cacha_key: str
    cacha_data: Any