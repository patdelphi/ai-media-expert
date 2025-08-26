"""Celery应用配置

配置和初始化Celery应用实例。
"""

from celery import Celery

from app.core.config import settings

# 创建Celery应用实例
celery_app = Celery(
    "ai_media_expert",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "app.tasks.download_tasks",
        "app.tasks.analysis_tasks",
    ]
)

# Celery配置
celery_app.conf.update(
    # 任务序列化
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    
    # 时区设置
    timezone="UTC",
    enable_utc=True,
    
    # 任务路由
    task_routes={
        "app.tasks.download_tasks.*": {"queue": "download"},
        "app.tasks.analysis_tasks.*": {"queue": "analysis"},
    },
    
    # 任务结果过期时间（秒）
    result_expires=3600,
    
    # 任务超时时间（秒）
    task_time_limit=3600,  # 1小时
    task_soft_time_limit=3300,  # 55分钟软限制
    
    # Worker配置
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    
    # 任务确认
    task_acks_late=True,
    worker_disable_rate_limits=False,
    
    # 任务重试
    task_default_retry_delay=60,  # 60秒
    task_max_retries=3,
    
    # 监控
    worker_send_task_events=True,
    task_send_sent_event=True,
    
    # 任务压缩
    task_compression="gzip",
    result_compression="gzip",
    
    # 定时任务
    beat_schedule={
        # 清理过期任务
        'cleanup-expired-tasks': {
            'task': 'app.tasks.maintenance_tasks.cleanup_expired_tasks',
            'schedule': 3600.0,  # 每小时执行一次
        },
        # 清理临时文件
        'cleanup-temp-files': {
            'task': 'app.tasks.maintenance_tasks.cleanup_temp_files',
            'schedule': 86400.0,  # 每天执行一次
        },
    },
)

# 任务发现
celery_app.autodiscover_tasks([
    'app.tasks.download_tasks',
    'app.tasks.analysis_tasks',
    'app.tasks.maintenance_tasks',
])


@celery_app.task(bind=True)
def debug_task(self):
    """调试任务"""
    print(f'Request: {self.request!r}')
    return 'Debug task completed'