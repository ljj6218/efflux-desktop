from fastapi import APIRouter, Depends, File, UploadFile, Form
import uuid
import aiofiles
from common.core.logger import get_logger
from common.utils.json_file_util import JSONFileUtil
import traceback

logger = get_logger(__name__)

router = APIRouter(prefix="/api/upload", tags=["Upload"])

@router.post("/upload")
async def upload(
        file: UploadFile = File(...),
        #description: str = Form(...)
    ):
    unique_id = uuid.uuid4()

    # 读取文件内容并转为base64
    content = await file.read()
    # base64_str = base64.b64encode(content).decode("utf-8")
    # 可选：保存文件到本地（调试用）
    try:
        async with aiofiles.open(f"uploads/{unique_id}", 'wb') as out_file:
            await out_file.write(content)
        file_info = {
            "filename": file.filename,
            "content_type": file.content_type,
            "size": file.size
        }
        # 只有在文件成功保存后才会执行这里
        JSONFileUtil(f"uploads/{unique_id}.json").write(file_info)
    except Exception as e:
        # 发生任何异常时执行这里
        logger.info('文件保存失败')
        logger.info(traceback.format_exc())

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

