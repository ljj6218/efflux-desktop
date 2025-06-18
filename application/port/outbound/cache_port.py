from abc import ABC, abstractmethod
from typing import Any, Optional

class CachePort(ABC):

    @abstractmethod
    def set_data(self, name: str, key: str, value: Any) -> None:
        """手动设置缓存数据"""
        pass

    @abstractmethod
    def get_from_cache(self, name: str, key: str) -> Optional[Any]:
        """从缓存中获取数据，如果不存在，返回 None"""
        pass

    @abstractmethod
    def pop_from_cache(self, name: str, key: str) -> Optional[Any]:
        """从缓存中获取数据并弹出，如果不存在，返回 None"""
        pass

    @abstractmethod
    def delete_from_cache(self, name: str, key: str) -> None:
        """删除指定键的缓存数据"""
        pass

    @abstractmethod
    def clear_cache(self, name: str) -> None:
        """清除缓存中的所有数据"""
        pass

    @abstractmethod
    def cache_info(self, name: str) -> str:
        """获取当前缓存的信息"""
        pass