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
        
        # 检查文件大小（500MB限制）
        max_size = 500 * 1024 * 1024  # 500MB
        file_size = 0
        with open(file_path, "wb") as f:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                file_size += len(chunk)
                if file_size > max_size:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail="File size exceeds 500MB limit"
                    )
                f.write(chunk)

        # 提取视频元数据
        from app.services.video_metadata import VideoMetadataExtractor
        extractor = VideoMetadataExtractor()
        meta = extractor.extract_comprehensive_metadata(str(file_path))
        
        format_info = meta.get('format_info', {})
        video_streams = meta.get('video_streams', [])
        audio_streams = meta.get('audio_streams', [])
        format_name = format_info.get('format_name')
        if isinstance(format_name, str) and format_name:
            format_name = format_name.split(',')[0]
        
        # 录入数据库
        from app.models.uploaded_file import UploadedFile
        import datetime
        
        def _safe_int(value):
            try:
                return int(value)
            except (TypeError, ValueError):
                return None

        def _calc_video_ratio(width: int | None, height: int | None) -> str | None:
            if not width or not height:
                return None
            def gcd(a: int, b: int) -> int:
                while b:
                    a, b = b, a % b
                return a
            common_divisor = gcd(width, height)
            simplified_width = width // common_divisor
            simplified_height = height // common_divisor
            if simplified_width > 50 or simplified_height > 50:
                standard_ratios = [
                    (16, 9), (9, 16), (4, 3), (3, 4), (1, 1),
                    (21, 9), (9, 21), (5, 4), (4, 5)
                ]
                current_ratio = width / height
                best_match = None
                min_diff = float('inf')
                for w, h in standard_ratios:
                    ratio = w / h
                    diff = abs(current_ratio - ratio)
                    if diff < min_diff:
                        min_diff = diff
                        best_match = (w, h)
                if best_match and min_diff < 0.1:
                    simplified_width, simplified_height = best_match
            return f"{simplified_width}:{simplified_height}"

        def _calc_aspect_ratio(width: int | None, height: int | None) -> str | None:
            if not width or not height:
                return None
            ratio = round(width / height, 2)
            return f"{ratio:.2f}:1"

        def _calc_fps(frame_rate: str | None) -> str | None:
            if not frame_rate:
                return None
            if "/" in frame_rate:
                try:
                    num_str, den_str = frame_rate.split("/", 1)
                    num = float(num_str)
                    den = float(den_str)
                    if den == 0:
                        return None
                    return f"{num / den:.2f}"
                except ValueError:
                    return None
            try:
                return f"{float(frame_rate):.2f}"
            except ValueError:
                return None

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
            format_name=format_name,
            bit_rate=format_info.get('bit_rate'),
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
            file_created_at=datetime.datetime.fromtimestamp(os.path.getctime(str(file_path)))
        )
        
        if video_streams:
            vs = video_streams[0]
            width = _safe_int(vs.get('width'))
            height = _safe_int(vs.get('height'))
            new_uploaded_file.width = width
            new_uploaded_file.height = height
            new_uploaded_file.video_codec = vs.get('codec_name')
            new_uploaded_file.frame_rate = _calc_fps(vs.get('r_frame_rate'))
            new_uploaded_file.aspect_ratio = _calc_aspect_ratio(width, height)
            new_uploaded_file.video_ratio = _calc_video_ratio(width, height)

        if audio_streams:
            ast = audio_streams[0]
            new_uploaded_file.audio_codec = ast.get('codec_name')
            new_uploaded_file.sample_rate = _safe_int(ast.get('sample_rate'))
            new_uploaded_file.channels = _safe_int(ast.get('channels'))

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
            format=format_name,
            bitrate=format_info.get('bit_rate'),
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now()
        )
        
        if video_streams:
            vs = video_streams[0]
            width = _safe_int(vs.get('width'))
            height = _safe_int(vs.get('height'))
            new_video.resolution = f"{width}x{height}" if width and height else None
            fps_value = _calc_fps(vs.get('r_frame_rate'))
            if fps_value is not None:
                try:
                    new_video.fps = float(fps_value)
                except ValueError:
                    pass
                    
            new_video.codec = vs.get('codec_name')
            new_video.video_codec = vs.get('codec_name')
            
        if audio_streams:
            new_video.audio_codec = audio_streams[0].get('codec_name')
            
        db.add(new_video)
        
        db.commit()
        db.refresh(new_video)
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
