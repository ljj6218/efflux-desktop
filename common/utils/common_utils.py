import uuid
from typing import Dict, Any

cache_map: Dict[str,Any] = {}

def create_uuid() -> str:
    return str(uuid.uuid4())

def set_cache(key: str, value: Any) -> None:
    cache_map[key] = value

def get_cache(key: str) -> Any:
    return cache_map.get(key)
