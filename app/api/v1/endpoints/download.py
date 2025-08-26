"""视频下载API端点

提供视频下载任务管理相关的API接口。
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.models.video import DownloadTask
from app.schemas.common import PaginatedResponse, PaginationParams, ResponseModel
from app.schemas.video import DownloadTaskCreate, DownloadTaskResponse
from app.core.logging import download_logger

router = APIRouter()


@router.post("/tasks", response_model=ResponseModel[DownloadTaskResponse])
def create_download_task(
    task_data: DownloadTaskCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """创建下载任务
    
    创建新的视频下载任务并加入队列。
    """
    # 检查是否已存在相同URL的未完成任务
    existing_task = db.query(DownloadTask).filter(
        DownloadTask.user_id == current_user.id,
        DownloadTask.url == str(task_data.url),
        DownloadTask.status.in_(["pending", "processing"])
    ).first()
    
    if existing_task:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A download task for this URL is already in progress"
        )
    
    # 创建下载任务
    download_task = DownloadTask(
        user_id=current_user.id,
        url=str(task_data.url),
        quality=task_data.quality,
        format_preference=task_data.format_preference,
        audio_only=task_data.audio_only,
        priority=task_data.priority,
        options=task_data.options,
        status="pending"
    )
    
    db.add(download_task)
    db.commit()
    db.refresh(download_task)
    
    download_logger.info(
        "Download task created",
        user_id=current_user.id,
        task_id=download_task.id,
        url=str(task_data.url),
        priority=task_data.priority
    )
    
    # TODO: 这里应该将任务加入Celery队列
    # from app.tasks.download import download_video_task
    # download_video_task.delay(download_task.id)
    
    return ResponseModel(
        code=200,
        message="Download task created successfully",
        data=DownloadTaskResponse.from_attributes(download_task)
    )


@router.get("/tasks", response_model=ResponseModel[PaginatedResponse[DownloadTaskResponse]])
def get_download_tasks(
    pagination: PaginationParams = Depends(),
    status_filter: Optional[str] = Query(None, description="状态筛选"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """获取下载任务列表
    
    分页获取用户的下载任务列表。
    """
    # 构建查询
    query = db.query(DownloadTask).filter(
        DownloadTask.user_id == current_user.id
    )
    
    # 状态筛选
    if status_filter:
        query = query.filter(DownloadTask.status == status_filter)
    
    # 获取总数
    total = query.count()
    
    # 分页查询
    tasks = query.order_by(desc(DownloadTask.created_at)).offset(
        pagination.offset
    ).limit(pagination.size).all()
    
    # 转换为响应模型
    task_responses = [DownloadTaskResponse.from_attributes(task) for task in tasks]
    
    paginated_data = PaginatedResponse.create(
        items=task_responses,
        total=total,
        page=pagination.page,
        size=pagination.size
    )
    
    return ResponseModel(
        code=200,
        message="Download tasks retrieved successfully",
        data=paginated_data
    )


@router.get("/tasks/{task_id}", response_model=ResponseModel[DownloadTaskResponse])
def get_download_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """获取下载任务详情
    
    获取指定下载任务的详细信息。
    """
    task = db.query(DownloadTask).filter(
        DownloadTask.id == task_id,
        DownloadTask.user_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Download task not found"
        )
    
    return ResponseModel(
        code=200,
        message="Download task retrieved successfully",
        data=DownloadTaskResponse.from_attributes(task)
    )


@router.post("/tasks/{task_id}/pause", response_model=ResponseModel[dict])
def pause_download_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """暂停下载任务
    
    暂停正在进行的下载任务。
    """
    task = db.query(DownloadTask).filter(
        DownloadTask.id == task_id,
        DownloadTask.user_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Download task not found"
        )
    
    if task.status not in ["pending", "processing"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task cannot be paused in current status"
        )
    
    # TODO: 实现暂停逻辑
    # 这里应该通知Celery worker暂停任务
    
    download_logger.info(
        "Download task pause requested",
        user_id=current_user.id,
        task_id=task_id
    )
    
    return ResponseModel(
        code=200,
        message="Download task pause requested",
        data={"message": "Task pause has been requested"}
    )


@router.post("/tasks/{task_id}/resume", response_model=ResponseModel[dict])
def resume_download_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """恢复下载任务
    
    恢复已暂停的下载任务。
    """
    task = db.query(DownloadTask).filter(
        DownloadTask.id == task_id,
        DownloadTask.user_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Download task not found"
        )
    
    if task.status != "paused":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task is not paused"
        )
    
    # TODO: 实现恢复逻辑
    # 这里应该重新将任务加入Celery队列
    
    download_logger.info(
        "Download task resume requested",
        user_id=current_user.id,
        task_id=task_id
    )
    
    return ResponseModel(
        code=200,
        message="Download task resume requested",
        data={"message": "Task has been resumed"}
    )


@router.delete("/tasks/{task_id}", response_model=ResponseModel[dict])
def cancel_download_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """取消下载任务
    
    取消指定的下载任务。
    """
    task = db.query(DownloadTask).filter(
        DownloadTask.id == task_id,
        DownloadTask.user_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Download task not found"
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
    
    download_logger.info(
        "Download task cancelled",
        user_id=current_user.id,
        task_id=task_id
    )
    
    return ResponseModel(
        code=200,
        message="Download task cancelled successfully",
        data={"message": "Task has been cancelled"}
    )


@router.get("/stats", response_model=ResponseModel[dict])
def get_download_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """获取下载统计信息
    
    获取用户的下载任务统计数据。
    """
    # 统计各状态的任务数量
    stats = db.query(
        DownloadTask.status,
        db.func.count(DownloadTask.id).label('count')
    ).filter(
        DownloadTask.user_id == current_user.id
    ).group_by(DownloadTask.status).all()
    
    stats_dict = {status: count for status, count in stats}
    
    # 计算总数
    total_tasks = sum(stats_dict.values())
    
    return ResponseModel(
        code=200,
        message="Download statistics retrieved successfully",
        data={
            "total_tasks": total_tasks,
            "by_status": stats_dict,
            "success_rate": (
                stats_dict.get("completed", 0) / total_tasks * 100
                if total_tasks > 0 else 0
            )
        }
    )