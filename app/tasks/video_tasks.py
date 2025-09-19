"""视频处理相关的Celery任务

处理视频上传后的异步任务，包括视频分析、缩略图生成等。
"""

import os
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

from celery import current_task
from sqlalchemy.orm import Session

from app.tasks.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.video import Video
from app.services.video_processing import video_processing_service
from app.services.video_metadata import video_metadata_extractor
from app.core.config import settings
from app.core.app_logging import app_logger as api_logger


@celery_app.task(bind=True)
def process_uploaded_video(self, video_id: int) -> Dict[str, Any]:
    """处理上传完成的视频
    
    Args:
        video_id: 视频ID
        
    Returns:
        处理结果
    """
    db = SessionLocal()
    try:
        # 获取视频记录
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            raise Exception(f"Video with id {video_id} not found")
        
        api_logger.info(
            "Starting video processing",
            video_id=video_id,
            file_path=video.file_path
        )
        
        # 更新任务状态
        current_task.update_state(
            state='PROGRESS',
            meta={'current': 10, 'total': 100, 'status': 'Analyzing video...'}
        )
        
        # 1. 验证视频文件
        is_valid, error_msg = video_processing_service.validate_video_file(video.file_path)
        if not is_valid:
            video.upload_status = "failed"
            video.upload_error = f"Video validation failed: {error_msg}"
            db.commit()
            raise Exception(f"Video validation failed: {error_msg}")
        
        # 2. 分析视频信息
        current_task.update_state(
            state='PROGRESS',
            meta={'current': 30, 'total': 100, 'status': 'Extracting video metadata...'}
        )
        
        video_info = video_processing_service.analyze_video(video.file_path)
        
        # 更新视频信息
        video.duration = video_info.get('duration')
        video.resolution = video_info.get('resolution')
        video.format = video_info.get('format')
        video.fps = video_info.get('fps')
        video.bitrate = video_info.get('bitrate')
        video.codec = video_info.get('video_codec')  # 保持向后兼容
        video.video_codec = video_info.get('video_codec')
        video.audio_codec = video_info.get('audio_codec')
        video.video_bitrate = video_info.get('video_bitrate')
        video.audio_bitrate = video_info.get('audio_bitrate')
        
        # 如果文件大小未设置，从分析结果中获取
        if not video.file_size and video_info.get('file_size'):
            video.file_size = video_info.get('file_size')
        
        db.commit()
        
        # 3. 生成缩略图
        current_task.update_state(
            state='PROGRESS',
            meta={'current': 60, 'total': 100, 'status': 'Generating thumbnail...'}
        )
        
        thumbnail_dir = Path(settings.upload_dir) / "thumbnails"
        thumbnail_dir.mkdir(parents=True, exist_ok=True)
        
        thumbnail_filename = f"thumb_{video.id}.jpg"
        thumbnail_path = thumbnail_dir / thumbnail_filename
        
        if video_processing_service.generate_thumbnail(video.file_path, str(thumbnail_path)):
            video.thumbnail_path = str(thumbnail_path)
            db.commit()
        
        # 4. 生成预览图片
        current_task.update_state(
            state='PROGRESS',
            meta={'current': 80, 'total': 100, 'status': 'Generating preview images...'}
        )
        
        preview_dir = Path(settings.upload_dir) / "previews" / str(video.id)
        preview_images = video_processing_service.generate_preview_images(
            video.file_path, str(preview_dir), count=6
        )
        
        if preview_images:
            video.preview_images = preview_images
            db.commit()
        
        # 5. 提取详细元数据
        current_task.update_state(
            state='PROGRESS',
            meta={'current': 85, 'total': 100, 'status': 'Extracting comprehensive metadata...'}
        )
        
        try:
            # 提取全面的元数据
            comprehensive_metadata = video_metadata_extractor.extract_comprehensive_metadata(video.file_path)
            
            # 智能生成标题和标签
            smart_info = video_metadata_extractor.extract_smart_title_and_tags(video.file_path, comprehensive_metadata)
            
            # 如果视频没有标题，使用智能生成的标题
            if not video.title or video.title == Path(video.file_path).stem:
                video.title = smart_info['suggested_title']
            
            # 存储元数据
            if not video.extra_metadata:
                video.extra_metadata = {}
            
            video.extra_metadata.update({
                'comprehensive_metadata': comprehensive_metadata,
                'smart_suggestions': smart_info,
                'metadata_extraction_time': datetime.utcnow().isoformat()
            })
            
            db.commit()
            
        except Exception as e:
            api_logger.warning(
                "Failed to extract comprehensive metadata",
                video_id=video_id,
                error=str(e)
            )
        
        # 6. 计算文件哈希（用于重复检测）
        current_task.update_state(
            state='PROGRESS',
            meta={'current': 95, 'total': 100, 'status': 'Calculating file hash...'}
        )
        
        try:
            file_hash = video_processing_service.calculate_file_hash(video.file_path)
            # 将哈希值存储在额外元数据中
            if not video.extra_metadata:
                video.extra_metadata = {}
            video.extra_metadata['file_hash'] = file_hash
            db.commit()
        except Exception as e:
            api_logger.warning(
                "Failed to calculate file hash",
                video_id=video_id,
                error=str(e)
            )
        
        # 6. 完成处理
        current_task.update_state(
            state='PROGRESS',
            meta={'current': 100, 'total': 100, 'status': 'Processing completed'}
        )
        
        video.status = "active"
        video.is_analyzed = True
        db.commit()
        
        api_logger.info(
            "Video processing completed",
            video_id=video_id,
            duration=video.duration,
            resolution=video.resolution,
            format=video.format
        )
        
        return {
            'video_id': video_id,
            'status': 'completed',
            'duration': video.duration,
            'resolution': video.resolution,
            'format': video.format,
            'thumbnail_path': video.thumbnail_path,
            'preview_images_count': len(preview_images) if preview_images else 0
        }
        
    except Exception as e:
        api_logger.error(
            "Video processing failed",
            video_id=video_id,
            error=str(e)
        )
        
        # 更新视频状态为处理失败
        try:
            video = db.query(Video).filter(Video.id == video_id).first()
            if video:
                video.status = "failed"
                video.upload_error = str(e)
                db.commit()
        except Exception as db_error:
            api_logger.error(
                "Failed to update video status",
                video_id=video_id,
                error=str(db_error)
            )
        
        # 重新抛出异常，让Celery知道任务失败
        raise
        
    finally:
        db.close()


