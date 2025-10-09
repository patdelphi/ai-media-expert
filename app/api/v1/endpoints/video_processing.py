"""视频处理API端点

提供视频处理相关功能，包括缩略图生成、元数据提取等。
"""

import os
from typing import Any, List, Optional
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.models.video import Video
from app.schemas.common import ResponseModel
from app.services.video_processing import video_processing_service
from app.core.app_logging import api_logger
from app.tasks.video_tasks import generate_video_thumbnails

router = APIRouter()


@router.post("/videos/{video_id}/thumbnails", response_model=ResponseModel[dict])
def generate_thumbnails(
    video_id: int,
    timestamps: Optional[List[int]] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """为指定视频生成缩略图
    
    Args:
        video_id: 视频ID
        timestamps: 指定时间戳列表（秒），如果不提供则自动选择
    """
    # 检查视频是否存在
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found"
        )
    
    # 检查用户权限（只有上传者或管理员可以操作）
    if video.uploaded_by != current_user.id and current_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied"
        )
    
    # 检查视频文件是否存在
    if not video.file_path or not os.path.exists(video.file_path):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Video file not found"
        )
    
    try:
        # 启动异步任务生成缩略图
        task = generate_video_thumbnails.delay(video_id, timestamps)
        
        api_logger.info(
            "Thumbnail generation task started",
            video_id=video_id,
            task_id=task.id,
            user_id=current_user.id
        )
        
        return ResponseModel(
            code=200,
            message="Thumbnail generation task started",
            data={
                "task_id": task.id,
                "video_id": video_id,
                "status": "processing"
            }
        )
        
    except Exception as e:
        api_logger.error(
            "Failed to start thumbnail generation",
            video_id=video_id,
            user_id=current_user.id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate thumbnails: {str(e)}"
        )


@router.get("/videos/{video_id}/analysis", response_model=ResponseModel[dict])
def analyze_video(
    video_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """分析视频文件信息
    
    返回视频的详细技术信息，包括编码格式、分辨率、时长等。
    """
    # 检查视频是否存在
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found"
        )
    
    # 检查用户权限
    if video.uploaded_by != current_user.id and current_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied"
        )
    
    # 检查视频文件是否存在
    if not video.file_path or not os.path.exists(video.file_path):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Video file not found"
        )
    
    try:
        # 分析视频信息
        video_info = video_processing_service.analyze_video(video.file_path)
        
        # 验证视频文件
        is_valid, error_msg = video_processing_service.validate_video_file(video.file_path)
        
        api_logger.info(
            "Video analysis completed",
            video_id=video_id,
            user_id=current_user.id
        )
        
        return ResponseModel(
            code=200,
            message="Video analysis completed",
            data={
                "video_id": video_id,
                "file_info": {
                    "path": video.file_path,
                    "size": video.file_size,
                    "original_name": video.original_filename
                },
                "technical_info": video_info,
                "validation": {
                    "is_valid": is_valid,
                    "error_message": error_msg
                },
                "processing_status": {
                    "upload_status": video.upload_status,
                    "is_analyzed": video.is_analyzed,
                    "has_thumbnail": bool(video.thumbnail_path),
                    "preview_images_count": len(video.preview_images) if video.preview_images else 0
                }
            }
        )
        
    except Exception as e:
        api_logger.error(
            "Video analysis failed",
            video_id=video_id,
            user_id=current_user.id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze video: {str(e)}"
        )


@router.post("/videos/{video_id}/reprocess", response_model=ResponseModel[dict])
def reprocess_video(
    video_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """重新处理视频
    
    重新执行视频分析、缩略图生成等处理任务。
    """
    # 检查视频是否存在
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found"
        )
    
    # 检查用户权限
    if video.uploaded_by != current_user.id and current_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied"
        )
    
    # 检查视频文件是否存在
    if not video.file_path or not os.path.exists(video.file_path):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Video file not found"
        )
    
    try:
        # 重置处理状态
        video.is_analyzed = False
        video.thumbnail_path = None
        video.preview_images = []
        db.commit()
        
        # 启动重新处理任务
        from app.tasks.video_tasks import process_uploaded_video
        task = process_uploaded_video.delay(video_id)
        
        api_logger.info(
            "Video reprocessing task started",
            video_id=video_id,
            task_id=task.id,
            user_id=current_user.id
        )
        
        return ResponseModel(
            code=200,
            message="Video reprocessing task started",
            data={
                "task_id": task.id,
                "video_id": video_id,
                "status": "processing"
            }
        )
        
    except Exception as e:
        api_logger.error(
            "Failed to start video reprocessing",
            video_id=video_id,
            user_id=current_user.id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reprocess video: {str(e)}"
        )


@router.get("/videos/{video_id}/thumbnails", response_model=ResponseModel[dict])
def get_video_thumbnails(
    video_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """获取视频缩略图信息
    
    返回视频的主缩略图和预览图片列表。
    """
    # 检查视频是否存在
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found"
        )
    
    # 检查用户权限
    if video.uploaded_by != current_user.id and current_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied"
        )
    
    # 构建缩略图URL（这里需要根据实际的静态文件服务配置）
    def build_thumbnail_url(path: str) -> str:
        if not path:
            return ""
        # 将绝对路径转换为相对URL
        # 这里假设uploads目录通过/static/uploads路径提供服务
        relative_path = path.replace(str(Path("uploads")), "static/uploads").replace("\\", "/")
        return f"http://localhost:8000/{relative_path}"
    
    thumbnail_data = {
        "video_id": video_id,
        "main_thumbnail": {
            "path": video.thumbnail_path,
            "url": build_thumbnail_url(video.thumbnail_path) if video.thumbnail_path else None
        },
        "preview_images": [],
        "additional_thumbnails": []
    }
    
    # 添加预览图片
    if video.preview_images:
        for i, img_path in enumerate(video.preview_images):
            thumbnail_data["preview_images"].append({
                "index": i,
                "path": img_path,
                "url": build_thumbnail_url(img_path)
            })
    
    # 添加额外的缩略图（如果有）
    if video.extra_metadata and "additional_thumbnails" in video.extra_metadata:
        for i, img_path in enumerate(video.extra_metadata["additional_thumbnails"]):
            thumbnail_data["additional_thumbnails"].append({
                "index": i,
                "path": img_path,
                "url": build_thumbnail_url(img_path)
            })
    
    return ResponseModel(
        code=200,
        message="Thumbnails retrieved successfully",
        data=thumbnail_data
    )