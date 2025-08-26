"""视频分析API端点

提供视频分析任务管理相关的API接口。
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.models.video import AnalysisTask, Video
from app.schemas.common import PaginatedResponse, PaginationParams, ResponseModel
from app.schemas.video import AnalysisTaskCreate, AnalysisTaskResponse
from app.core.logging import analysis_logger

router = APIRouter()


@router.post("/tasks", response_model=ResponseModel[AnalysisTaskResponse])
def create_analysis_task(
    task_data: AnalysisTaskCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """创建分析任务
    
    为指定视频创建新的分析任务。
    """
    # 验证视频是否存在且属于当前用户
    video = db.query(Video).join(
        Video.download_tasks
    ).filter(
        Video.id == task_data.video_id,
        Video.download_tasks.any(user_id=current_user.id),
        Video.status == "active"
    ).first()
    
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found or access denied"
        )
    
    # 检查是否已存在未完成的分析任务
    existing_task = db.query(AnalysisTask).filter(
        AnalysisTask.user_id == current_user.id,
        AnalysisTask.video_id == task_data.video_id,
        AnalysisTask.status.in_(["pending", "processing"])
    ).first()
    
    if existing_task:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An analysis task for this video is already in progress"
        )
    
    # 创建分析任务
    analysis_task = AnalysisTask(
        user_id=current_user.id,
        video_id=task_data.video_id,
        template_id=task_data.template_id,
        analysis_type=task_data.analysis_type,
        config=task_data.config,
        status="pending"
    )
    
    db.add(analysis_task)
    db.commit()
    db.refresh(analysis_task)
    
    analysis_logger.info(
        "Analysis task created",
        user_id=current_user.id,
        task_id=analysis_task.id,
        video_id=task_data.video_id,
        analysis_type=task_data.analysis_type
    )
    
    # TODO: 这里应该将任务加入Celery队列
    # from app.tasks.analysis import analyze_video_task
    # analyze_video_task.delay(analysis_task.id)
    
    return ResponseModel(
        code=200,
        message="Analysis task created successfully",
        data=AnalysisTaskResponse.from_attributes(analysis_task)
    )


@router.get("/tasks", response_model=ResponseModel[PaginatedResponse[AnalysisTaskResponse]])
def get_analysis_tasks(
    pagination: PaginationParams = Depends(),
    status_filter: Optional[str] = Query(None, description="状态筛选"),
    video_id: Optional[int] = Query(None, description="视频ID筛选"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """获取分析任务列表
    
    分页获取用户的分析任务列表。
    """
    # 构建查询
    query = db.query(AnalysisTask).filter(
        AnalysisTask.user_id == current_user.id
    )
    
    # 状态筛选
    if status_filter:
        query = query.filter(AnalysisTask.status == status_filter)
    
    # 视频ID筛选
    if video_id:
        query = query.filter(AnalysisTask.video_id == video_id)
    
    # 获取总数
    total = query.count()
    
    # 分页查询
    tasks = query.order_by(desc(AnalysisTask.created_at)).offset(
        pagination.offset
    ).limit(pagination.size).all()
    
    # 转换为响应模型
    task_responses = [AnalysisTaskResponse.from_attributes(task) for task in tasks]
    
    paginated_data = PaginatedResponse.create(
        items=task_responses,
        total=total,
        page=pagination.page,
        size=pagination.size
    )
    
    return ResponseModel(
        code=200,
        message="Analysis tasks retrieved successfully",
        data=paginated_data
    )


@router.get("/tasks/{task_id}", response_model=ResponseModel[AnalysisTaskResponse])
def get_analysis_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """获取分析任务详情
    
    获取指定分析任务的详细信息。
    """
    task = db.query(AnalysisTask).filter(
        AnalysisTask.id == task_id,
        AnalysisTask.user_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis task not found"
        )
    
    return ResponseModel(
        code=200,
        message="Analysis task retrieved successfully",
        data=AnalysisTaskResponse.from_attributes(task)
    )


@router.get("/tasks/{task_id}/result", response_model=ResponseModel[dict])
def get_analysis_result(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """获取分析结果
    
    获取指定分析任务的详细结果数据。
    """
    task = db.query(AnalysisTask).filter(
        AnalysisTask.id == task_id,
        AnalysisTask.user_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis task not found"
        )
    
    if task.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Analysis task is not completed yet"
        )
    
    return ResponseModel(
        code=200,
        message="Analysis result retrieved successfully",
        data={
            "task_id": task.id,
            "video_id": task.video_id,
            "analysis_type": task.analysis_type,
            "result_data": task.result_data,
            "result_summary": task.result_summary,
            "confidence_score": task.confidence_score,
            "completed_at": task.completed_at
        }
    )


@router.post("/tasks/{task_id}/export", response_model=ResponseModel[dict])
def export_analysis_result(
    task_id: int,
    format: str = Query("json", description="导出格式"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """导出分析结果
    
    将分析结果导出为指定格式。
    """
    task = db.query(AnalysisTask).filter(
        AnalysisTask.id == task_id,
        AnalysisTask.user_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis task not found"
        )
    
    if task.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Analysis task is not completed yet"
        )
    
    # 验证导出格式
    allowed_formats = ["json", "csv", "pdf", "markdown"]
    if format not in allowed_formats:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported format. Allowed formats: {', '.join(allowed_formats)}"
        )
    
    # TODO: 实现实际的导出逻辑
    # 这里应该根据格式生成相应的文件并返回下载链接
    
    analysis_logger.info(
        "Analysis result export requested",
        user_id=current_user.id,
        task_id=task_id,
        format=format
    )
    
    return ResponseModel(
        code=200,
        message="Export request processed successfully",
        data={
            "message": f"Analysis result will be exported as {format}",
            "download_url": f"/api/v1/analysis/downloads/{task_id}.{format}"
        }
    )


@router.delete("/tasks/{task_id}", response_model=ResponseModel[dict])
def cancel_analysis_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """取消分析任务
    
    取消指定的分析任务。
    """
    task = db.query(AnalysisTask).filter(
        AnalysisTask.id == task_id,
        AnalysisTask.user_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis task not found"
        )
    
    if task.status in ["completed", "cancelled"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task cannot be cancelled in current status"
        )
    
    # 更新任务状态
    task.status = "cancelled"
    db.commit()
    
    # TODO: 通知Celery worker取消任务
    
    analysis_logger.info(
        "Analysis task cancelled",
        user_id=current_user.id,
        task_id=task_id
    )
    
    return ResponseModel(
        code=200,
        message="Analysis task cancelled successfully",
        data={"message": "Task has been cancelled"}
    )


@router.get("/stats", response_model=ResponseModel[dict])
def get_analysis_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """获取分析统计信息
    
    获取用户的分析任务统计数据。
    """
    # 统计各状态的任务数量
    stats = db.query(
        AnalysisTask.status,
        db.func.count(AnalysisTask.id).label('count')
    ).filter(
        AnalysisTask.user_id == current_user.id
    ).group_by(AnalysisTask.status).all()
    
    stats_dict = {status: count for status, count in stats}
    
    # 统计各分析类型的数量
    type_stats = db.query(
        AnalysisTask.analysis_type,
        db.func.count(AnalysisTask.id).label('count')
    ).filter(
        AnalysisTask.user_id == current_user.id
    ).group_by(AnalysisTask.analysis_type).all()
    
    type_stats_dict = {analysis_type: count for analysis_type, count in type_stats}
    
    # 计算总数
    total_tasks = sum(stats_dict.values())
    
    return ResponseModel(
        code=200,
        message="Analysis statistics retrieved successfully",
        data={
            "total_tasks": total_tasks,
            "by_status": stats_dict,
            "by_type": type_stats_dict,
            "success_rate": (
                stats_dict.get("completed", 0) / total_tasks * 100
                if total_tasks > 0 else 0
            )
        }
    )