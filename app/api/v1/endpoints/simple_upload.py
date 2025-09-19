"""简单视频上传API

提供单文件上传功能，替代复杂的分片上传机制。
"""

import os
import uuid
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.config import settings
<<<<<<< HEAD
from app.core.app_logging import get_logger
=======
from app.core.logging import get_logger
>>>>>>> ad3f17f (feat: 完善视频上传功能 - 修复时长格式化、上传时间显示、移除时间编辑按钮)
from app.models.user import User
from app.models.video import Video
from app.schemas.common import ResponseModel
from app.schemas.video_upload import UploadStatus

# 创建路由器
router = APIRouter()

# 获取日志记录器
api_logger = get_logger("api")

# 上传目录配置
UPLOAD_DIR = Path(settings.upload_dir) / "videos"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


class SimpleUploadResponse:
    """简单上传响应"""
    def __init__(self, video_id: int, filename: str, file_size: int, message: str):
        self.video_id = video_id
        self.filename = filename
        self.file_size = file_size
        self.message = message


@router.post("/simple", response_model=ResponseModel[dict])
async def simple_upload(
    file: UploadFile = File(...),
    title: str = Form(None),
    description: str = Form(None)
) -> Any:
    """简单视频文件上传
    
    接收单个视频文件并保存到服务器。
    """
    # 记录接收到的参数（在try之前，避免参数验证失败时无法记录）
    api_logger.info(
        "Simple upload parameters received",
        has_file=file is not None,
        filename=getattr(file, 'filename', 'no_filename') if file else 'no_file',
        content_type=getattr(file, 'content_type', 'no_content_type') if file else 'no_file',
        title=title,
        description=description
    )
    
    try:
        # 记录上传请求
        api_logger.info(
            "Simple upload request received",
            filename=file.filename,
            content_type=file.content_type,
            file_size=file.size if hasattr(file, 'size') else 'unknown',
            user_id=current_user.id,
            title=title,
            description=description
        )
        
        # 验证文件类型
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No filename provided"
            )
        
        # 检查文件扩展名
        file_extension = Path(file.filename).suffix.lower()
        allowed_extensions = ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv', '.m4v']
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file format. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # 生成唯一文件名
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = UPLOAD_DIR / unique_filename
        
        # 读取文件内容
        file_content = await file.read()
        file_size = len(file_content)
        
        # 检查文件大小（500MB限制）
        max_size = 500 * 1024 * 1024  # 500MB
        if file_size > max_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File size exceeds 500MB limit"
            )
        
        # 保存文件
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        api_logger.info(
            "File saved successfully",
            file_path=str(file_path),
            file_size=file_size
        )
        
        return ResponseModel(
            code=200,
            message="File uploaded successfully",
            data={
                "filename": file.filename,
                "file_size": file_size,
                "upload_status": "completed",
                "file_path": str(file_path)
            }
        )
        
    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        api_logger.error(
            "Simple upload failed",
            error=str(e),
            filename=file.filename if file else None
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )