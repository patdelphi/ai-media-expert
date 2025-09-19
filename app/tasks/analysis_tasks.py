"""视频分析异步任务

使用Celery实现视频分析的异步处理。
"""

from datetime import datetime
from typing import Dict

from celery import current_task
from sqlalchemy.orm import sessionmaker

from app.core.database import engine
from app.core.app_logging import analysis_logger
from app.models.video import AnalysisTask, Video
from app.services.analysis_service import AnalysisService
from app.tasks.celery_app import celery_app

# 创建数据库会话
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@celery_app.task(bind=True, name="analyze_video")
def analyze_video_task(self, task_id: int) -> Dict:
    """分析视频任务
    
    Args:
        task_id: 分析任务ID
    
    Returns:
        任务执行结果
    """
    db = SessionLocal()
    analysis_service = AnalysisService()
    
    try:
        # 获取分析任务
        task = db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()
        if not task:
            raise Exception(f"Analysis task {task_id} not found")
        
        # 获取关联的视频
        video = db.query(Video).filter(Video.id == task.video_id).first()
        if not video:
            raise Exception(f"Video {task.video_id} not found")
        
        # 更新任务状态为处理中
        task.status = "processing"
        task.started_at = datetime.utcnow()
        task.progress = 0
        db.commit()
        
        analysis_logger.info(
            "Starting video analysis",
            task_id=task_id,
            video_id=task.video_id,
            analysis_type=task.analysis_type,
            user_id=task.user_id
        )
        
        # 进度回调函数
        def progress_callback(progress: int):
            # 更新任务进度
            if progress != task.progress:
                task.progress = min(max(progress, 0), 100)
                db.commit()
                
                # 更新Celery任务状态
                current_task.update_state(
                    state='PROGRESS',
                    meta={
                        'current': progress,
                        'total': 100,
                        'status': f'Analyzing... {progress}%'
                    }
                )
        
        # 执行分析
        analysis_result = analysis_service.analyze_video(
            task_id=task_id,
            video_path=video.file_path,
            analysis_type=task.analysis_type or "full",
            config=task.config,
            progress_callback=progress_callback
        )
        
        # 更新任务状态为完成
        task.status = "completed"
        task.progress = 100
        task.completed_at = datetime.utcnow()
        task.result_data = analysis_result['analysis_result']
        task.result_summary = analysis_result['summary']
        task.confidence_score = analysis_result['confidence_score']
        task.error_message = None
        
        # 更新视频的分析状态
        video.is_analyzed = True
        
        db.commit()
        
        analysis_logger.info(
            "Video analysis completed",
            task_id=task_id,
            video_id=task.video_id,
            confidence_score=analysis_result['confidence_score']
        )
        
        return {
            'status': 'completed',
            'task_id': task_id,
            'video_id': task.video_id,
            'analysis_type': task.analysis_type,
            'confidence_score': analysis_result['confidence_score'],
            'message': 'Video analysis completed successfully'
        }
        
    except Exception as e:
        error_msg = str(e)
        analysis_logger.error(
            "Video analysis failed",
            task_id=task_id,
            error=error_msg,
            exc_info=True
        )
        
        # 更新任务状态为失败
        if 'task' in locals():
            task.status = "failed"
            task.error_message = error_msg
            task.error_code = "ANALYSIS_ERROR"
            db.commit()
        
        return {
            'status': 'failed',
            'task_id': task_id,
            'error': error_msg,
            'message': 'Video analysis failed'
        }
        
    finally:
        db.close()


@celery_app.task(name="batch_analyze_videos")
def batch_analyze_videos_task(task_ids: list) -> Dict:
    """批量分析视频任务
    
    Args:
        task_ids: 分析任务ID列表
    
    Returns:
        批量任务执行结果
    """
    results = []
    
    for task_id in task_ids:
        try:
            result = analyze_video_task.delay(task_id)
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
    
    analysis_logger.info(
        "Batch analysis tasks queued",
        task_count=len(task_ids),
        results=results
    )
    
    return {
        'status': 'queued',
        'total_tasks': len(task_ids),
        'results': results
    }


@celery_app.task(name="generate_analysis_report")
def generate_analysis_report_task(task_id: int, format: str = "json") -> Dict:
    """生成分析报告任务
    
    Args:
        task_id: 分析任务ID
        format: 报告格式 (json, pdf, markdown)
    
    Returns:
        报告生成结果
    """
    db = SessionLocal()
    
    try:
        # 获取分析任务
        task = db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()
        if not task:
            raise Exception(f"Analysis task {task_id} not found")
        
        if task.status != "completed":
            raise Exception(f"Analysis task {task_id} is not completed")
        
        # 获取关联的视频
        video = db.query(Video).filter(Video.id == task.video_id).first()
        if not video:
            raise Exception(f"Video {task.video_id} not found")
        
        analysis_logger.info(
            "Generating analysis report",
            task_id=task_id,
            format=format
        )
        
        # 生成报告
        report_data = {
            'task_info': {
                'id': task.id,
                'video_id': task.video_id,
                'analysis_type': task.analysis_type,
                'created_at': task.created_at.isoformat(),
                'completed_at': task.completed_at.isoformat(),
                'confidence_score': task.confidence_score
            },
            'video_info': {
                'title': video.title,
                'duration': video.duration,
                'resolution': video.resolution,
                'platform': video.platform,
                'author': video.author
            },
            'analysis_result': task.result_data,
            'summary': task.result_summary
        }
        
        # 根据格式生成不同的报告
        if format == "json":
            report_content = report_data
        elif format == "markdown":
            report_content = _generate_markdown_report(report_data)
        elif format == "pdf":
            # TODO: 实现PDF报告生成
            report_content = "PDF report generation not implemented yet"
        else:
            raise Exception(f"Unsupported report format: {format}")
        
        analysis_logger.info(
            "Analysis report generated",
            task_id=task_id,
            format=format
        )
        
        return {
            'status': 'completed',
            'task_id': task_id,
            'format': format,
            'report': report_content,
            'message': 'Analysis report generated successfully'
        }
        
    except Exception as e:
        error_msg = str(e)
        analysis_logger.error(
            "Failed to generate analysis report",
            task_id=task_id,
            format=format,
            error=error_msg,
            exc_info=True
        )
        
        return {
            'status': 'failed',
            'task_id': task_id,
            'error': error_msg,
            'message': 'Failed to generate analysis report'
        }
        
    finally:
        db.close()


def _generate_markdown_report(report_data: Dict) -> str:
    """生成Markdown格式的分析报告
    
    Args:
        report_data: 报告数据
    
    Returns:
        Markdown格式的报告内容
    """
    task_info = report_data['task_info']
    video_info = report_data['video_info']
    
    markdown = f"""
# 视频分析报告

## 基本信息

- **任务ID**: {task_info['id']}
- **视频标题**: {video_info['title']}
- **分析类型**: {task_info['analysis_type']}
- **置信度分数**: {task_info['confidence_score']:.2f}
- **分析时间**: {task_info['completed_at']}

## 视频信息

- **时长**: {video_info['duration']}秒
- **分辨率**: {video_info['resolution']}
- **平台**: {video_info['platform']}
- **作者**: {video_info['author']}

## 分析摘要

{report_data['summary']}

## 详细结果

```json
{report_data['analysis_result']}
```

---
*报告生成时间: {datetime.utcnow().isoformat()}*
"""
    
    return markdown


@celery_app.task(name="cleanup_analysis_cache")
def cleanup_analysis_cache_task() -> Dict:
    """清理分析缓存任务
    
    清理过期的分析缓存文件。
    
    Returns:
        清理结果
    """
    try:
        # TODO: 实现缓存清理逻辑
        cleaned_count = 0
        
        analysis_logger.info(
            "Analysis cache cleanup completed",
            cleaned_files=cleaned_count
        )
        
        return {
            'status': 'completed',
            'cleaned_files': cleaned_count,
            'message': f'Cleaned up {cleaned_count} cache files'
        }
        
    except Exception as e:
        analysis_logger.error(
            "Failed to cleanup analysis cache",
            error=str(e),
            exc_info=True
        )
        
        return {
            'status': 'failed',
            'error': str(e),
            'message': 'Failed to cleanup analysis cache'
        }