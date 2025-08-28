from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import uuid
import shutil
from datetime import datetime

from app.core.database import get_db
from app.models.video import Video
from app.schemas.video import VideoCreate, VideoResponse

router = APIRouter()

UPLOAD_DIR = "uploads/videos"
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv", ".webm"}

@router.post("/batch", response_model=List[VideoResponse])
async def upload_videos_batch(
    files: List[UploadFile] = File(...),
    titles: Optional[List[str]] = Form(None),
    descriptions: Optional[List[str]] = Form(None),
    auto_analyze: bool = Form(False),
    db: Session = Depends(get_db)
):
    """批量上传视频文件，支持逐一设置标题描述"""
    
    uploaded_videos = []
    
    for i, file in enumerate(files):
        # 检查文件扩展名
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400, 
                detail=f"不支持的文件格式: {file_ext}"
            )
        
        # 生成唯一文件名
        file_id = str(uuid.uuid4())
        filename = f"{file_id}{file_ext}"
        file_path = os.path.join(UPLOAD_DIR, filename)
        
        # 保存文件
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"文件保存失败: {str(e)}")
        
        # 获取文件信息
        file_size = os.path.getsize(file_path)
        
        # 获取对应的标题和描述
        title = titles[i] if titles and i < len(titles) and titles[i] else file.filename
        description = descriptions[i] if descriptions and i < len(descriptions) and descriptions[i] else None
        
        # 创建数据库记录
        video_data = VideoCreate(
            title=title,
            description=description,
            original_filename=file.filename,
            file_path=file_path,
            file_size=file_size,
            platform="local",
            status="uploaded" if not auto_analyze else "pending_analysis",
            extra_metadata={}
        )
        
        db_video = Video(**video_data.dict())
        db.add(db_video)
        db.commit()
        db.refresh(db_video)
        
        uploaded_videos.append(VideoResponse.from_orm(db_video))
        
        # 如果需要自动分析，触发分析任务
        if auto_analyze:
            # TODO: 触发分析任务
            pass
    
    return uploaded_videos

@router.post("/", response_model=VideoResponse)
async def upload_video(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    auto_analyze: bool = Form(False),
    db: Session = Depends(get_db)
):
    """单文件上传"""
    
    # 检查文件扩展名
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400, 
            detail=f"不支持的文件格式: {file_ext}"
        )
    
    # 生成唯一文件名
    file_id = str(uuid.uuid4())
    filename = f"{file_id}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    # 保存文件
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件保存失败: {str(e)}")
    
    # 获取文件信息
    file_size = os.path.getsize(file_path)
    
    # 创建数据库记录
    video_data = VideoCreate(
        title=title or file.filename,
        description=description,
        original_filename=file.filename,
        file_path=file_path,
        file_size=file_size,
        platform="local",
        status="uploaded" if not auto_analyze else "pending_analysis"
    )
    
    db_video = Video(**video_data.dict())
    db.add(db_video)
    db.commit()
    db.refresh(db_video)
    
    # 如果需要自动分析，触发分析任务
    if auto_analyze:
        # TODO: 触发分析任务
        pass
    
    return VideoResponse.from_orm(db_video)

@router.get("/status/{video_id}")
async def get_upload_status(video_id: int, db: Session = Depends(get_db)):
    """获取上传状态"""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")
    
    return {
        "id": video.id,
        "title": video.title,
        "status": video.status,
        "created_at": video.created_at
    }