from typing import List, Dict, Optional, Any

from application.domain.file import File, FileChunk
from common.core.container.annotate import component
from application.port.inbound.file_case import FileCase
from application.port.outbound.file_port import FilePort
import injector
from common.core.logger import get_logger

logger = get_logger(__name__)

@component
class FileService(FileCase):

    @injector.inject
    def __init__(self, file_port: FilePort):
        self.file_port = file_port

    async def get_allowed_file_types(self) -> List[str]:
        return self.file_port.get_allowed_file_types()

    async def upload_file(self, file: Any, **kwargs) -> File:
        logger.info(f"上传文件 ---> [filename={getattr(file, 'filename', 'unknown')}]")
        return await self.file_port.upload(file, **kwargs)  # 添加了await

    async def get_file_list(
        self,
        content_keyword: Optional[str] = None,
        filename_keyword: Optional[str] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        logger.info(f"查询文件列表 ---> [content_keyword={content_keyword}, filename_keyword={filename_keyword}]")
        return self.file_port.file_list(
            content_keyword=content_keyword,
            filename_keyword=filename_keyword,
            **kwargs
        )

    async def get_chunk_list(
        self,
        content_keyword: Optional[str] = None,
        file_id_list: Optional[List[str]] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        logger.info(f"查询文件块列表 ---> [content_keyword={content_keyword}, file_id_list={file_id_list}]")
        return self.file_port.chunk_list(
            content_keyword=content_keyword,
            file_id_list=file_id_list,
            **kwargs
        )

    async def delete_files(self, file_id_list: List[str], **kwargs) -> Dict[str, Any]:
        logger.info(f"删除文件 ---> {file_id_list}")
        return self.file_port.delete(file_id_list, **kwargs)
