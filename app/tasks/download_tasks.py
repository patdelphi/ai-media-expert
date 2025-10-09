"""视频下载异步任务

使用Celery实现视频下载的异步处理，支持进度跟踪和错误处理。
"""

from datetime import datetime, timedelta
from typing import Dict, Optional
from pathlib import Path
import asyncio
import traceback

from celery import current_task
from sqlalchemy.orm import Session

from app.tasks.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.video import Video, DownloadTask
from app.services.download_service import DownloadService
from app.services.download_api_client import get_download_api_client
from app.core.config import settings
from app.core.app_logging import get_logger

download_logger = get_logger("download_tasks")


@celery_app.task(bind=True, name="download_video")
def download_video_task(self, task_id: int) -> Dict:
    """下载视频任务
    
    Args:
        task_id: 下载任务ID
    
    Returns:
        任务执行结果
    """
    db = SessionLocal()
    
    try:
        # 获取下载任务
        task = db.query(DownloadTask).filter(DownloadTask.id == task_id).first()
        if not task:
            raise Exception(f"Download task {task_id} not found")
        
        # 更新任务状态为处理中
        task.status = "processing"
        task.started_at = datetime.utcnow()
        task.progress = 0
        db.commit()
        
        download_logger.info(
            "Starting video download",
            task_id=task_id,
            url=task.url,
            user_id=task.user_id
        )
        
        # 使用异步函数处理下载
        result = asyncio.run(_download_video_async(task, db))
        
        return result
        
    except Exception as e:
        # 更新任务状态为失败
        task = db.query(DownloadTask).filter(DownloadTask.id == task_id).first()
        if task:
            task.status = "failed"
            task.error_message = str(e)
            task.error_code = "TASK_ERROR"
            task.completed_at = datetime.utcnow()
            db.commit()
        
        download_logger.error(
            "Download task failed",
            task_id=task_id,
            error=str(e),
            traceback=traceback.format_exc()
        )
        
        return {
            'status': 'failed',
            'error': str(e),
            'task_id': task_id
        }
    
    finally:
        db.close()


async def _download_video_async(task: DownloadTask, db: Session) -> Dict:
    """异步下载视频处理函数
    
    Args:
        task: 下载任务对象
        db: 数据库会话
        
    Returns:
        Dict: 处理结果
    """
    download_service = None
    
    try:
        # 初始化下载服务
        download_service = DownloadService()
        
        # 处理下载任务
        result = await download_service.process_download_task(task.id)
        
        # 刷新任务状态
        db.refresh(task)
        
        if task.status == "completed":
            download_logger.info(
                "Video download completed successfully",
                task_id=task.id,
                file_path=task.file_path,
                file_size=task.file_size
            )
            
            return {
                'status': 'completed',
                'task_id': task.id,
                'file_path': task.file_path,
                'file_size': task.file_size,
                'video_id': task.video_id
            }
        else:
            return {
                'status': task.status,
                'task_id': task.id,
                'error': task.error_message,
                'error_code': task.error_code
            }
            
    except Exception as e:
        # 更新任务状态为失败
        task.status = "failed"
        task.error_message = str(e)
        task.error_code = "DOWNLOAD_ERROR"
        task.completed_at = datetime.utcnow()
        db.commit()
        
        download_logger.error(
            "Download processing failed",
            task_id=task.id,
            error=str(e),
            traceback=traceback.format_exc()
        )
        
        return {
            'status': 'failed',
            'error': str(e),
            'task_id': task.id
        }


@celery_app.task(bind=True, name="create_download_task")
def create_download_task_async(self, url: str, user_id: int, priority: str = "normal") -> Dict:
    """创建下载任务
    
    Args:
        url: 视频URL
        user_id: 用户ID
        priority: 任务优先级
        
    Returns:
        创建结果
    """
    db = SessionLocal()
    
    try:
        download_service = DownloadService()
        
        # 异步创建下载任务
        result = asyncio.run(_create_download_task_async(download_service, url, user_id, priority, db))
        
        return result
        
    except Exception as e:
        download_logger.error(
            "Failed to create download task",
            url=url,
            user_id=user_id,
            error=str(e)
        )
        
        return {
            'status': 'failed',
            'error': str(e)
        }
    
    finally:
        db.close()


