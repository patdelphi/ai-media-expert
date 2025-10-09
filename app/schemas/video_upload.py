"""视频上传相关数据模式

定义视频上传的请求、响应和状态管理数据结构。
"""

from datetime import datetime
from typing import List, Optional
from enum import Enum

from pydantic import BaseModel, Field, validator


class UploadStatus(str, Enum):
    """上传状态枚举"""
    PENDING = "pending"
    UPLOADING = "uploading"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class ChunkUploadRequest(BaseModel):
    """分片上传请求"""
    upload_session_id: str = Field(description="上传会话ID")
    chunk_index: int = Field(ge=0, description="分片索引")
    total_chunks: int = Field(gt=0, description="总分片数")
    chunk_size: int = Field(gt=0, description="分片大小")
    file_hash: Optional[str] = Field(default=None, description="文件哈希值")
    chunk_hash: Optional[str] = Field(default=None, description="分片哈希值")


class InitUploadRequest(BaseModel):
    """初始化上传请求"""
    filename: str = Field(min_length=1, max_length=500, description="原始文件名")
    file_size: int = Field(gt=0, description="文件大小（字节）")
    file_hash: Optional[str] = Field(default=None, description="文件MD5哈希")
    chunk_size: int = Field(default=1024*1024, gt=0, description="分片大小")
    title: Optional[str] = Field(default=None, max_length=500, description="视频标题")
    description: Optional[str] = Field(default=None, description="视频描述")
    
    @validator('filename')
    def validate_filename(cls, v):
        # 检查文件扩展名
        allowed_extensions = ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv', '.m4v']
        if not any(v.lower().endswith(ext) for ext in allowed_extensions):
            raise ValueError(f'Unsupported file format. Allowed: {", ".join(allowed_extensions)}')
        return v


class InitUploadResponse(BaseModel):
    """初始化上传响应"""
    upload_session_id: str = Field(description="上传会话ID")
    video_id: int = Field(description="视频ID")
    chunk_size: int = Field(description="分片大小")
    total_chunks: int = Field(description="总分片数")
    uploaded_chunks: List[int] = Field(default=[], description="已上传的分片索引列表")
    upload_url: str = Field(description="上传接口URL")


class ChunkUploadResponse(BaseModel):
    """分片上传响应"""
    chunk_index: int = Field(description="分片索引")
    uploaded: bool = Field(description="是否上传成功")
    progress: float = Field(ge=0, le=100, description="总体上传进度")
    uploaded_chunks: int = Field(description="已上传分片数")
    total_chunks: int = Field(description="总分片数")
    upload_speed: Optional[float] = Field(default=None, description="上传速度（字节/秒）")


class UploadProgressResponse(BaseModel):
    """上传进度响应"""
    video_id: int = Field(description="视频ID")
    upload_session_id: str = Field(description="上传会话ID")
    status: UploadStatus = Field(description="上传状态")
    progress: float = Field(ge=0, le=100, description="上传进度")
    uploaded_chunks: int = Field(description="已上传分片数")
    total_chunks: int = Field(description="总分片数")
    upload_speed: Optional[float] = Field(default=None, description="上传速度")
    error_message: Optional[str] = Field(default=None, description="错误信息")
    estimated_time: Optional[int] = Field(default=None, description="预计剩余时间（秒）")


class UploadControlRequest(BaseModel):
    """上传控制请求"""
    upload_session_id: str = Field(description="上传会话ID")
    action: str = Field(description="操作类型：pause, resume, cancel")
    
    @validator('action')
    def validate_action(cls, v):
        allowed_actions = ['pause', 'resume', 'cancel']
        if v not in allowed_actions:
            raise ValueError(f'Invalid action. Allowed: {", ".join(allowed_actions)}')
        return v


class VideoUploadResponse(BaseModel):
    """视频上传完成响应"""
    video_id: int = Field(description="视频ID")
    title: str = Field(description="视频标题")
    filename: str = Field(description="文件名")
    file_size: int = Field(description="文件大小")
    duration: Optional[int] = Field(default=None, description="视频时长（秒）")
    resolution: Optional[str] = Field(default=None, description="分辨率")
    format: Optional[str] = Field(default=None, description="视频格式")
    codec: Optional[str] = Field(default=None, description="编码格式")
    thumbnail_url: Optional[str] = Field(default=None, description="缩略图URL")
    upload_status: UploadStatus = Field(description="上传状态")
    created_at: datetime = Field(description="创建时间")


class VideoListResponse(BaseModel):
    """视频列表响应"""
    videos: List[VideoUploadResponse] = Field(description="视频列表")
    total: int = Field(description="总数")
    page: int = Field(description="当前页")
    size: int = Field(description="每页大小")
    pages: int = Field(description="总页数")


class UploadSessionInfo(BaseModel):
    """上传会话信息"""
    upload_session_id: str = Field(description="上传会话ID")
    video_id: int = Field(description="视频ID")
    filename: str = Field(description="文件名")
    file_size: int = Field(description="文件大小")
    chunk_size: int = Field(description="分片大小")
    total_chunks: int = Field(description="总分片数")
    uploaded_chunks: int = Field(description="已上传分片数")
    status: UploadStatus = Field(description="上传状态")
    progress: float = Field(description="上传进度")
    upload_speed: Optional[float] = Field(default=None, description="上传速度")
    error_message: Optional[str] = Field(default=None, description="错误信息")
    created_at: datetime = Field(description="创建时间")
    updated_at: datetime = Field(description="更新时间")


class FileValidationResponse(BaseModel):
    """文件验证响应"""
    valid: bool = Field(description="是否有效")
    file_type: Optional[str] = Field(default=None, description="文件类型")
    file_size: Optional[int] = Field(default=None, description="文件大小")
    duration: Optional[int] = Field(default=None, description="视频时长")
    resolution: Optional[str] = Field(default=None, description="分辨率")
    error_message: Optional[str] = Field(default=None, description="错误信息")