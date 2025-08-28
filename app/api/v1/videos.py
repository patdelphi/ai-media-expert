from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from typing import List, Optional
import os

from app.core.database import get_db
from app.models.video import Video
from app.schemas.video import VideoResponse, VideoUpdate

router = APIRouter()

@router.get("/", response_model=List[VideoResponse])
async def get_videos(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    platform: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    sort_by: str = Query("created_at", regex="^(created_at|title|file_size|duration)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    db: Session = Depends(get_db)
):
    """获取视频列表"""
    
    query = db.query(Video)
    
    # 搜索过滤
    if search:
        query = query.filter(
            Video.title.contains(search) |
            Video.description.contains(search) |
            Video.author.contains(search)
        )
    
    # 平台过滤
    if platform and platform != "全部":
        query = query.filter(Video.platform == platform)
    
    # 状态过滤
    if status and status != "全部":
        query = query.filter(Video.status == status)
    
    # 排序
    order_func = desc if sort_order == "desc" else asc
    query = query.order_by(order_func(getattr(Video, sort_by)))
    
    # 分页
    videos = query.offset(skip).limit(limit).all()
    
    return videos

@router.get("/count")
async def get_videos_count(
    search: Optional[str] = Query(None),
    platform: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """获取视频总数"""
    
    query = db.query(Video)
    
    # 应用相同的过滤条件
    if search:
        query = query.filter(
            Video.title.contains(search) |
            Video.description.contains(search) |
            Video.author.contains(search)
        )
    
    if platform and platform != "全部":
        query = query.filter(Video.platform == platform)
    
    if status and status != "全部":
        query = query.filter(Video.status == status)
    
    total = query.count()
    
    return {"total": total}

@router.get("/{video_id}", response_model=VideoResponse)
async def get_video(video_id: int, db: Session = Depends(get_db)):
    """获取单个视频详情"""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")
    return video

@router.put("/{video_id}", response_model=VideoResponse)
async def update_video(
    video_id: int,
    video_update: VideoUpdate,
    db: Session = Depends(get_db)
):
    """更新视频信息"""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")
    
    # 更新字段
    for field, value in video_update.dict(exclude_unset=True).items():
        setattr(video, field, value)
    
    db.commit()
    db.refresh(video)
    return video

@router.delete("/{video_id}")
async def delete_video(video_id: int, db: Session = Depends(get_db)):
    """删除视频"""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")
    
    # 删除文件
    if video.file_path and os.path.exists(video.file_path):
        try:
            os.remove(video.file_path)
        except Exception as e:
            print(f"删除文件失败: {e}")
    
    # 删除数据库记录
    db.delete(video)
    db.commit()
    
    return {"message": "视频删除成功"}

@router.delete("/batch")
async def delete_videos_batch(
    video_ids: List[int],
    db: Session = Depends(get_db)
):
    """批量删除视频"""
    videos = db.query(Video).filter(Video.id.in_(video_ids)).all()
    
    deleted_count = 0
    for video in videos:
        # 删除文件
        if video.file_path and os.path.exists(video.file_path):
            try:
                os.remove(video.file_path)
            except Exception as e:
                print(f"删除文件失败: {e}")
        
        db.delete(video)
        deleted_count += 1
    
    db.commit()
    
    return {"message": f"成功删除 {deleted_count} 个视频"}

@router.get("/platforms")
async def get_platforms(db: Session = Depends(get_db)):
    """获取所有平台列表"""
    platforms = db.query(Video.platform).distinct().all()
    return [p[0] for p in platforms if p[0]]

@router.get("/stats")
async def get_video_stats(db: Session = Depends(get_db)):
    """获取视频统计信息"""
    total_videos = db.query(Video).count()
    analyzed_videos = db.query(Video).filter(Video.status == "analyzed").count()
    total_size = db.query(Video.file_size).filter(Video.file_size.isnot(None)).all()
    total_size_mb = sum([size[0] for size in total_size if size[0]]) / (1024 * 1024)
    
    return {
        "total_videos": total_videos,
        "analyzed_videos": analyzed_videos,
        "pending_analysis": total_videos - analyzed_videos,
        "total_size_mb": round(total_size_mb, 2)
    }