from abc import ABC, abstractmethod
from typing import List, Optional
from application.domain.file import FileChunk

class VectorDBPort(ABC):
    """向量数据库操作端口接口"""

    @abstractmethod
    async def store_chunk(self, chunk: FileChunk) -> Optional[FileChunk]:
        """
        存储文件块到向量数据库
        :param chunk: 文件块实体
        :return: 存储后的文件块实体(包含向量ID等)
        """
        pass

    @abstractmethod
    async def search_chunks(
        self,
        query: str,
        file_id_list: Optional[List[str]] = None,
        limit: int = 5
    ) -> List[FileChunk]:
        """
        在向量数据库中搜索相似块
        :param query: 查询文本
        :param file_id_list: 限定搜索的文件ID列表
        :param limit: 返回结果数量限制
        :return: 相似文件块列表
        """
        pass

    @abstractmethod
    async def delete_chunks(self, chunk_ids: List[str]) -> int:
        """
        从向量数据库删除块
        :param chunk_ids: 要删除的块ID列表
        :return: 实际删除的数量
        """
        pass

    @abstractmethod
    async def get_chunk(self, chunk_id: str) -> Optional[FileChunk]:
        """
        获取单个块信息
        :param chunk_id: 块ID
        :return: 文件块实体
        """
        pass
