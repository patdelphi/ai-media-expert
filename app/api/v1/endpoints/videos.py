"""视频管理API端点

提供视频信息查询、管理等相关的API接口。
"""

from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.models.video import Video, VideoTag, Tag
from app.schemas.common import PaginatedResponse, PaginationParams, ResponseModel
from app.schemas.video import VideoResponse, VideoListResponse
from app.core.app_logging import api_logger

router = APIRouter()


@router.get("/", response_model=ResponseModel[PaginatedResponse[VideoListResponse]])
def get_videos(
    pagination: PaginationParams = Depends(),
    platform: Optional[str] = Query(None, description="平台筛选"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """获取视频列表
    
    分页获取用户的视频列表，支持平台筛选和关键词搜索。
    """
    # 构建查询
    query = db.query(Video).join(
        Video.download_tasks
    ).filter(
        Video.download_tasks.any(user_id=current_user.id),
        Video.status == "active"
    )
    
    # 平台筛选
    if platform:
        query = query.filter(Video.platform == platform)
    
    # 关键词搜索
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Video.title.ilike(search_term),
                Video.description.ilike(search_term),
                Video.author.ilike(search_term)
            )
        )
    
    # 获取总数
    total = query.count()
    
    # 分页查询
    videos = query.order_by(desc(Video.created_at)).offset(
        pagination.offset
    ).limit(pagination.size).all()
    
    # 转换为响应模型
    video_responses = [VideoListResponse.from_attributes(video) for video in videos]
    
    paginated_data = PaginatedResponse.create(
        items=video_responses,
        total=total,
        page=pagination.page,
        size=pagination.size
    )
    
    return ResponseModel(
        code=200,
        message="Videos retrieved successfully",
        data=paginated_data
    )


@router.get("/{video_id}", response_model=ResponseModel[VideoResponse])
def get_video(
    video_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """获取视频详情
    
    获取指定视频的详细信息。
    """
    # 查询视频
    video = db.query(Video).join(
        Video.download_tasks
    ).filter(
        Video.id == video_id,
        Video.download_tasks.any(user_id=current_user.id),
        Video.status == "active"
    ).first()
    
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found"
        )
    
    return ResponseModel(
        code=200,
        message="Video retrieved successfully",
        data=VideoResponse.from_attributes(video)
    )


@router.delete("/{video_id}", response_model=ResponseModel[dict])
def delete_video(
    video_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """删除视频
    
    软删除指定的视频（设置状态为deleted）。
    """
    # 查询视频
    video = db.query(Video).join(
        Video.download_tasks
    ).filter(
        Video.id == video_id,
        Video.download_tasks.any(user_id=current_user.id),
        Video.status == "active"
    ).first()
    
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found"
        )
    
    # 软删除
    video.status = "deleted"
    db.commit()
    
    api_logger.info(
        "Video deleted",
        user_id=current_user.id,
        video_id=video_id,
        video_title=video.title
    )
    
    return ResponseModel(
        code=200,
        message="Video deleted successfully",
        data={"message": "Video has been deleted"}
    )


@router.get("/{video_id}/tags", response_model=ResponseModel[List[dict]])
def get_video_tags(
    video_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """获取视频标签
    
    获取指定视频的所有标签。
    """
    # 验证视频权限
    video = db.query(Video).join(
        Video.download_tasks
    ).filter(
        Video.id == video_id,
        Video.download_tasks.any(user_id=current_user.id),
        Video.status == "active"
    ).first()
    
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found"
        )
    
    # 获取标签
    video_tags = db.query(VideoTag, Tag).join(
        Tag, VideoTag.tag_id == Tag.id
    ).filter(
        VideoTag.video_id == video_id
    ).all()
    
    tags_data = [
        {
            "id": tag.id,
            "name": tag.name,
            "category": tag.category,
            "color": tag.color,
            "confidence": video_tag.confidence,
            "created_by": video_tag.created_by
        }
        for video_tag, tag in video_tags
    ]
    
    return ResponseModel(
        code=200,
        message="Video tags retrieved successfully",
        data=tags_data
    )


@router.get("/platforms/list", response_model=ResponseModel[List[dict]])
def get_platforms(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """获取平台列表
    
    获取用户视频涉及的所有平台及其视频数量。
    """
    # 查询用户视频的平台统计
    platforms = db.query(
        Video.platform,
        db.func.count(Video.id).label('count')
    ).join(
        Video.download_tasks
    ).filter(
        Video.download_tasks.any(user_id=current_user.id),
        Video.status == "active",
        Video.platform.isnot(None)
    ).group_by(Video.platform).all()
    
    platforms_data = [
        {
            "platform": platform,
            "count": count
        }
        for platform, count in platforms
    ]
    
    return ResponseModel(
        code=200,
        message="Platforms retrieved successfully",
        data=platforms_data
    )