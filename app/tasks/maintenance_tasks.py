"""系统维护异步任务

用于系统清理、维护和监控的后台任务。
"""

import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict

from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.database import engine
from app.core.logging import app_logger
from app.models.video import DownloadTask, AnalysisTask, Video
from app.tasks.celery_app import celery_app

# 创建数据库会话
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@celery_app.task(name="cleanup_expired_tasks")
def cleanup_expired_tasks() -> Dict:
    """清理过期任务
    
    清理超过一定时间的已完成或失败任务记录。
    
    Returns:
        清理结果
    """
    db = SessionLocal()
    
    try:
        # 设置过期时间（30天前）
        expiry_date = datetime.utcnow() - timedelta(days=30)
        
        # 清理过期的下载任务
        expired_download_tasks = db.query(DownloadTask).filter(
            DownloadTask.status.in_(["completed", "failed", "cancelled"]),
            DownloadTask.updated_at < expiry_date
        ).count()
        
        db.query(DownloadTask).filter(
            DownloadTask.status.in_(["completed", "failed", "cancelled"]),
            DownloadTask.updated_at < expiry_date
        ).delete(synchronize_session=False)
        
        # 清理过期的分析任务
        expired_analysis_tasks = db.query(AnalysisTask).filter(
            AnalysisTask.status.in_(["completed", "failed", "cancelled"]),
            AnalysisTask.updated_at < expiry_date
        ).count()
        
        db.query(AnalysisTask).filter(
            AnalysisTask.status.in_(["completed", "failed", "cancelled"]),
            AnalysisTask.updated_at < expiry_date
        ).delete(synchronize_session=False)
        
        db.commit()
        
        total_cleaned = expired_download_tasks + expired_analysis_tasks
        
        app_logger.info(
            "Expired tasks cleanup completed",
            download_tasks_cleaned=expired_download_tasks,
            analysis_tasks_cleaned=expired_analysis_tasks,
            total_cleaned=total_cleaned
        )
        
        return {
            'status': 'completed',
            'download_tasks_cleaned': expired_download_tasks,
            'analysis_tasks_cleaned': expired_analysis_tasks,
            'total_cleaned': total_cleaned,
            'message': f'Cleaned up {total_cleaned} expired tasks'
        }
        
    except Exception as e:
        app_logger.error(
            "Failed to cleanup expired tasks",
            error=str(e),
            exc_info=True
        )
        
        return {
            'status': 'failed',
            'error': str(e),
            'message': 'Failed to cleanup expired tasks'
        }
        
    finally:
        db.close()


@celery_app.task(name="cleanup_temp_files")
def cleanup_temp_files() -> Dict:
    """清理临时文件
    
    清理下载目录中的临时文件和孤儿文件。
    
    Returns:
        清理结果
    """
    db = SessionLocal()
    
    try:
        cleaned_files = 0
        cleaned_size = 0
        
        # 获取所有有效的文件路径
        valid_files = set()
        
        # 从视频表获取有效文件
        videos = db.query(Video).filter(Video.status == "active").all()
        for video in videos:
            if video.file_path and os.path.exists(video.file_path):
                valid_files.add(os.path.abspath(video.file_path))
        
        # 扫描下载目录
        download_dir = Path(settings.download_dir)
        if download_dir.exists():
            for file_path in download_dir.rglob('*'):
                if file_path.is_file():
                    abs_path = str(file_path.absolute())
                    
                    # 检查文件是否在有效文件列表中
                    if abs_path not in valid_files:
                        # 检查文件是否超过7天未修改
                        file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                        if datetime.utcnow() - file_mtime > timedelta(days=7):
                            try:
                                file_size = file_path.stat().st_size
                                file_path.unlink()
                                cleaned_files += 1
                                cleaned_size += file_size
                                
                                app_logger.debug(
                                    "Cleaned up temp file",
                                    file_path=str(file_path),
                                    size=file_size
                                )
                            except OSError as e:
                                app_logger.warning(
                                    "Failed to delete temp file",
                                    file_path=str(file_path),
                                    error=str(e)
                                )
        
        # 清理空目录
        empty_dirs = 0
        for dir_path in download_dir.rglob('*'):
            if dir_path.is_dir() and not any(dir_path.iterdir()):
                try:
                    dir_path.rmdir()
                    empty_dirs += 1
                except OSError:
                    pass
        
        app_logger.info(
            "Temp files cleanup completed",
            cleaned_files=cleaned_files,
            cleaned_size=cleaned_size,
            empty_dirs_removed=empty_dirs
        )
        
        return {
            'status': 'completed',
            'cleaned_files': cleaned_files,
            'cleaned_size': cleaned_size,
            'empty_dirs_removed': empty_dirs,
            'message': f'Cleaned up {cleaned_files} temp files ({cleaned_size} bytes)'
        }
        
    except Exception as e:
        app_logger.error(
            "Failed to cleanup temp files",
            error=str(e),
            exc_info=True
        )
        
        return {
            'status': 'failed',
            'error': str(e),
            'message': 'Failed to cleanup temp files'
        }
        
    finally:
        db.close()


@celery_app.task(name="system_health_check")
def system_health_check() -> Dict:
    """系统健康检查
    
    检查系统各组件的健康状态。
    
    Returns:
        健康检查结果
    """
    health_status = {
        'database': False,
        'redis': False,
        'disk_space': False,
        'memory': False
    }
    
    issues = []
    
    try:
        # 检查数据库连接
        db = SessionLocal()
        try:
            db.execute("SELECT 1")
            health_status['database'] = True
        except Exception as e:
            issues.append(f"Database connection failed: {str(e)}")
        finally:
            db.close()
        
        # 检查Redis连接
        try:
            import redis
            r = redis.from_url(settings.redis_url)
            r.ping()
            health_status['redis'] = True
        except Exception as e:
            issues.append(f"Redis connection failed: {str(e)}")
        
        # 检查磁盘空间
        try:
            download_dir = Path(settings.download_dir)
            if download_dir.exists():
                stat = shutil.disk_usage(download_dir)
                free_space_gb = stat.free / (1024**3)
                if free_space_gb > 1:  # 至少1GB可用空间
                    health_status['disk_space'] = True
                else:
                    issues.append(f"Low disk space: {free_space_gb:.2f}GB available")
            else:
                issues.append("Download directory does not exist")
        except Exception as e:
            issues.append(f"Disk space check failed: {str(e)}")
        
        # 检查内存使用
        try:
            import psutil
            memory = psutil.virtual_memory()
            if memory.percent < 90:  # 内存使用率低于90%
                health_status['memory'] = True
            else:
                issues.append(f"High memory usage: {memory.percent:.1f}%")
        except Exception as e:
            issues.append(f"Memory check failed: {str(e)}")
        
        # 计算整体健康状态
        healthy_components = sum(health_status.values())
        total_components = len(health_status)
        overall_health = healthy_components / total_components
        
        status = 'healthy' if overall_health >= 0.75 else 'degraded' if overall_health >= 0.5 else 'unhealthy'
        
        app_logger.info(
            "System health check completed",
            status=status,
            health_score=overall_health,
            issues=issues
        )
        
        return {
            'status': status,
            'health_score': overall_health,
            'components': health_status,
            'issues': issues,
            'timestamp': datetime.utcnow().isoformat(),
            'message': f'System is {status}'
        }
        
    except Exception as e:
        app_logger.error(
            "System health check failed",
            error=str(e),
            exc_info=True
        )
        
        return {
            'status': 'error',
            'error': str(e),
            'message': 'Health check failed'
        }


@celery_app.task(name="generate_system_report")
def generate_system_report() -> Dict:
    """生成系统报告
    
    生成系统使用统计和性能报告。
    
    Returns:
        系统报告
    """
    db = SessionLocal()
    
    try:
        # 统计数据
        stats = {}
        
        # 用户统计
        from app.models.user import User
        stats['users'] = {
            'total': db.query(User).count(),
            'active': db.query(User).filter(User.is_active == True).count(),
            'verified': db.query(User).filter(User.is_verified == True).count()
        }
        
        # 视频统计
        stats['videos'] = {
            'total': db.query(Video).count(),
            'active': db.query(Video).filter(Video.status == 'active').count(),
            'analyzed': db.query(Video).filter(Video.is_analyzed == True).count()
        }
        
        # 下载任务统计
        stats['download_tasks'] = {
            'total': db.query(DownloadTask).count(),
            'completed': db.query(DownloadTask).filter(DownloadTask.status == 'completed').count(),
            'failed': db.query(DownloadTask).filter(DownloadTask.status == 'failed').count(),
            'pending': db.query(DownloadTask).filter(DownloadTask.status == 'pending').count()
        }
        
        # 分析任务统计
        stats['analysis_tasks'] = {
            'total': db.query(AnalysisTask).count(),
            'completed': db.query(AnalysisTask).filter(AnalysisTask.status == 'completed').count(),
            'failed': db.query(AnalysisTask).filter(AnalysisTask.status == 'failed').count(),
            'pending': db.query(AnalysisTask).filter(AnalysisTask.status == 'pending').count()
        }
        
        # 平台统计
        platform_stats = db.query(
            Video.platform,
            db.func.count(Video.id).label('count')
        ).filter(
            Video.platform.isnot(None)
        ).group_by(Video.platform).all()
        
        stats['platforms'] = {platform: count for platform, count in platform_stats}
        
        # 存储统计
        try:
            download_dir = Path(settings.download_dir)
            if download_dir.exists():
                total_size = sum(f.stat().st_size for f in download_dir.rglob('*') if f.is_file())
                file_count = sum(1 for f in download_dir.rglob('*') if f.is_file())
                
                stats['storage'] = {
                    'total_size_bytes': total_size,
                    'total_size_gb': total_size / (1024**3),
                    'file_count': file_count
                }
            else:
                stats['storage'] = {
                    'total_size_bytes': 0,
                    'total_size_gb': 0,
                    'file_count': 0
                }
        except Exception:
            stats['storage'] = {'error': 'Unable to calculate storage stats'}
        
        report = {
            'timestamp': datetime.utcnow().isoformat(),
            'system_info': {
                'version': settings.app_version,
                'environment': settings.environment
            },
            'statistics': stats
        }
        
        app_logger.info(
            "System report generated",
            total_users=stats['users']['total'],
            total_videos=stats['videos']['total'],
            storage_gb=stats['storage'].get('total_size_gb', 0)
        )
        
        return {
            'status': 'completed',
            'report': report,
            'message': 'System report generated successfully'
        }
        
    except Exception as e:
        app_logger.error(
            "Failed to generate system report",
            error=str(e),
            exc_info=True
        )
        
        return {
            'status': 'failed',
            'error': str(e),
            'message': 'Failed to generate system report'
        }
        
    finally:
        db.close()