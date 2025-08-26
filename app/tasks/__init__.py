"""异步任务模块

使用Celery实现异步任务处理，包括视频下载、分析等后台任务。
"""

from app.tasks.celery_app import celery_app
from app.tasks.download_tasks import download_video_task
from app.tasks.analysis_tasks import analyze_video_task

__all__ = [
    "celery_app",
    "download_video_task",
    "analyze_video_task",
]