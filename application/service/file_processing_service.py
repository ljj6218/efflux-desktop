from typing import List, Optional
from common.core.container.annotate import component
from application.domain.file import File, FileChunk
from application.port.outbound.file_port import FilePort
from application.port.outbound.vectordb_port import VectorDBPort
import injector
from common.core.logger import get_logger

logger = get_logger(__name__)

@component
class FileProcessingService:

    @injector.inject
    def __init__(
        self,
        file_port: FilePort,
        vectordb_port: VectorDBPort
    ):
        self.file_port = file_port
        self.vectordb_port = vectordb_port

    async def process_file_to_chunks(self, file_id: str) -> List[FileChunk]:
        """处理文件并转换为文本块"""
        logger.info(f"开始处理文件 ---> [file_id={file_id}]")

        # 1. 获取文件元信息
        file_info = await self._get_file_info(file_id)
        if not file_info:
            logger.error(f"文件不存在 ---> [file_id={file_id}]")
            return []

        # 2. 读取并转换文件内容
        content = await self._read_file_content(file_info)
        if not content:
            logger.error(f"文件内容为空 ---> [file_id={file_id}]")
            return []

        # 3. 文本分块处理
        chunks = self._split_content_to_chunks(content, file_id)
        if not chunks:
            logger.error(f"分块处理失败 ---> [file_id={file_id}]")
            return []

        # 4. 存储向量
        saved_chunks = await self._store_chunks_to_vectordb(chunks)
        logger.info(f"文件处理完成 ---> [file_id={file_id}, chunks_count={len(saved_chunks)}]")
        return saved_chunks

    async def _get_file_info(self, file_id: str) -> Optional[File]:
        """获取文件元信息"""
        files = await self.file_port.get_file_list(file_id_list=[file_id])
        return files[0] if files else None

    async def _read_file_content(self, file_info: File) -> Optional[str]:
        """读取文件内容"""
        # 这里需要根据实际文件类型实现具体读取逻辑
        # 例如: PDF解析、Word文档解析等
        raise NotImplementedError("文件内容读取方法需要实现")

    def _split_content_to_chunks(self, content: str, file_id: str) -> List[FileChunk]:
        """将内容分割为块"""
        # 这里实现具体分块逻辑，例如按段落、按字数等
        raise NotImplementedError("内容分块方法需要实现")

    async def _store_chunks_to_vectordb(self, chunks: List[FileChunk]) -> List[FileChunk]:
        """存储块到向量数据库"""
        saved_chunks = []
        for chunk in chunks:
            saved_chunk = await self.vectordb_port.store_chunk(chunk)
            if saved_chunk:
                saved_chunks.append(saved_chunk)
        return saved_chunks