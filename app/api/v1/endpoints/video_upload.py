"""视频上传API端点

提供视频文件上传、进度跟踪、控制等功能。
"""

import os
import uuid
import hashlib
from typing import Any, List, Optional
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.models.video import Video
from app.schemas.video_upload import (
    InitUploadRequest, InitUploadResponse, ChunkUploadRequest, ChunkUploadResponse,
    UploadProgressResponse, UploadControlRequest, VideoUploadResponse,
    UploadSessionInfo, UploadStatus, FileValidationResponse
)
from app.schemas.common import ResponseModel
from app.core.config import settings
<<<<<<< HEAD
from app.core.app_logging import api_logger
=======
from app.core.logging import api_logger
>>>>>>> ad3f17f (feat: 完善视频上传功能 - 修复时长格式化、上传时间显示、移除时间编辑按钮)
from app.services.video_processing import VideoProcessingService

router = APIRouter()

# 上传目录配置
UPLOAD_DIR = Path(settings.upload_dir) / "videos"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# 临时分片目录
TEMP_DIR = UPLOAD_DIR / "temp"
TEMP_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/init", response_model=ResponseModel[InitUploadResponse])
def init_upload(
    request: InitUploadRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """初始化视频上传
    
    创建上传会话，生成唯一的会话ID和视频记录。
    """
    try:
        # 生成唯一的上传会话ID
        upload_session_id = str(uuid.uuid4())
        
        # 计算总分片数
        total_chunks = (request.file_size + request.chunk_size - 1) // request.chunk_size
        
        # 生成唯一文件名
        file_extension = Path(request.filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = str(UPLOAD_DIR / unique_filename)
        
        # 创建视频记录
        video = Video(
            title=request.title or Path(request.filename).stem,
            description=request.description,
            original_filename=request.filename,
            file_path=file_path,
            file_size=request.file_size,
            upload_status=UploadStatus.PENDING,
            upload_progress=0.0,
            uploaded_by=current_user.id,
            chunk_size=request.chunk_size,
            total_chunks=total_chunks,
            uploaded_chunks=0,
            upload_session_id=upload_session_id,
            status="uploading"
        )
        
        db.add(video)
        db.commit()
        db.refresh(video)
        
        # 创建临时目录用于存储分片
        session_temp_dir = TEMP_DIR / upload_session_id
        session_temp_dir.mkdir(exist_ok=True)
        
        api_logger.info(
            "Upload session initialized",
            user_id=current_user.id,
            video_id=video.id,
            upload_session_id=upload_session_id,
            filename=request.filename,
            file_size=request.file_size,
            total_chunks=total_chunks
        )
        
        return ResponseModel(
            code=200,
            message="Upload session initialized successfully",
            data=InitUploadResponse(
                upload_session_id=upload_session_id,
                video_id=video.id,
                chunk_size=request.chunk_size,
                total_chunks=total_chunks,
                uploaded_chunks=[],
                upload_url=f"/api/v1/upload/chunk"
            )
        )
        
    except Exception as e:
        api_logger.error(
            "Failed to initialize upload session",
            user_id=current_user.id,
            error=str(e),
            filename=request.filename
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize upload: {str(e)}"
        )


@router.post("/chunk", response_model=ResponseModel[ChunkUploadResponse])
async def upload_chunk(
    upload_session_id: str = Form(...),
    chunk_index: int = Form(...),
    total_chunks: int = Form(...),
    chunk_file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """上传视频分片
    
    接收并保存视频文件分片。
    """
    try:
        # 记录接收到的参数
        api_logger.info(
            "Chunk upload request received",
            upload_session_id=upload_session_id,
            chunk_index=chunk_index,
            total_chunks=total_chunks,
            chunk_filename=chunk_file.filename,
            chunk_content_type=chunk_file.content_type,
            chunk_size=chunk_file.size if hasattr(chunk_file, 'size') else 'unknown',
            user_id=current_user.id
        )
        # 查找视频记录
        video = db.query(Video).filter(
            and_(
                Video.upload_session_id == upload_session_id,
                Video.uploaded_by == current_user.id
            )
        ).first()
        
        if not video:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Upload session not found"
            )
        
        # 检查上传状态
        if video.upload_status == UploadStatus.CANCELLED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Upload has been cancelled"
            )
        
        # 更新上传状态为正在上传
        if video.upload_status == UploadStatus.PENDING:
            video.upload_status = UploadStatus.UPLOADING
        
        # 保存分片文件
        session_temp_dir = TEMP_DIR / upload_session_id
        chunk_path = session_temp_dir / f"chunk_{chunk_index:06d}"
        
        # 写入分片数据
        chunk_data = await chunk_file.read()
        with open(chunk_path, "wb") as f:
            f.write(chunk_data)
        
        # 更新上传进度
        video.uploaded_chunks += 1
        video.upload_progress = (video.uploaded_chunks / video.total_chunks) * 100
        
        # 检查是否所有分片都已上传
        if video.uploaded_chunks >= video.total_chunks:
            # 合并分片
            await merge_chunks(video, session_temp_dir, db)
        
        db.commit()
        
        api_logger.info(
            "Chunk uploaded",
            user_id=current_user.id,
            video_id=video.id,
            chunk_index=chunk_index,
            progress=video.upload_progress
        )
        
        return ResponseModel(
            code=200,
            message="Chunk uploaded successfully",
            data=ChunkUploadResponse(
                chunk_index=chunk_index,
                uploaded=True,
                progress=video.upload_progress,
                uploaded_chunks=video.uploaded_chunks,
                total_chunks=video.total_chunks,
                upload_speed=video.upload_speed
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        api_logger.error(
            "Failed to upload chunk",
            user_id=current_user.id,
            upload_session_id=upload_session_id,
            chunk_index=chunk_index,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload chunk: {str(e)}"
        )


async def merge_chunks(video: Video, temp_dir: Path, db: Session):
    """合并分片文件"""
    try:
        # 合并所有分片
        with open(video.file_path, "wb") as output_file:
            for i in range(video.total_chunks):
                chunk_path = temp_dir / f"chunk_{i:06d}"
                if chunk_path.exists():
                    with open(chunk_path, "rb") as chunk_file:
                        output_file.write(chunk_file.read())
                    # 删除分片文件
                    chunk_path.unlink()
        
        # 删除临时目录
        if temp_dir.exists():
            temp_dir.rmdir()
        
        # 更新视频状态
        video.upload_status = UploadStatus.COMPLETED
        video.upload_progress = 100.0
        video.status = "uploaded"
        
        # 启动视频处理任务（异步）
        from app.tasks.video_tasks import process_uploaded_video
        process_uploaded_video.delay(video.id)
        
        api_logger.info(
            "Video upload completed",
            video_id=video.id,
            file_path=video.file_path
        )
        
    except Exception as e:
        video.upload_status = UploadStatus.FAILED
        video.upload_error = str(e)
        api_logger.error(
            "Failed to merge chunks",
            video_id=video.id,
            error=str(e)
        )
        raise


@router.get("/progress/{upload_session_id}", response_model=ResponseModel[UploadProgressResponse])
def get_upload_progress(
    upload_session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """获取上传进度
    
    实时获取指定上传会话的进度信息。
    """
    video = db.query(Video).filter(
        and_(
            Video.upload_session_id == upload_session_id,
            Video.uploaded_by == current_user.id
        )
    ).first()
    
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Upload session not found"
        )
    
    # 计算预计剩余时间
    estimated_time = None
    if video.upload_speed and video.upload_speed > 0:
        remaining_bytes = video.file_size * (100 - video.upload_progress) / 100
        estimated_time = int(remaining_bytes / video.upload_speed)
    
    return ResponseModel(
        code=200,
        message="Upload progress retrieved successfully",
        data=UploadProgressResponse(
            video_id=video.id,
            upload_session_id=upload_session_id,
            status=video.upload_status,
            progress=video.upload_progress,
            uploaded_chunks=video.uploaded_chunks,
            total_chunks=video.total_chunks,
            upload_speed=video.upload_speed,
            error_message=video.upload_error,
            estimated_time=estimated_time
        )
    )


@router.post("/control", response_model=ResponseModel[dict])
def control_upload(
    request: UploadControlRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """控制上传操作
    
    暂停、恢复或取消上传。
    """
    video = db.query(Video).filter(
        and_(
            Video.upload_session_id == request.upload_session_id,
            Video.uploaded_by == current_user.id
        )
    ).first()
    
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Upload session not found"
        )
    
    if request.action == "pause":
        if video.upload_status == UploadStatus.UPLOADING:
            video.upload_status = UploadStatus.PAUSED
            message = "Upload paused successfully"
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Can only pause uploading videos"
            )
    
    elif request.action == "resume":
        if video.upload_status == UploadStatus.PAUSED:
            video.upload_status = UploadStatus.UPLOADING
            message = "Upload resumed successfully"
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Can only resume paused videos"
            )
    
    elif request.action == "cancel":
        if video.upload_status in [UploadStatus.PENDING, UploadStatus.UPLOADING, UploadStatus.PAUSED]:
            video.upload_status = UploadStatus.CANCELLED
            video.status = "cancelled"
            
            # 清理临时文件
            session_temp_dir = TEMP_DIR / request.upload_session_id
            if session_temp_dir.exists():
                import shutil
                shutil.rmtree(session_temp_dir)
            
            message = "Upload cancelled successfully"
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot cancel completed or failed uploads"
            )
    
    db.commit()
    
    api_logger.info(
        "Upload control action",
        user_id=current_user.id,
        video_id=video.id,
        action=request.action,
        new_status=video.upload_status
    )
    
    return ResponseModel(
        code=200,
        message=message,
        data={"action": request.action, "status": video.upload_status}
    )


@router.get("/sessions", response_model=ResponseModel[List[UploadSessionInfo]])
def get_upload_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """获取用户的上传会话列表
    
    返回当前用户的所有上传会话信息。
    """
    videos = db.query(Video).filter(
        and_(
            Video.uploaded_by == current_user.id,
            Video.upload_session_id.isnot(None)
        )
    ).order_by(Video.created_at.desc()).all()
    
    sessions = []
    for video in videos:
        sessions.append(UploadSessionInfo(
            upload_session_id=video.upload_session_id,
            video_id=video.id,
            filename=video.original_filename,
            file_size=video.file_size,
            chunk_size=video.chunk_size,
            total_chunks=video.total_chunks,
            uploaded_chunks=video.uploaded_chunks,
            status=video.upload_status,
            progress=video.upload_progress,
            upload_speed=video.upload_speed,
            error_message=video.upload_error,
            created_at=video.created_at,
            updated_at=video.updated_at
        ))
    
    return ResponseModel(
        code=200,
        message="Upload sessions retrieved successfully",
        data=sessions
    )