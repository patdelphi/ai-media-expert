"""视频下载异步任务

使用Celery实现视频下载的异步处理。
"""

import os
from datetime import datetime
from typing import Dict, Optional

from celery import current_task
from sqlalchemy.orm import sessionmaker

from app.core.database import engine
from app.core.app_logging import download_logger
from app.models.video import DownloadTask, Video
from app.services.download_service import DownloadService
from app.tasks.celery_app import celery_app

# 创建数据库会话
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@celery_app.task(bind=True, name="download_video")
def download_video_task(self, task_id: int) -> Dict:
    """下载视频任务
    
    Args:
        task_id: 下载任务ID
    
    Returns:
        任务执行结果
    """
    db = SessionLocal()
    download_service = DownloadService()
    
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
        
        # 进度回调函数
        def progress_hook(d):
            if d['status'] == 'downloading':
                # 计算下载进度
                if 'total_bytes' in d and d['total_bytes']:
                    progress = int((d['downloaded_bytes'] / d['total_bytes']) * 100)
                elif 'total_bytes_estimate' in d and d['total_bytes_estimate']:
                    progress = int((d['downloaded_bytes'] / d['total_bytes_estimate']) * 100)
                else:
                    progress = task.progress + 1  # 增量更新
                
                # 限制进度范围
                progress = min(max(progress, 0), 95)  # 下载完成后留5%给后处理
                
                # 更新任务进度
                if progress != task.progress:
                    task.progress = progress
                    db.commit()
                    
                    # 更新Celery任务状态
                    current_task.update_state(
                        state='PROGRESS',
                        meta={
                            'current': progress,
                            'total': 100,
                            'status': f'Downloading... {progress}%'
                        }
                    )
            
            elif d['status'] == 'finished':
                download_logger.info(
                    "Download finished",
                    task_id=task_id,
                    filename=d.get('filename')
                )
        
        # 构建下载选项
        download_options = {
            'quality': task.quality,
            'format_preference': task.format_preference,
            'audio_only': task.audio_only,
        }
        
        # 如果有额外选项，合并进去
        if task.options:
            download_options.update(task.options)
        
        # 执行下载
        file_path, video_info = download_service.download_video(
            task_id=task_id,
            url=task.url,
            options=download_options,
            progress_callback=progress_hook
        )
        
        # 创建或更新视频记录
        video = create_or_update_video(db, video_info, task)
        
        # 更新任务状态为完成
        task.status = "completed"
        task.progress = 100
        task.completed_at = datetime.utcnow()
        task.video_id = video.id
        task.file_path = file_path
        task.error_message = None
        db.commit()
        
        download_logger.info(
            "Video download completed",
            task_id=task_id,
            video_id=video.id,
            file_path=file_path
        )
        
        return {
            'status': 'completed',
            'task_id': task_id,
            'video_id': video.id,
            'file_path': file_path,
            'message': 'Video downloaded successfully'
        }
        
    except Exception as e:
        error_msg = str(e)
        download_logger.error(
            "Video download failed",
            task_id=task_id,
            error=error_msg,
            exc_info=True
        )
        
        # 更新任务状态为失败
        if 'task' in locals():
            task.status = "failed"
            task.error_message = error_msg
            task.retry_count += 1
            db.commit()
        
        # 如果还有重试次数，则重试
        if hasattr(self, 'retry') and task.retry_count < task.max_retries:
            download_logger.info(
                "Retrying download task",
                task_id=task_id,
                retry_count=task.retry_count,
                max_retries=task.max_retries
            )
            raise self.retry(countdown=60 * (task.retry_count + 1))  # 递增延迟
        
        return {
            'status': 'failed',
            'task_id': task_id,
            'error': error_msg,
            'message': 'Video download failed'
        }
        
    finally:
        db.close()


