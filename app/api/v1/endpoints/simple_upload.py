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
from app.core.app_logging import api_logger
from app.models.user import User
from app.models.video import Video
from app.schemas.common import ResponseModel
from app.schemas.video_upload import UploadStatus

# 创建路由器
router = APIRouter()

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
    description: str = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """简单视频文件上传
    
    接收单个视频文件并保存到服务器。
    """
    
    file_path: Path | None = None
    try:
        # 记录接收到的参数
        api_logger.info(
            "Simple upload parameters received",
            has_file=file is not None,
            filename=getattr(file, 'filename', 'no_filename') if file else 'no_file',
            content_type=getattr(file, 'content_type', 'no_content_type') if file else 'no_file',
            title=title,
            description=description,
            user_id=current_user.id
        )
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

        # 提取视频元数据
        from app.services.video_metadata import VideoMetadataExtractor
        extractor = VideoMetadataExtractor()
        meta = extractor.extract_comprehensive_metadata(str(file_path))
        
        format_info = meta.get('format_info', {})
        video_streams = meta.get('video_streams', [])
        audio_streams = meta.get('audio_streams', [])
        
        # 录入数据库
        from app.models.uploaded_file import UploadedFile
        import datetime
        import os
        
        # 存入 uploaded_files 表（用于旧版历史记录等）
        new_uploaded_file = UploadedFile(
            user_id=current_user.id,
            original_filename=file.filename,
            saved_filename=unique_filename,
            file_size=file_size,
            content_type=file.content_type,
            title=title or Path(file.filename).stem,
            description=description,
            file_path=str(file_path),
            duration=format_info.get('duration'),
            format_name=format_info.get('format_name'),
            bit_rate=format_info.get('bit_rate'),
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
            file_created_at=datetime.datetime.fromtimestamp(os.path.getctime(str(file_path)))
        )
        
        if video_streams:
            vs = video_streams[0]
            new_uploaded_file.width = vs.get('width')
            new_uploaded_file.height = vs.get('height')
            new_uploaded_file.video_codec = vs.get('codec_name')
            new_uploaded_file.frame_rate = vs.get('r_frame_rate')
            new_uploaded_file.aspect_ratio = vs.get('display_aspect_ratio')

        if audio_streams:
            ast = audio_streams[0]
            new_uploaded_file.audio_codec = ast.get('codec_name')
            new_uploaded_file.sample_rate = ast.get('sample_rate')
            new_uploaded_file.channels = ast.get('channels')

        db.add(new_uploaded_file)
        
        # 存入 videos 表（新版分片上传机制统一表）
        new_video = Video(
            title=title or Path(file.filename).stem,
            description=description,
            original_filename=file.filename,
            file_path=str(file_path),
            file_size=file_size,
            platform="local",
            status="uploaded",
            upload_status=UploadStatus.COMPLETED,
            uploaded_by=current_user.id,
            duration=format_info.get('duration'),
            format=format_info.get('format_name'),
            bitrate=format_info.get('bit_rate'),
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now()
        )
        
        if video_streams:
            vs = video_streams[0]
            new_video.resolution = f"{vs.get('width')}x{vs.get('height')}" if vs.get('width') else None
            
            fps_str = vs.get('r_frame_rate', '0/1')
            if '/' in fps_str:
                num, den = fps_str.split('/')
                if int(den) > 0:
                    new_video.fps = int(num) / int(den)
                    
            new_video.codec = vs.get('codec_name')
            new_video.video_codec = vs.get('codec_name')
            
        if audio_streams:
            new_video.audio_codec = audio_streams[0].get('codec_name')
            
        db.add(new_video)
        
        db.commit()
        try:
            from app.tasks.video_tasks import process_uploaded_video

            process_uploaded_video.delay(new_video.id)
        except Exception as e:
            api_logger.error(
                "Failed to enqueue video post-processing",
                video_id=new_video.id,
                error=str(e)
            )

        api_logger.info(
            "File saved successfully",
            file_path=str(file_path),
            file_size=file_size
        )

        return ResponseModel(
            code=200,
            message="File uploaded successfully",
            data={
                "video_id": new_video.id,
                "filename": file.filename,
                "file_size": file_size,
                "upload_status": "completed",
                "file_path": str(file_path)
            }
        )
        
    except HTTPException:
        db.rollback()
        if file_path and file_path.exists():
            try:
                file_path.unlink()
            except OSError:
                pass
        raise
    except Exception as e:
        db.rollback()
        if file_path and file_path.exists():
            try:
                file_path.unlink()
            except OSError:
                pass
        api_logger.error(
            "Simple upload failed",
            error=str(e),
            filename=file.filename if file else None
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )
