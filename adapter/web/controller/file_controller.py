from fastapi import APIRouter, Depends, UploadFile, File as FastAPIFile
from common.core.logger import get_logger
from common.core.container.container import get_container
from application.port.inbound.file_case import FileCase
from adapter.web.vo.base_response import BaseResponse
from typing import List, Optional

logger = get_logger(__name__)

router = APIRouter(prefix="/api/file", tags=["FILE"])

def file_case() -> FileCase:
    return get_container().get(FileCase)

@router.get("/allowed_types")
async def get_allowed_file_types(file_service: FileCase = Depends(file_case)) -> BaseResponse:
    return BaseResponse.from_success(data=await file_service.get_allowed_file_types())

@router.post("/upload")
async def upload_file(
    file: UploadFile = FastAPIFile(...),
    file_service: FileCase = Depends(file_case)
) -> BaseResponse:
    return BaseResponse.from_success(data=await file_service.upload_file(file))

@router.get("/list")
async def get_files(
    content_keyword: Optional[str] = None,
    filename_keyword: Optional[str] = None,
    file_service: FileCase = Depends(file_case)
) -> BaseResponse:
    return BaseResponse.from_success(data=await file_service.get_file_list(
        content_keyword=content_keyword,
        filename_keyword=filename_keyword
    ))

@router.get("/chunks")
async def get_file_chunks(
    content_keyword: Optional[str] = None,
    file_id_list: Optional[List[str]] = None,
    file_service: FileCase = Depends(file_case)
) -> BaseResponse:
    return BaseResponse.from_success(data=await file_service.get_chunk_list(
        content_keyword=content_keyword,
        file_id_list=file_id_list
    ))

@router.delete("/batch")
async def delete_files(
    file_id_list: List[str],
    file_service: FileCase = Depends(file_case)
) -> BaseResponse:
    return BaseResponse.from_success(data=await file_service.delete_files(file_id_list))
