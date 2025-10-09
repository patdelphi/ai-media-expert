"""下载队列管理API端点

提供下载队列状态监控和管理相关的API接口。
"""

from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.common import ResponseModel, PaginatedResponse, PaginationParams
from app.core.app_logging import download_logger

router = APIRouter()


@router.get("/queue", response_model=ResponseModel[PaginatedResponse[dict]])
def get_download_queue(
    pagination: PaginationParams = Depends(),
    status_filter: Optional[str] = Query(None, description="队列状态筛选"),
    priority_filter: Optional[int] = Query(None, description="优先级筛选"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """获取下载队列状态
    
    分页获取用户的下载队列状态信息。
    """
    try:
        # 构建基础查询
        base_query = """
        SELECT 
            dq.id,
            dq.task_id,
            dq.priority,
            dq.status,
            dq.worker_id,
            dq.started_at,
            dq.completed_at,
            dq.created_at,
            dt.url,
            dt.platform,
            dt.video_title,
            dt.status as task_status,
            dt.progress,
            dt.error_message
        FROM download_queue dq
        JOIN download_tasks dt ON dq.task_id = dt.id
        WHERE dt.user_id = ?
        """
        
        params = [current_user.id]
        
        # 添加筛选条件
        if status_filter:
            base_query += " AND dq.status = ?"
            params.append(status_filter)
        
        if priority_filter is not None:
            base_query += " AND dq.priority = ?"
            params.append(priority_filter)
        
        # 获取总数
        count_query = f"SELECT COUNT(*) FROM ({base_query}) as subquery"
        result = db.execute(count_query, params)
        total = result.fetchone()[0]
        
        # 分页查询
        paginated_query = f"{base_query} ORDER BY dq.priority ASC, dq.created_at ASC LIMIT ? OFFSET ?"
        params.extend([pagination.size, pagination.offset])
        
        result = db.execute(paginated_query, params)
        queue_rows = result.fetchall()
        
        # 构建响应数据
        queue_items = []
        for row in queue_rows:
            queue_item = {
                "queue_id": row[0],
                "task_id": row[1],
                "priority": row[2],
                "queue_status": row[3],
                "worker_id": row[4],
                "started_at": row[5].isoformat() if row[5] else None,
                "completed_at": row[6].isoformat() if row[6] else None,
                "created_at": row[7].isoformat() if row[7] else None,
                "task_info": {
                    "url": row[8],
                    "platform": row[9],
                    "video_title": row[10],
                    "task_status": row[11],
                    "progress": row[12] or 0,
                    "error_message": row[13]
                }
            }
            queue_items.append(queue_item)
        
        paginated_data = PaginatedResponse.create(
            items=queue_items,
            total=total,
            page=pagination.page,
            size=pagination.size
        )
        
        download_logger.info(
            "Download queue retrieved",
            user_id=current_user.id,
            total_items=total,
            page=pagination.page
        )
        
        return ResponseModel(
            code=200,
            message="Download queue retrieved successfully",
            data=paginated_data
        )
        
    except Exception as e:
        download_logger.error(
            "Failed to retrieve download queue",
            user_id=current_user.id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve download queue"
        )


@router.get("/queue/summary", response_model=ResponseModel[dict])
def get_queue_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """获取队列状态摘要
    
    获取用户下载队列的状态摘要信息。
    """
    try:
        # 查询队列状态统计
        queue_stats_query = """
        SELECT 
            dq.status,
            COUNT(*) as count,
            AVG(dq.priority) as avg_priority
        FROM download_queue dq
        JOIN download_tasks dt ON dq.task_id = dt.id
        WHERE dt.user_id = ?
        GROUP BY dq.status
        """
        
        result = db.execute(queue_stats_query, (current_user.id,))
        status_rows = result.fetchall()
        
        # 查询优先级分布
        priority_stats_query = """
        SELECT 
            dq.priority,
            COUNT(*) as count
        FROM download_queue dq
        JOIN download_tasks dt ON dq.task_id = dt.id
        WHERE dt.user_id = ?
        GROUP BY dq.priority
        ORDER BY dq.priority ASC
        """
        
        result = db.execute(priority_stats_query, (current_user.id,))
        priority_rows = result.fetchall()
        
        # 查询活跃工作进程
        worker_stats_query = """
        SELECT 
            dq.worker_id,
            COUNT(*) as active_tasks
        FROM download_queue dq
        JOIN download_tasks dt ON dq.task_id = dt.id
        WHERE dt.user_id = ? AND dq.status = 'processing' AND dq.worker_id IS NOT NULL
        GROUP BY dq.worker_id
        """
        
        result = db.execute(worker_stats_query, (current_user.id,))
        worker_rows = result.fetchall()
        
        # 构建摘要数据
        summary_data = {
            "status_distribution": [
                {
                    "status": row[0],
                    "count": row[1],
                    "avg_priority": round(row[2], 2) if row[2] else 0
                }
                for row in status_rows
            ],
            "priority_distribution": [
                {
                    "priority": row[0],
                    "count": row[1]
                }
                for row in priority_rows
            ],
            "active_workers": [
                {
                    "worker_id": row[0],
                    "active_tasks": row[1]
                }
                for row in worker_rows
            ],
            "totals": {
                "total_queued": sum(row[1] for row in status_rows if row[0] == 'queued'),
                "total_processing": sum(row[1] for row in status_rows if row[0] == 'processing'),
                "total_completed": sum(row[1] for row in status_rows if row[0] == 'completed'),
                "total_failed": sum(row[1] for row in status_rows if row[0] == 'failed'),
                "active_workers_count": len(worker_rows)
            }
        }
        
        download_logger.info(
            "Queue summary retrieved",
            user_id=current_user.id,
            total_items=sum(row[1] for row in status_rows)
        )
        
        return ResponseModel(
            code=200,
            message="Queue summary retrieved successfully",
            data=summary_data
        )
        
    except Exception as e:
        download_logger.error(
            "Failed to retrieve queue summary",
            user_id=current_user.id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve queue summary"
        )


@router.put("/queue/{queue_id}/priority", response_model=ResponseModel[dict])
def update_queue_priority(
    queue_id: int,
    new_priority: int = Query(..., description="新的优先级", ge=1, le=10),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """更新队列项优先级
    
    更新指定队列项的优先级。
    """
    try:
        # 检查队列项是否存在且属于当前用户
        check_query = """
        SELECT dq.priority, dq.status
        FROM download_queue dq
        JOIN download_tasks dt ON dq.task_id = dt.id
        WHERE dq.id = ? AND dt.user_id = ?
        """
        
        result = db.execute(check_query, (queue_id, current_user.id))
        row = result.fetchone()
        
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Queue item not found"
            )
        
        old_priority = row[0]
        queue_status = row[1]
        
        # 检查是否可以修改优先级
        if queue_status in ['processing', 'completed']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot change priority for {queue_status} tasks"
            )
        
        # 更新优先级
        update_query = """
        UPDATE download_queue 
        SET priority = ?, updated_at = CURRENT_TIMESTAMP 
        WHERE id = ?
        """
        db.execute(update_query, (new_priority, queue_id))
        db.commit()
        
        download_logger.info(
            "Queue priority updated",
            user_id=current_user.id,
            queue_id=queue_id,
            old_priority=old_priority,
            new_priority=new_priority
        )
        
        return ResponseModel(
            code=200,
            message="Queue priority updated successfully",
            data={
                "queue_id": queue_id,
                "old_priority": old_priority,
                "new_priority": new_priority
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        download_logger.error(
            "Failed to update queue priority",
            user_id=current_user.id,
            queue_id=queue_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update queue priority"
        )


@router.delete("/queue/{queue_id}", response_model=ResponseModel[dict])
def cancel_queue_item(
    queue_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """取消队列项
    
    取消指定的队列项（仅限未开始处理的任务）。
    """
    try:
        # 检查队列项状态
        check_query = """
        SELECT dq.status, dq.task_id
        FROM download_queue dq
        JOIN download_tasks dt ON dq.task_id = dt.id
        WHERE dq.id = ? AND dt.user_id = ?
        """
        
        result = db.execute(check_query, (queue_id, current_user.id))
        row = result.fetchone()
        
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Queue item not found"
            )
        
        queue_status = row[0]
        task_id = row[1]
        
        # 检查是否可以取消
        if queue_status in ['processing', 'completed']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel {queue_status} tasks"
            )
        
        # 更新队列状态为失败
        update_queue_query = """
        UPDATE download_queue 
        SET status = 'failed', completed_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP 
        WHERE id = ?
        """
        db.execute(update_queue_query, (queue_id,))
        
        # 更新任务状态为取消
        update_task_query = """
        UPDATE download_tasks 
        SET status = 'cancelled', error_message = 'Cancelled by user', updated_at = CURRENT_TIMESTAMP 
        WHERE id = ?
        """
        db.execute(update_task_query, (task_id,))
        
        db.commit()
        
        download_logger.info(
            "Queue item cancelled",
            user_id=current_user.id,
            queue_id=queue_id,
            task_id=task_id
        )
        
        return ResponseModel(
            code=200,
            message="Queue item cancelled successfully",
            data={
                "queue_id": queue_id,
                "task_id": task_id,
                "status": "cancelled"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        download_logger.error(
            "Failed to cancel queue item",
            user_id=current_user.id,
            queue_id=queue_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel queue item"
        )