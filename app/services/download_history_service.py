"""下载历史管理服务

提供下载历史记录的管理功能，包括记录创建、查询、统计等。
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from uuid import uuid4
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc

from app.core.app_logging import download_logger
from app.models.download_history import (
    DownloadHistory,
    DownloadStatistics,
    PlatformStatistics,
    DownloadTag,
    DownloadHistoryTag
)
from app.models.video import DownloadTask
from app.models.user import User


class DownloadHistoryService:
    """下载历史管理服务类
    
    负责管理下载历史记录、统计信息和标签系统。
    """
    
    def __init__(self):
        pass
    
    async def create_history_record(
        self,
        db: Session,
        task: DownloadTask,
        video_info: Dict[str, Any],
        download_options: Dict[str, Any]
    ) -> DownloadHistory:
        """创建下载历史记录
        
        Args:
            db: 数据库会话
            task: 下载任务
            video_info: 视频信息
            download_options: 下载选项
            
        Returns:
            创建的历史记录
        """
        try:
            history = DownloadHistory(
                id=str(uuid4()),
                user_id=task.user_id,
                task_id=task.id,
                original_url=task.url,
                video_title=video_info.get('title'),
                video_id=video_info.get('video_id'),
                platform=video_info.get('platform', 'unknown'),
                video_duration=video_info.get('duration'),
                author_name=video_info.get('author', {}).get('name'),
                author_id=video_info.get('author', {}).get('unique_id'),
                download_format=download_options.get('format'),
                download_quality=download_options.get('quality'),
                download_options=json.dumps(download_options),
                status='started',
                started_at=datetime.utcnow(),
                thumbnail_url=video_info.get('thumbnail'),
                video_description=video_info.get('description'),
                tags=json.dumps(video_info.get('keywords', [])),
                view_count=video_info.get('statistics', {}).get('play_count'),
                like_count=video_info.get('statistics', {}).get('digg_count'),
                comment_count=video_info.get('statistics', {}).get('comment_count')
            )
            
            db.add(history)
            db.commit()
            db.refresh(history)
            
            download_logger.info(
                "下载历史记录已创建",
                history_id=history.id,
                task_id=task.id,
                platform=history.platform
            )
            
            return history
            
        except Exception as e:
            download_logger.error(
                "创建下载历史记录失败",
                task_id=task.id,
                error=str(e)
            )
            db.rollback()
            raise
    
    async def update_history_record(
        self,
        db: Session,
        history_id: str,
        status: str,
        file_path: Optional[str] = None,
        file_size: Optional[int] = None,
        download_speed: Optional[float] = None,
        error_message: Optional[str] = None
    ) -> Optional[DownloadHistory]:
        """更新下载历史记录
        
        Args:
            db: 数据库会话
            history_id: 历史记录ID
            status: 新状态
            file_path: 文件路径
            file_size: 文件大小
            download_speed: 下载速度
            error_message: 错误信息
            
        Returns:
            更新后的历史记录
        """
        try:
            history = db.query(DownloadHistory).filter(
                DownloadHistory.id == history_id
            ).first()
            
            if not history:
                download_logger.warning(
                    "下载历史记录不存在",
                    history_id=history_id
                )
                return None
            
            # 更新状态
            history.status = status
            
            # 更新完成时间和下载时长
            if status in ['completed', 'failed', 'cancelled']:
                history.completed_at = datetime.utcnow()
                if history.started_at:
                    duration = (history.completed_at - history.started_at).total_seconds()
                    history.download_duration = int(duration)
            
            # 更新其他字段
            if file_path:
                history.file_path = file_path
            if file_size:
                history.file_size = file_size
            if download_speed:
                history.download_speed = download_speed
            if error_message:
                history.error_message = error_message
            
            history.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(history)
            
            # 更新统计信息
            await self._update_statistics(db, history)
            
            download_logger.info(
                "下载历史记录已更新",
                history_id=history_id,
                status=status
            )
            
            return history
            
        except Exception as e:
            download_logger.error(
                "更新下载历史记录失败",
                history_id=history_id,
                error=str(e)
            )
            db.rollback()
            raise
    
    async def get_user_history(
        self,
        db: Session,
        user_id: str,
        platform: Optional[str] = None,
        status: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[DownloadHistory]:
        """获取用户下载历史
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            platform: 平台过滤
            status: 状态过滤
            start_date: 开始日期
            end_date: 结束日期
            limit: 数量限制
            offset: 偏移量
            
        Returns:
            历史记录列表
        """
        query = db.query(DownloadHistory).filter(
            DownloadHistory.user_id == user_id,
            DownloadHistory.is_deleted == False
        )
        
        if platform:
            query = query.filter(DownloadHistory.platform == platform)
        
        if status:
            query = query.filter(DownloadHistory.status == status)
        
        if start_date:
            query = query.filter(DownloadHistory.created_at >= start_date)
        
        if end_date:
            query = query.filter(DownloadHistory.created_at <= end_date)
        
        return query.order_by(desc(DownloadHistory.created_at)).offset(offset).limit(limit).all()
    
    async def get_user_statistics(
        self,
        db: Session,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """获取用户下载统计
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            days: 统计天数
            
        Returns:
            统计信息
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # 基础统计
        total_query = db.query(DownloadHistory).filter(
            DownloadHistory.user_id == user_id,
            DownloadHistory.created_at >= start_date,
            DownloadHistory.is_deleted == False
        )
        
        total_downloads = total_query.count()
        successful_downloads = total_query.filter(DownloadHistory.status == 'completed').count()
        failed_downloads = total_query.filter(DownloadHistory.status == 'failed').count()
        
        # 文件大小统计
        size_result = db.query(
            func.sum(DownloadHistory.file_size).label('total_size'),
            func.avg(DownloadHistory.file_size).label('avg_size')
        ).filter(
            DownloadHistory.user_id == user_id,
            DownloadHistory.status == 'completed',
            DownloadHistory.created_at >= start_date,
            DownloadHistory.is_deleted == False
        ).first()
        
        # 平台统计
        platform_stats = db.query(
            DownloadHistory.platform,
            func.count(DownloadHistory.id).label('count')
        ).filter(
            DownloadHistory.user_id == user_id,
            DownloadHistory.created_at >= start_date,
            DownloadHistory.is_deleted == False
        ).group_by(DownloadHistory.platform).all()
        
        # 每日统计
        daily_stats = db.query(
            func.date(DownloadHistory.created_at).label('date'),
            func.count(DownloadHistory.id).label('count')
        ).filter(
            DownloadHistory.user_id == user_id,
            DownloadHistory.created_at >= start_date,
            DownloadHistory.is_deleted == False
        ).group_by(func.date(DownloadHistory.created_at)).all()
        
        return {
            'period_days': days,
            'total_downloads': total_downloads,
            'successful_downloads': successful_downloads,
            'failed_downloads': failed_downloads,
            'success_rate': (successful_downloads / total_downloads * 100) if total_downloads > 0 else 0,
            'total_file_size': size_result.total_size or 0,
            'average_file_size': size_result.avg_size or 0,
            'platform_distribution': [
                {'platform': stat.platform, 'count': stat.count}
                for stat in platform_stats
            ],
            'daily_downloads': [
                {'date': stat.date.isoformat(), 'count': stat.count}
                for stat in daily_stats
            ]
        }
    
    async def delete_history_record(
        self,
        db: Session,
        history_id: str,
        user_id: str,
        hard_delete: bool = False
    ) -> bool:
        """删除下载历史记录
        
        Args:
            db: 数据库会话
            history_id: 历史记录ID
            user_id: 用户ID
            hard_delete: 是否硬删除
            
        Returns:
            是否成功删除
        """
        try:
            history = db.query(DownloadHistory).filter(
                DownloadHistory.id == history_id,
                DownloadHistory.user_id == user_id
            ).first()
            
            if not history:
                return False
            
            if hard_delete:
                # 硬删除：从数据库中完全删除
                db.delete(history)
            else:
                # 软删除：标记为已删除
                history.is_deleted = True
                history.updated_at = datetime.utcnow()
            
            db.commit()
            
            download_logger.info(
                "下载历史记录已删除",
                history_id=history_id,
                user_id=user_id,
                hard_delete=hard_delete
            )
            
            return True
            
        except Exception as e:
            download_logger.error(
                "删除下载历史记录失败",
                history_id=history_id,
                error=str(e)
            )
            db.rollback()
            return False
    
    async def _update_statistics(
        self,
        db: Session,
        history: DownloadHistory
    ):
        """更新统计信息
        
        Args:
            db: 数据库会话
            history: 历史记录
        """
        try:
            # 更新用户统计
            await self._update_user_statistics(db, history)
            
            # 更新平台统计
            await self._update_platform_statistics(db, history)
            
        except Exception as e:
            download_logger.error(
                "更新统计信息失败",
                history_id=history.id,
                error=str(e)
            )
    
    async def _update_user_statistics(
        self,
        db: Session,
        history: DownloadHistory
    ):
        """更新用户统计信息
        
        Args:
            db: 数据库会话
            history: 历史记录
        """
        # 按日期统计
        date = history.created_at.date()
        
        # 查找或创建统计记录
        stats = db.query(DownloadStatistics).filter(
            DownloadStatistics.user_id == history.user_id,
            func.date(DownloadStatistics.date) == date,
            DownloadStatistics.platform == history.platform
        ).first()
        
        if not stats:
            stats = DownloadStatistics(
                id=str(uuid4()),
                user_id=history.user_id,
                date=datetime.combine(date, datetime.min.time()),
                platform=history.platform
            )
            db.add(stats)
        
        # 更新统计数据
        stats.total_downloads += 1
        
        if history.status == 'completed':
            stats.successful_downloads += 1
            if history.file_size:
                stats.total_file_size += history.file_size
            if history.download_duration:
                stats.total_download_time += history.download_duration
            if history.download_speed:
                # 更新平均下载速度
                if stats.avg_download_speed == 0:
                    stats.avg_download_speed = history.download_speed
                else:
                    stats.avg_download_speed = (
                        stats.avg_download_speed + history.download_speed
                    ) / 2
                
                # 更新最大下载速度
                if history.download_speed > stats.max_download_speed:
                    stats.max_download_speed = history.download_speed
        
        elif history.status == 'failed':
            stats.failed_downloads += 1
        elif history.status == 'cancelled':
            stats.cancelled_downloads += 1
        
        if history.video_duration:
            stats.total_duration += history.video_duration
        
        stats.updated_at = datetime.utcnow()
        db.commit()
    
    async def _update_platform_statistics(
        self,
        db: Session,
        history: DownloadHistory
    ):
        """更新平台统计信息
        
        Args:
            db: 数据库会话
            history: 历史记录
        """
        # 查找或创建平台统计记录
        stats = db.query(PlatformStatistics).filter(
            PlatformStatistics.platform == history.platform
        ).first()
        
        if not stats:
            stats = PlatformStatistics(
                id=str(uuid4()),
                platform=history.platform
            )
            db.add(stats)
        
        # 更新统计数据
        stats.total_downloads += 1
        
        if history.status == 'completed':
            stats.successful_downloads += 1
            
            if history.file_size:
                # 更新平均文件大小
                if stats.avg_file_size == 0:
                    stats.avg_file_size = history.file_size
                else:
                    stats.avg_file_size = (
                        (stats.avg_file_size * (stats.successful_downloads - 1) + history.file_size)
                        / stats.successful_downloads
                    )
                
                stats.total_file_size += history.file_size
            
            if history.download_speed:
                # 更新平均下载速度
                if stats.avg_download_speed == 0:
                    stats.avg_download_speed = history.download_speed
                else:
                    stats.avg_download_speed = (
                        (stats.avg_download_speed * (stats.successful_downloads - 1) + history.download_speed)
                        / stats.successful_downloads
                    )
        
        # 更新成功率
        stats.avg_success_rate = (
            stats.successful_downloads / stats.total_downloads * 100
        ) if stats.total_downloads > 0 else 0
        
        # 更新最后下载时间
        stats.last_download_at = history.created_at
        stats.updated_at = datetime.utcnow()
        
        db.commit()


# 创建全局服务实例
download_history_service = DownloadHistoryService()