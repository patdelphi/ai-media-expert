"""下载历史数据模型

记录用户的下载历史、文件路径、下载统计等信息。
"""

from sqlalchemy import Column, String, Integer, Float, DateTime, Text, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class DownloadHistory(Base):
    """下载历史记录表
    
    记录每次下载的详细信息，包括成功和失败的记录。
    """
    __tablename__ = "download_history"
    
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    task_id = Column(String, ForeignKey("download_tasks.id"), nullable=True, index=True)
    
    # 视频信息
    original_url = Column(Text, nullable=False)
    video_title = Column(String(500), nullable=True)
    video_id = Column(String(100), nullable=True)
    platform = Column(String(50), nullable=False, index=True)
    video_duration = Column(Integer, nullable=True)  # 视频时长（秒）
    
    # 作者信息
    author_name = Column(String(200), nullable=True)
    author_id = Column(String(100), nullable=True)
    
    # 下载配置
    download_format = Column(String(20), nullable=True)  # mp4, webm等
    download_quality = Column(String(20), nullable=True)  # 1080p, 720p等
    download_options = Column(Text, nullable=True)  # JSON格式的下载选项
    
    # 下载结果
    status = Column(String(20), nullable=False, index=True)  # completed, failed, cancelled
    file_path = Column(Text, nullable=True)  # 下载文件的本地路径
    file_size = Column(Integer, nullable=True)  # 文件大小（字节）
    download_speed = Column(Float, nullable=True)  # 平均下载速度（KB/s）
    
    # 时间信息
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    download_duration = Column(Integer, nullable=True)  # 下载耗时（秒）
    
    # 错误信息
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    
    # 元数据
    thumbnail_url = Column(Text, nullable=True)
    video_description = Column(Text, nullable=True)
    tags = Column(Text, nullable=True)  # JSON格式的标签列表
    
    # 统计信息
    view_count = Column(Integer, nullable=True)
    like_count = Column(Integer, nullable=True)
    comment_count = Column(Integer, nullable=True)
    
    # 系统字段
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    
    # 关联关系
    user = relationship("User", back_populates="download_history")
    task = relationship("DownloadTask", back_populates="history_record")
    
    # 索引
    __table_args__ = (
        Index('idx_download_history_user_platform', 'user_id', 'platform'),
        Index('idx_download_history_status_created', 'status', 'created_at'),
        Index('idx_download_history_platform_created', 'platform', 'created_at'),
    )
    
    def __repr__(self):
        return f"<DownloadHistory(id={self.id}, user_id={self.user_id}, platform={self.platform}, status={self.status})>"


class DownloadStatistics(Base):
    """下载统计表
    
    记录用户的下载统计信息，按日期和平台聚合。
    """
    __tablename__ = "download_statistics"
    
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    
    # 统计维度
    date = Column(DateTime, nullable=False, index=True)  # 统计日期（按天）
    platform = Column(String(50), nullable=True, index=True)  # 平台（为空表示全平台）
    
    # 下载统计
    total_downloads = Column(Integer, default=0, nullable=False)  # 总下载数
    successful_downloads = Column(Integer, default=0, nullable=False)  # 成功下载数
    failed_downloads = Column(Integer, default=0, nullable=False)  # 失败下载数
    cancelled_downloads = Column(Integer, default=0, nullable=False)  # 取消下载数
    
    # 数据统计
    total_file_size = Column(Integer, default=0, nullable=False)  # 总文件大小（字节）
    total_duration = Column(Integer, default=0, nullable=False)  # 总视频时长（秒）
    total_download_time = Column(Integer, default=0, nullable=False)  # 总下载时间（秒）
    
    # 速度统计
    avg_download_speed = Column(Float, default=0.0, nullable=False)  # 平均下载速度（KB/s）
    max_download_speed = Column(Float, default=0.0, nullable=False)  # 最大下载速度（KB/s）
    
    # 系统字段
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # 关联关系
    user = relationship("User")
    
    # 索引
    __table_args__ = (
        Index('idx_download_stats_user_date', 'user_id', 'date'),
        Index('idx_download_stats_user_platform_date', 'user_id', 'platform', 'date'),
    )
    
    def __repr__(self):
        return f"<DownloadStatistics(id={self.id}, user_id={self.user_id}, date={self.date}, platform={self.platform})>"


class PlatformStatistics(Base):
    """平台统计表
    
    记录各平台的整体使用统计。
    """
    __tablename__ = "platform_statistics"
    
    id = Column(String, primary_key=True, index=True)
    platform = Column(String(50), nullable=False, unique=True, index=True)
    
    # 使用统计
    total_users = Column(Integer, default=0, nullable=False)  # 使用该平台的用户数
    total_downloads = Column(Integer, default=0, nullable=False)  # 总下载次数
    successful_downloads = Column(Integer, default=0, nullable=False)  # 成功下载次数
    
    # 数据统计
    total_file_size = Column(Integer, default=0, nullable=False)  # 总文件大小
    avg_file_size = Column(Float, default=0.0, nullable=False)  # 平均文件大小
    
    # 性能统计
    avg_download_speed = Column(Float, default=0.0, nullable=False)  # 平均下载速度
    avg_success_rate = Column(Float, default=0.0, nullable=False)  # 平均成功率
    
    # 时间统计
    last_download_at = Column(DateTime, nullable=True)  # 最后一次下载时间
    
    # 系统字段
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<PlatformStatistics(platform={self.platform}, total_downloads={self.total_downloads})>"


class DownloadTag(Base):
    """下载标签表
    
    用于给下载记录添加自定义标签，方便分类和搜索。
    """
    __tablename__ = "download_tags"
    
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    color = Column(String(20), nullable=True)  # 标签颜色
    description = Column(Text, nullable=True)
    
    # 使用统计
    usage_count = Column(Integer, default=0, nullable=False)
    
    # 系统字段
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # 关联关系
    user = relationship("User")
    
    # 索引
    __table_args__ = (
        Index('idx_download_tags_user_name', 'user_id', 'name'),
    )
    
    def __repr__(self):
        return f"<DownloadTag(id={self.id}, name={self.name}, user_id={self.user_id})>"


class DownloadHistoryTag(Base):
    """下载历史标签关联表
    
    多对多关系：一个下载记录可以有多个标签，一个标签可以关联多个下载记录。
    """
    __tablename__ = "download_history_tags"
    
    id = Column(String, primary_key=True, index=True)
    history_id = Column(String, ForeignKey("download_history.id"), nullable=False, index=True)
    tag_id = Column(String, ForeignKey("download_tags.id"), nullable=False, index=True)
    
    # 系统字段
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # 关联关系
    history = relationship("DownloadHistory")
    tag = relationship("DownloadTag")
    
    # 索引
    __table_args__ = (
        Index('idx_history_tags_history_tag', 'history_id', 'tag_id'),
    )
    
    def __repr__(self):
        return f"<DownloadHistoryTag(history_id={self.history_id}, tag_id={self.tag_id})>"