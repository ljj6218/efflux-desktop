from typing import Optional, Any, Dict

from common.core.container.annotate import component
from application.port.outbound.cache_port import CachePort
from adapter.cache.cache_util import CacheUtil
from common.core.errors.common_error_code import CommonErrorCode
from common.core.errors.common_exception import CommonException

@component
class CacheAdapter(CachePort):

    def __init__(self):
        self.cache_map: Dict[str, CacheUtil] = {}

    def set_data(self, name: str, key: str, value: Any) -> None:
        if name not in self.cache_map:
            self.cache_map[name] = CacheUtil()
        self.cache_map[name].set_data(key, value)

    def get_from_cache(self, name: str, key: str) -> Optional[Any]:
        if name not in self.cache_map:
            raise CommonException(error_code=CommonErrorCode.CACHE_NOT_FOUND, dynamics_message=name)
        return self.cache_map[name].get_from_cache(key)

    def pop_from_cache(self, name: str, key: str) -> Optional[Any]:
        if name not in self.cache_map:
            raise CommonException(error_code=CommonErrorCode.CACHE_NOT_FOUND, dynamics_message=name)
        """从缓存中获取数据并弹出，如果不存在，返回 None"""
        return self.cache_map[name].pop_from_cache(key)

    def delete_from_cache(self, name: str, key: str) -> None:
        """删除指定键的缓存数据"""
        if name in self.cache_map:
            return self.cache_map[name].delete_from_cache(key)

    def clear_cache(self, name: str) -> None:
        if name not in self.cache_map:
            self.cache_map[name].clear_cache()
            del self.cache_map[name]

    def cache_info(self, name: str) -> Dict[str, Any]:
        if name not in self.cache_map:
            raise CommonException(error_code=CommonErrorCode.CACHE_NOT_FOUND, dynamics_message=name)
        return self.cache_map[name].cache_info()