def create_or_update_video(db, video_info: Dict, task: DownloadTask) -> Video:
    """创建或更新视频记录
    
    Args:
        db: 数据库会话
        video_info: 视频信息
        task: 下载任务
    
    Returns:
        视频对象
    """
    # 检查是否已存在相同的视频
    existing_video = None
    if video_info.get('video_id') and video_info.get('platform'):
        existing_video = db.query(Video).filter(
            Video.video_id == video_info['video_id'],
            Video.platform == video_info['platform']
        ).first()
    
    if existing_video:
        # 更新现有视频信息
        video = existing_video
        video.file_path = video_info.get('file_path', video.file_path)
        video.file_size = video_info.get('file_size', video.file_size)
        video.updated_at = datetime.utcnow()
    else:
        # 创建新视频记录
        video = Video(
            title=video_info.get('title', 'Unknown Title'),
            description=video_info.get('description'),
            file_path=video_info.get('file_path'),
            file_size=video_info.get('file_size'),
            duration=video_info.get('duration'),
            resolution=video_info.get('resolution'),
            format=video_info.get('ext', 'mp4'),
            platform=video_info.get('platform'),
            original_url=video_info.get('original_url'),
            video_id=video_info.get('video_id'),
            author=video_info.get('uploader'),
            author_id=video_info.get('uploader_id'),
            upload_date=video_info.get('upload_date'),
            view_count=video_info.get('view_count', 0),
            like_count=video_info.get('like_count', 0),
            comment_count=video_info.get('comment_count', 0),
            status="active",
            metadata={
                'thumbnail': video_info.get('thumbnail'),
                'formats': video_info.get('formats', []),
                'download_task_id': task.id
            }
        )
        db.add(video)
    
    db.commit()
    db.refresh(video)
    
    return video


@celery_app.task(name="batch_download_videos")
def batch_download_videos_task(task_ids: list) -> Dict:
    """批量下载视频任务
    
    Args:
        task_ids: 下载任务ID列表
    
    Returns:
        批量任务执行结果
    """
    results = []
    
    for task_id in task_ids:
        try:
            result = download_video_task.delay(task_id)
            results.append({
                'task_id': task_id,
                'celery_task_id': result.id,
                'status': 'queued'
            })
        except Exception as e:
            results.append({
                'task_id': task_id,
                'status': 'failed',
                'error': str(e)
            })
    
    download_logger.info(
        "Batch download tasks queued",
        task_count=len(task_ids),
        results=results
    )
    
    return {
        'status': 'queued',
        'total_tasks': len(task_ids),
        'results': results
    }


@celery_app.task(name="cleanup_failed_downloads")
def cleanup_failed_downloads_task() -> Dict:
    """清理失败的下载任务
    
    删除失败任务产生的临时文件。
    
    Returns:
        清理结果
    """
    db = SessionLocal()
    cleaned_count = 0
    
    try:
        # 查找失败的任务
        failed_tasks = db.query(DownloadTask).filter(
            DownloadTask.status == "failed",
            DownloadTask.file_path.isnot(None)
        ).all()
        
        for task in failed_tasks:
            if task.file_path and os.path.exists(task.file_path):
                try:
                    os.remove(task.file_path)
                    task.file_path = None
                    cleaned_count += 1
                    download_logger.info(
                        "Cleaned up failed download file",
                        task_id=task.id,
                        file_path=task.file_path
                    )
                except OSError as e:
                    download_logger.warning(
                        "Failed to clean up file",
                        task_id=task.id,
                        file_path=task.file_path,
                        error=str(e)
                    )
        
        db.commit()
        
        return {
            'status': 'completed',
            'cleaned_files': cleaned_count,
            'message': f'Cleaned up {cleaned_count} failed download files'
        }
        
    except Exception as e:
        download_logger.error(
            "Failed to cleanup failed downloads",
            error=str(e),
            exc_info=True
        )
        return {
            'status': 'failed',
            'error': str(e),
            'message': 'Failed to cleanup failed downloads'
        }
    
    finally:
        db.close()