@celery_app.task
def cleanup_failed_uploads() -> Dict[str, Any]:
    """清理失败的上传文件
    
    定期清理超时或失败的上传文件和临时数据。
    """
    db = SessionLocal()
    try:
        from datetime import datetime, timedelta
        
        # 查找超过24小时仍未完成的上传
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        
        failed_videos = db.query(Video).filter(
            Video.upload_status.in_(['pending', 'uploading', 'paused']),
            Video.created_at < cutoff_time
        ).all()
        
        cleaned_count = 0
        for video in failed_videos:
            try:
                # 删除临时文件
                temp_dir = Path(settings.upload_dir) / "videos" / "temp" / video.upload_session_id
                if temp_dir.exists():
                    import shutil
                    shutil.rmtree(temp_dir)
                
                # 删除不完整的视频文件
                if video.file_path and os.path.exists(video.file_path):
                    os.remove(video.file_path)
                
                # 更新状态
                video.upload_status = "failed"
                video.upload_error = "Upload timeout - cleaned up by system"
                video.status = "failed"
                
                cleaned_count += 1
                
            except Exception as e:
                api_logger.error(
                    "Failed to cleanup video",
                    video_id=video.id,
                    error=str(e)
                )
        
        db.commit()
        
        api_logger.info(
            "Upload cleanup completed",
            cleaned_count=cleaned_count
        )
        
        return {
            'status': 'completed',
            'cleaned_count': cleaned_count
        }
        
    except Exception as e:
        api_logger.error(
            "Upload cleanup failed",
            error=str(e)
        )
        raise
        
    finally:
        db.close()


@celery_app.task
def generate_video_thumbnails(video_id: int, timestamps: list = None) -> Dict[str, Any]:
    """为视频生成多个时间点的缩略图
    
    Args:
        video_id: 视频ID
        timestamps: 时间戳列表（秒），如果为None则自动选择
        
    Returns:
        生成结果
    """
    db = SessionLocal()
    try:
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            raise Exception(f"Video with id {video_id} not found")
        
        if not os.path.exists(video.file_path):
            raise Exception(f"Video file not found: {video.file_path}")
        
        # 如果没有指定时间戳，自动生成
        if not timestamps:
            duration = video.duration or 0
            if duration > 0:
                # 生成6个均匀分布的时间点
                timestamps = [int(duration * i / 7) for i in range(1, 7)]
            else:
                timestamps = [1]  # 默认第1秒
        
        thumbnail_dir = Path(settings.upload_dir) / "thumbnails" / str(video_id)
        thumbnail_dir.mkdir(parents=True, exist_ok=True)
        
        generated_thumbnails = []
        for i, timestamp in enumerate(timestamps):
            timestamp_str = f"{timestamp // 3600:02d}:{(timestamp % 3600) // 60:02d}:{timestamp % 60:02d}"
            thumbnail_path = thumbnail_dir / f"thumb_{timestamp}s.jpg"
            
            if video_processing_service.generate_thumbnail(
                video.file_path, str(thumbnail_path), timestamp_str
            ):
                generated_thumbnails.append(str(thumbnail_path))
        
        # 更新视频记录
        if generated_thumbnails:
            if not video.extra_metadata:
                video.extra_metadata = {}
            video.extra_metadata['additional_thumbnails'] = generated_thumbnails
            db.commit()
        
        api_logger.info(
            "Additional thumbnails generated",
            video_id=video_id,
            count=len(generated_thumbnails)
        )
        
        return {
            'video_id': video_id,
            'status': 'completed',
            'thumbnails': generated_thumbnails,
            'count': len(generated_thumbnails)
        }
        
    except Exception as e:
        api_logger.error(
            "Thumbnail generation failed",
            video_id=video_id,
            error=str(e)
        )
        raise
        
    finally:
        db.close()