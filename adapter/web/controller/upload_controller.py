from fastapi import APIRouter, Depends, File, UploadFile, Form
import uuid
import aiofiles
from common.core.logger import get_logger
logger = get_logger(__name__)

router = APIRouter(prefix="/api/upload", tags=["Upload"])

@router.post("/upload")
async def upload(
        file: UploadFile = File(...),
        #description: str = Form(...)
    ):
    # 获取文件类型
    content_type = file.content_type

    unique_id = uuid.uuid4()

    # 读取文件内容并转为base64
    content = await file.read()
    # base64_str = base64.b64encode(content).decode("utf-8")
    # 可选：保存文件到本地（调试用）
    async with aiofiles.open(f"uploads/{unique_id}", 'wb') as out_file:
        await out_file.write(content)
        
    return {
        "code": 200,
        "message": "success",
        "sub_code": 200,
        "sub_message": "success",
        "data": {
            "id": unique_id,
            "filename": file.filename,
        }
    }

