"""视频相关数据模型

定义视频、下载任务、分析任务等核心业务模型。
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger, Boolean, Column, Date, DateTime, Float, ForeignKey, Index, Integer, 
    String, Text, JSON
)
from sqlalchemy.orm import relationship

from app.core.database import BaseModel


class Video(BaseModel):
    """视频模型"""
    __tablename__ = "videos"
    
    # 基础信息
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    original_filename = Column(String(500), nullable=True)  # 原始文件名
    file_path = Column(Text, nullable=False)
    file_size = Column(BigInteger, nullable=True)  # 字节
    
    # 技术参数
    duration = Column(Integer, nullable=True)  # 秒
    resolution = Column(String(20), nullable=True)  # 如: 1920x1080
    format = Column(String(10), nullable=True)  # 如: mp4, avi
    fps = Column(Float, nullable=True)  # 帧率
    bitrate = Column(Integer, nullable=True)  # 比特率
    codec = Column(String(20), nullable=True)  # 编码格式
    
    # 平台信息
    platform = Column(String(50), nullable=True)  # 如: tiktok, youtube
    original_url = Column(Text, nullable=True)
    video_id = Column(String(255), nullable=True)  # 平台视频ID
    
    # 作者信息
    author = Column(String(255), nullable=True)
    author_id = Column(String(255), nullable=True)
    channel_name = Column(String(255), nullable=True)
    
    # 统计数据
    upload_date = Column(Date, nullable=True)
    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    share_count = Column(Integer, default=0)
    
    # 状态信息
    status = Column(String(20), default="active", nullable=False)  # active, deleted, processing, uploaded, analyzed
    is_analyzed = Column(Boolean, default=False, nullable=False)
    
    # 上传相关字段
    upload_status = Column(String(20), default="pending", nullable=False)  # pending, uploading, completed, failed, cancelled
    upload_progress = Column(Float, default=0.0, nullable=False)  # 上传进度 0-100
    upload_speed = Column(Float, nullable=True)  # 上传速度 bytes/s
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=True)  # 上传用户ID
    upload_error = Column(Text, nullable=True)  # 上传错误信息
    chunk_size = Column(Integer, nullable=True)  # 分片大小
    total_chunks = Column(Integer, nullable=True)  # 总分片数
    uploaded_chunks = Column(Integer, default=0, nullable=False)  # 已上传分片数
    upload_session_id = Column(String(255), nullable=True)  # 上传会话ID
    
    # 视频技术信息扩展
    audio_codec = Column(String(20), nullable=True)  # 音频编码格式
    video_codec = Column(String(20), nullable=True)  # 视频编码格式
    audio_bitrate = Column(Integer, nullable=True)  # 音频比特率
    video_bitrate = Column(Integer, nullable=True)  # 视频比特率
    thumbnail_path = Column(Text, nullable=True)  # 缩略图路径
    preview_images = Column(JSON, nullable=True, default=list)  # 预览图片列表
    
    # 元数据
    extra_metadata = Column(JSON, nullable=True, default=dict)  # 额外的元数据信息
    
    # 关联关系
    download_tasks = relationship("DownloadTask", back_populates="video")
    analysis_tasks = relationship("AnalysisTask", back_populates="video")
    video_tags = relationship("VideoTag", back_populates="video")
    user = relationship("User", back_populates="videos", foreign_keys=[uploaded_by])
    uploader = relationship("User", foreign_keys=[uploaded_by])
    
    def __repr__(self):
        return f"<Video(id={self.id}, title='{self.title[:50]}...', platform='{self.platform}')>"
    
    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "file_path": self.file_path,
            "file_size": self.file_size,
            "duration": self.duration,
            "resolution": self.resolution,
            "format": self.format,
            "fps": self.fps,
            "bitrate": self.bitrate,
            "codec": self.codec,
            "platform": self.platform,
            "original_url": self.original_url,
            "video_id": self.video_id,
            "author": self.author,
            "author_id": self.author_id,
            "channel_name": self.channel_name,
            "upload_date": self.upload_date,
            "view_count": self.view_count,
            "like_count": self.like_count,
            "comment_count": self.comment_count,
            "share_count": self.share_count,
            "status": self.status,
            "is_analyzed": self.is_analyzed,
            "upload_status": self.upload_status,
            "upload_progress": self.upload_progress,
            "upload_speed": self.upload_speed,
            "uploaded_by": self.uploaded_by,
            "upload_error": self.upload_error,
            "chunk_size": self.chunk_size,
            "total_chunks": self.total_chunks,
            "uploaded_chunks": self.uploaded_chunks,
            "upload_session_id": self.upload_session_id,
            "audio_codec": self.audio_codec,
            "video_codec": self.video_codec,
            "audio_bitrate": self.audio_bitrate,
            "video_bitrate": self.video_bitrate,
            "thumbnail_path": self.thumbnail_path,
            "preview_images": self.preview_images,
            "extra_metadata": self.extra_metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class DownloadTask(BaseModel):
    """下载任务模型"""
    __tablename__ = "download_tasks"
    
    # 关联用户
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # 任务信息
    url = Column(Text, nullable=False)
    platform = Column(String(50), nullable=True, index=True)  # 添加索引以支持按平台筛选
    status = Column(String(20), default="pending", nullable=False, index=True)  # 添加索引以支持按状态筛选
    progress = Column(Integer, default=0, nullable=False)  # 0-100
    
    # 下载配置
    quality = Column(String(20), nullable=True)  # best, worst, 720p, 1080p等
    format_preference = Column(String(20), nullable=True)  # mp4, avi等
    audio_only = Column(Boolean, default=False, nullable=False)
    
    # 结果信息
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=True, index=True)
    file_path = Column(Text, nullable=True)
    file_size = Column(BigInteger, nullable=True)  # 文件大小（字节）
    downloaded_size = Column(BigInteger, default=0, nullable=False)  # 已下载大小（字节）
    download_speed = Column(Integer, nullable=True)  # 下载速度（字节/秒）
    eta = Column(Integer, nullable=True)  # 预计剩余时间（秒）
    error_message = Column(Text, nullable=True)
    error_code = Column(String(50), nullable=True)  # 错误代码
    
    # 任务调度
    priority = Column(Integer, default=5, nullable=False, index=True)  # 1-10, 数字越小优先级越高，添加索引支持优先级排序
    retry_count = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)
    celery_task_id = Column(String(255), nullable=True, index=True)  # Celery任务ID
    
    # 时间信息
    started_at = Column(DateTime, nullable=True, index=True)  # 添加索引支持时间范围查询
    completed_at = Column(DateTime, nullable=True, index=True)  # 添加索引支持时间范围查询
    
    # 配置选项
    options = Column(JSON, nullable=True)  # 额外的下载选项
    
    # 关联关系
    user = relationship("User", back_populates="download_tasks")
    history_record = relationship("DownloadHistory", back_populates="task", uselist=False)
    video = relationship("Video", back_populates="download_tasks")
    
    # 复合索引定义
    __table_args__ = (
        Index('idx_download_task_user_status', 'user_id', 'status'),  # 用户状态复合索引
        Index('idx_download_task_status_priority', 'status', 'priority'),  # 状态优先级复合索引
        Index('idx_download_task_platform_status', 'platform', 'status'),  # 平台状态复合索引
        Index('idx_download_task_created_status', 'created_at', 'status'),  # 创建时间状态复合索引
    )
    
    def __repr__(self):
        return f"<DownloadTask(id={self.id}, url='{self.url[:50]}...', status='{self.status}')>"
    
    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "url": self.url,
            "platform": self.platform,
            "status": self.status,
            "progress": self.progress,
            "quality": self.quality,
            "format_preference": self.format_preference,
            "audio_only": self.audio_only,
            "video_id": self.video_id,
            "file_path": self.file_path,
            "file_size": self.file_size,
            "downloaded_size": self.downloaded_size,
            "download_speed": self.download_speed,
            "eta": self.eta,
            "error_message": self.error_message,
            "error_code": self.error_code,
            "priority": self.priority,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "options": self.options,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class AnalysisTask(BaseModel):
    """分析任务模型"""
    __tablename__ = "analysis_tasks"
    
    # 关联信息
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False, index=True)
    
    # 任务信息
    template_id = Column(Integer, nullable=True)  # 分析模板ID
    status = Column(String(20), default="pending", nullable=False)  # pending, processing, completed, failed, cancelled
    progress = Column(Integer, default=0, nullable=False)  # 0-100
    
    # 分析配置
    analysis_type = Column(String(50), nullable=True)  # visual, audio, content, full
    config = Column(JSON, nullable=True)  # 分析配置参数
    
    # 结果信息
    result_data = Column(JSON, nullable=True)  # 分析结果数据
    result_summary = Column(Text, nullable=True)  # 结果摘要
    confidence_score = Column(Float, nullable=True)  # 置信度分数
    
    # 错误信息
    error_message = Column(Text, nullable=True)
    error_code = Column(String(20), nullable=True)
    
    # 时间信息
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # 关联关系
    user = relationship("User", back_populates="analysis_tasks")
    video = relationship("Video", back_populates="analysis_tasks")
    
    def __repr__(self):
        return f"<AnalysisTask(id={self.id}, video_id={self.video_id}, status='{self.status}')>"
    
    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "video_id": self.video_id,
            "template_id": self.template_id,
            "status": self.status,
            "progress": self.progress,
            "analysis_type": self.analysis_type,
            "config": self.config,
            "result_data": self.result_data,
            "result_summary": self.result_summary,
            "confidence_score": self.confidence_score,
            "error_message": self.error_message,
            "error_code": self.error_code,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class Tag(BaseModel):
    """标签模型"""
    __tablename__ = "tags"
    
    name = Column(String(100), unique=True, nullable=False, index=True)
    category = Column(String(50), nullable=True, index=True)
    description = Column(Text, nullable=True)
    color = Column(String(7), nullable=True)  # 十六进制颜色代码
    
    # 层级关系
    parent_id = Column(Integer, ForeignKey("tags.id"), nullable=True)
    
    # 统计信息
    usage_count = Column(Integer, default=0, nullable=False)
    
    # 关联关系
    parent = relationship("Tag", remote_side="Tag.id")
    video_tags = relationship("VideoTag", back_populates="tag")
    
    def __repr__(self):
        return f"<Tag(id={self.id}, name='{self.name}', category='{self.category}')>"
    
    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "color": self.color,
            "parent_id": self.parent_id,
            "usage_count": self.usage_count,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class VideoTag(BaseModel):
    """视频标签关联模型"""
    __tablename__ = "video_tags"
    
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False, index=True)
    tag_id = Column(Integer, ForeignKey("tags.id"), nullable=False, index=True)
    
    # 标签属性
    confidence = Column(Float, default=1.0, nullable=False)  # 置信度 0.0-1.0
    created_by = Column(String(20), default="system", nullable=False)  # system, user, ai
    
    # 关联关系
    video = relationship("Video", back_populates="video_tags")
    tag = relationship("Tag", back_populates="video_tags")
    
    def __repr__(self):
        return f"<VideoTag(video_id={self.video_id}, tag_id={self.tag_id}, confidence={self.confidence})>"
    
    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "video_id": self.video_id,
            "tag_id": self.tag_id,
            "confidence": self.confidence,
            "created_by": self.created_by,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class AIConfig(BaseModel):
    """AI配置模型"""
    __tablename__ = "ai_configs"
    
    name = Column(String(100), nullable=False)  # 配置名称
    provider = Column(String(50), nullable=False)  # 提供商：openai, claude, gemini等
    api_key = Column(String(500), nullable=False)  # API密钥
    api_base = Column(String(500))  # API基础URL
    model = Column(String(100), nullable=False)  # 模型名称
    max_tokens = Column(Integer, default=4000)  # 最大token数
    temperature = Column(Float, default=0.7)  # 温度参数
    is_active = Column(Boolean, default=True)  # 是否启用
    
    def __repr__(self):
        return f"<AIConfig(id={self.id}, name={self.name}, provider={self.provider})>"
    
    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "provider": self.provider,
            "api_key": self.api_key,
            "api_base": self.api_base,
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "is_active": self.is_active,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }