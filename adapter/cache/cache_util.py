from cachetools import LRUCache, cached
from typing import Any, Callable, Optional, Dict


class CacheUtil:
    def __init__(self, maxsize: int = 100):
        """初始化缓存工具，设置缓存的最大大小"""
        self.cache = LRUCache(maxsize)

    def set_data(self, key: str, value: Any) -> None:
        """手动设置缓存数据"""
        self.cache[key] = value

    def get_from_cache(self, key: str) -> Optional[Any]:
        """从缓存中获取数据，如果不存在，返回 None"""
        return self.cache.get(key)

    def pop_from_cache(self, key: str) -> Optional[Any]:
        """从缓存中获取数据并弹出，如果不存在，返回 None"""
        if key in self.cache:
            return self.cache.pop(key)
        return None

    def delete_from_cache(self, key: str) -> None:
        """删除指定键的缓存数据"""
        if key in self.cache:
            del self.cache[key]  # 从缓存中删除指定的键

    def clear_cache(self) -> None:
        """清除缓存中的所有数据"""
        self.cache.clear()

    def cache_info(self) -> Dict[str, Any]:
        """获取当前缓存的信息"""
        return {
            "cache_size": len(self.cache),
            "max_size": self.cache.maxsize,
            "items": list(self.cache.items())
        }