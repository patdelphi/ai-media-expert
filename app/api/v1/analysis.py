from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import json
import asyncio
from datetime import datetime

from app.core.database import get_db
from app.models.video import Video, AnalysisTask
from app.models.user import User
from app.schemas.video import AnalysisRequest, AnalysisResponse
from app.services.analysis_service import AnalysisService
from app.api.deps import get_current_user

router = APIRouter()

@router.post("/start/{video_id}", response_model=AnalysisResponse)
async def start_analysis(
    video_id: int,
    analysis_request: AnalysisRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """开始视频分析"""
    
    # 检查视频是否存在
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")
    
    # 检查是否已有进行中的分析任务
    existing_task = db.query(AnalysisTask).filter(
        AnalysisTask.video_id == video_id,
        AnalysisTask.status == "running"
    ).first()
    
    if existing_task:
        raise HTTPException(status_code=400, detail="该视频已有分析任务在进行中")
    
    # 创建分析任务
    task = AnalysisTask(
        user_id=current_user.id,
        video_id=video_id,
        analysis_types=json.dumps(analysis_request.analysis_types),
        ai_config_id=analysis_request.ai_config_id,
        status="pending",
        progress=0
    )
    
    db.add(task)
    db.commit()
    db.refresh(task)
    
    # 启动后台分析任务
    background_tasks.add_task(
        run_analysis_task,
        task.id,
        video.file_path,
        analysis_request.analysis_types,
        analysis_request.ai_config_id
    )
    
    return AnalysisResponse(
        task_id=task.id,
        video_id=video_id,
        status="pending",
        progress=0,
        message="分析任务已启动"
    )

@router.get("/status/{task_id}", response_model=AnalysisResponse)
async def get_analysis_status(
    task_id: int,
    db: Session = Depends(get_db)
):
    """获取分析任务状态"""
    
    task = db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="分析任务不存在")
    
    return AnalysisResponse(
        task_id=task.id,
        video_id=task.video_id,
        status=task.status,
        progress=task.progress,
        results=json.loads(task.results) if task.results else None,
        error_message=task.error_message
    )

@router.get("/results/{video_id}")
async def get_analysis_results(
    video_id: int,
    db: Session = Depends(get_db)
):
    """获取视频分析结果"""
    
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")
    
    # 获取最新的完成分析任务
    task = db.query(AnalysisTask).filter(
        AnalysisTask.video_id == video_id,
        AnalysisTask.status == "completed"
    ).order_by(AnalysisTask.created_at.desc()).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="该视频暂无分析结果")
    
    return {
        "video_id": video_id,
        "video_title": video.title,
        "analysis_results": json.loads(task.results) if task.results else {},
        "analyzed_at": task.completed_at,
        "analysis_types": json.loads(task.analysis_types)
    }

@router.get("/tasks")
async def get_analysis_tasks(
    skip: int = 0,
    limit: int = 20,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取分析任务列表"""
    
    query = db.query(AnalysisTask).join(Video)
    
    if status:
        query = query.filter(AnalysisTask.status == status)
    
    tasks = query.order_by(AnalysisTask.created_at.desc()).offset(skip).limit(limit).all()
    
    result = []
    for task in tasks:
        result.append({
            "id": task.id,
            "video_id": task.video_id,
            "video_title": task.video.title,
            "status": task.status,
            "progress": task.progress,
            "analysis_types": json.loads(task.analysis_types),
            "created_at": task.created_at,
            "completed_at": task.completed_at
        })
    
    return result

@router.delete("/tasks/{task_id}")
async def cancel_analysis_task(
    task_id: int,
    db: Session = Depends(get_db)
):
    """取消分析任务"""
    
    task = db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="分析任务不存在")
    
    if task.status in ["completed", "failed", "cancelled"]:
        raise HTTPException(status_code=400, detail="任务已完成或已取消")
    
    task.status = "cancelled"
    task.completed_at = datetime.utcnow()
    db.commit()
    
    return {"message": "分析任务已取消"}

@router.post("/batch")
async def start_batch_analysis(
    video_ids: List[int],
    analysis_request: AnalysisRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """批量开始分析"""
    
    task_ids = []
    
    for video_id in video_ids:
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            continue
        
        # 检查是否已有进行中的任务
        existing_task = db.query(AnalysisTask).filter(
            AnalysisTask.video_id == video_id,
            AnalysisTask.status == "running"
        ).first()
        
        if existing_task:
            continue
        
        # 创建分析任务
        task = AnalysisTask(
            user_id=current_user.id,
            video_id=video_id,
            analysis_types=json.dumps(analysis_request.analysis_types),
            ai_config_id=analysis_request.ai_config_id,
            status="pending",
            progress=0
        )
        
        db.add(task)
        db.commit()
        db.refresh(task)
        
        task_ids.append(task.id)
        
        # 启动后台分析任务
        background_tasks.add_task(
            run_analysis_task,
            task.id,
            video.file_path,
            analysis_request.analysis_types,
            analysis_request.ai_config_id
        )
    
    return {
        "message": f"已启动 {len(task_ids)} 个分析任务",
        "task_ids": task_ids
    }

async def run_analysis_task(
    task_id: int,
    video_path: str,
    analysis_types: List[str],
    ai_config_id: int
):
    """运行分析任务（后台任务）"""
    
    from app.core.database import SessionLocal
    db = SessionLocal()
    
    try:
        # 更新任务状态
        task = db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()
        if not task:
            return
        
        task.status = "running"
        task.started_at = datetime.utcnow()
        db.commit()
        
        # 执行分析
        analysis_service = AnalysisService()
        results = await analysis_service.analyze_video(
            video_path=video_path,
            analysis_types=analysis_types,
            ai_config_id=ai_config_id,
            progress_callback=lambda p: update_task_progress(task_id, p)
        )
        
        # 更新任务结果
        task.status = "completed"
        task.progress = 100
        task.results = json.dumps(results)
        task.completed_at = datetime.utcnow()
        
        # 更新视频状态
        video = db.query(Video).filter(Video.id == task.video_id).first()
        if video:
            video.status = "analyzed"
            video.analysis_results = json.dumps(results)
        
        db.commit()
        
    except Exception as e:
        # 更新任务错误状态
        task.status = "failed"
        task.error_message = str(e)
        task.completed_at = datetime.utcnow()
        db.commit()
        
    finally:
        db.close()

def update_task_progress(task_id: int, progress: int):
    """更新任务进度"""
    from app.core.database import SessionLocal
    db = SessionLocal()
    
    try:
        task = db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()
        if task:
            task.progress = progress
            db.commit()
    finally:
        db.close()