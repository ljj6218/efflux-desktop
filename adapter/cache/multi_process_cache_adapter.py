# from typing import Optional, Any, Dict
#
# from common.core.container.annotate import component
# from application.port.outbound.cache_port import CachePort
# from adapter.cache.cache_util import CacheUtil
# # from common.core.multi_process.multi_process_cache import manager, shared_cache
# from common.core.logger import get_logger
# logger = get_logger(__name__)
#
# from multiprocessing import Manager
#
# # 你可以在启动时创建一个共享的缓存
# manager = Manager()
# # 返回一个缓存字典
# shared_cache = manager.dict()
#
# from common.utils.common_utils import set_shared_cache, get_shared_cache
#
# @component
# class CacheAdapter(CachePort):
#
#     # def __init__(self):
#     #     print("=======111=======")
#     #
#     # @staticmethod
#     # def _get_cache_for_name(name: str):
#     #     """获取指定名称的缓存字典"""
#     #     if name not in shared_cache:
#     #         logger.warning(f"查询 {name}")
#     #         # 如果指定名称的缓存不存在，则初始化一个新的缓存
#     #         shared_cache[name] = CacheUtil()
#     #     return shared_cache[name]
#
#     def __init__(self):
#         """通过构造函数注入共享缓存"""
#         self.shared_cache = shared_cache
#
#     def _get_cache_for_name(self, name: str):
#         """获取指定名称的缓存字典"""
#         if name not in self.shared_cache:
#             logger.warning(f"查询 {name}")
#             # 如果指定名称的缓存不存在，则初始化一个新的缓存
#             self.shared_cache[name] = CacheUtil()
#         return self.shared_cache[name]
#
#
#     def clear_cache(self, name: str) -> None:
#         pass
#
#     def cache_info(self, name: str) -> str:
#         pass
#
#     def set_data(self, name: str, key: str, value: Any) -> None:
#         """手动设置缓存数据"""
#         cache = self._get_cache_for_name(name)
#         cache.set_data(key, value)
#
#     def get_from_cache(self, name: str, key: str) -> Optional[Any]:
#         """从缓存中获取数据，如果不存在，返回 None"""
#         cache = self._get_cache_for_name(name)
#         return cache.get_from_cache(key)
#
#     def pop_from_cache(self, name: str, key: str) -> Optional[Any]:
#         """从缓存中获取数据并弹出，如果不存在，返回 None"""
#         cache = self._get_cache_for_name(name)
#         return cache.pop_from_cache(key)
#
#     def delete_from_cache(self, name: str, key: str) -> None:
#         """删除指定键的缓存数据"""
#         cache = self._get_cache_for_name(name)
#         cache.delete_from_cache(key)