async def _create_download_task_async(
    download_service: DownloadService, 
    url: str, 
    user_id: int, 
    priority: str,
    db: Session
) -> Dict:
    """异步创建下载任务
    
    Args:
        download_service: 下载服务实例
        url: 视频URL
        user_id: 用户ID
        priority: 任务优先级
        db: 数据库会话
        
    Returns:
        创建结果
    """
    try:
        # 提取视频信息
        video_info = await download_service.extract_video_info(url)
        
        # 创建下载任务
        task = await download_service.create_download_task(
            url=url,
            user_id=user_id,
            priority=priority,
            video_info=video_info
        )
        
        download_logger.info(
            "Download task created successfully",
            task_id=task.id,
            url=url,
            user_id=user_id,
            title=video_info.get('title', 'Unknown')
        )
        
        return {
            'status': 'created',
            'task_id': task.id,
            'video_info': video_info
        }
        
    except Exception as e:
        download_logger.error(
            "Failed to create download task",
            url=url,
            user_id=user_id,
            error=str(e)
        )
        
        return {
            'status': 'failed',
            'error': str(e)
        }


@celery_app.task(name="cleanup_old_tasks")
def cleanup_old_tasks() -> Dict:
    """清理旧的下载任务
    
    Returns:
        清理结果
    """
    db = SessionLocal()
    
    try:
        # 清理7天前的已完成任务
        cutoff_date = datetime.utcnow() - timedelta(days=7)
        
        old_tasks = db.query(DownloadTask).filter(
            DownloadTask.status.in_(["completed", "failed"]),
            DownloadTask.completed_at < cutoff_date
        ).all()
        
        cleaned_count = 0
        for task in old_tasks:
            # 删除文件（如果存在）
            if task.file_path and Path(task.file_path).exists():
                try:
                    Path(task.file_path).unlink()
                except Exception as e:
                    download_logger.warning(
                        "Failed to delete file",
                        file_path=task.file_path,
                        error=str(e)
                    )
            
            # 删除任务记录
            db.delete(task)
            cleaned_count += 1
        
        db.commit()
        
        download_logger.info(
            "Cleaned up old download tasks",
            cleaned_count=cleaned_count
        )
        
        return {
            'status': 'completed',
            'cleaned_count': cleaned_count
        }
        
    except Exception as e:
        db.rollback()
        download_logger.error(
            "Failed to cleanup old tasks",
            error=str(e)
        )
        
        return {
            'status': 'failed',
            'error': str(e)
        }
    
    finally:
        db.close()


@celery_app.task(name="get_task_status")
def get_task_status(task_id: int) -> Dict:
    """获取任务状态
    
    Args:
        task_id: 任务ID
        
    Returns:
        任务状态信息
    """
    db = SessionLocal()
    
    try:
        task = db.query(DownloadTask).filter(DownloadTask.id == task_id).first()
        
        if not task:
            return {
                'status': 'not_found',
                'error': f'Task {task_id} not found'
            }
        
        return {
            'status': task.status,
            'progress': task.progress,
            'file_size': task.file_size,
            'downloaded_size': task.downloaded_size,
            'download_speed': task.download_speed,
            'eta': task.eta,
            'error_message': task.error_message,
            'error_code': task.error_code,
            'started_at': task.started_at.isoformat() if task.started_at else None,
            'completed_at': task.completed_at.isoformat() if task.completed_at else None
        }
        
    except Exception as e:
        download_logger.error(
            "Failed to get task status",
            task_id=task_id,
            error=str(e)
        )
        
        return {
            'status': 'error',
            'error': str(e)
        }
    
    finally:
        db.close()