"""测试上传API

最简化的文件上传测试，用于排除422错误。
"""

from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
<<<<<<< HEAD
from app.core.app_logging import get_logger
=======
from app.core.logging import get_logger
>>>>>>> ad3f17f (feat: 完善视频上传功能 - 修复时长格式化、上传时间显示、移除时间编辑按钮)

# 创建路由器
router = APIRouter()

# 获取日志记录器
api_logger = get_logger("api")


@router.post("/test")
async def test_upload(file: UploadFile = File(...)):
    """最简化的文件上传测试"""
    try:
        api_logger.info(f"Test upload received: {file.filename}")
        
        # 读取文件内容
        content = await file.read()
        file_size = len(content)
        
        api_logger.info(f"File size: {file_size} bytes")
        
        return JSONResponse(
            status_code=200,
            content={
                "message": "Upload successful",
                "filename": file.filename,
                "size": file_size,
                "content_type": file.content_type
            }
        )
        
    except Exception as e:
        api_logger.error(f"Test upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ping")
async def ping():
    """简单的ping测试"""
    return {"message": "pong"}