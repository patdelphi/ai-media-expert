"""视频相关数据模式

定义视频、下载任务、分析任务等相关的数据结构。"""

from datetime import datetime, date
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, HttpUrl, validator


class VideoBase(BaseModel):
    """视频基础模型"""
    title: str = Field(description="视频标题")
    description: Optional[str] = Field(default=None, description="视频描述")
    platform: Optional[str] = Field(default=None, description="视频平台")
    original_url: Optional[HttpUrl] = Field(default=None, description="原始URL")
    author: Optional[str] = Field(default=None, description="作者")


class VideoCreate(VideoBase):
    """视频创建模型"""
    original_filename: Optional[str] = Field(default=None, description="原始文件名")
    file_path: str = Field(description="文件路径")
    file_size: Optional[int] = Field(default=None, description="文件大小")
    duration: Optional[int] = Field(default=None, description="视频时长（秒）")
    resolution: Optional[str] = Field(default=None, description="分辨率")
    format: Optional[str] = Field(default=None, description="视频格式")
    extra_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="额外元数据")
    status: Optional[str] = Field(default="active", description="状态")
    is_analyzed: Optional[bool] = Field(default=False, description="是否已分析")


class VideoUpdate(BaseModel):
    """视频更新模型"""
    title: Optional[str] = Field(default=None, description="视频标题")
    description: Optional[str] = Field(default=None, description="视频描述")
    author: Optional[str] = Field(default=None, description="作者")


class VideoListResponse(BaseModel):
    """视频列表响应模型"""
    id: int
    title: str
    platform: Optional[str]
    author: Optional[str]
    duration: Optional[int]
    resolution: Optional[str]
    format: Optional[str]
    file_size: Optional[int]
    upload_date: Optional[date]
    view_count: Optional[int]
    like_count: Optional[int]
    is_analyzed: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class VideoResponse(BaseModel):
    """视频详情响应模型"""
    id: int
    title: str
    description: Optional[str]
    file_path: str
    file_size: Optional[int]
    duration: Optional[int]
    resolution: Optional[str]
    format: Optional[str]
    fps: Optional[float]
    bitrate: Optional[int]
    codec: Optional[str]
    platform: Optional[str]
    original_url: Optional[str]
    video_id: Optional[str]
    author: Optional[str]
    author_id: Optional[str]
    channel_name: Optional[str]
    upload_date: Optional[date]
    view_count: Optional[int]
    like_count: Optional[int]
    comment_count: Optional[int]
    share_count: Optional[int]
    status: str
    is_analyzed: bool
    extra_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="额外元数据")
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class DownloadTaskCreate(BaseModel):
    """下载任务创建模型"""
    url: HttpUrl = Field(description="视频URL")
    quality: Optional[str] = Field(default="best", description="视频质量")
    format_preference: Optional[str] = Field(default="mp4", description="格式偏好")
    audio_only: bool = Field(default=False, description="仅下载音频")
    priority: int = Field(default=5, ge=1, le=10, description="优先级")
    options: Optional[Dict[str, Any]] = Field(default=None, description="额外选项")
    
    @validator('quality')
    def validate_quality(cls, v):
        allowed_qualities = ['best', 'worst', '720p', '1080p', '480p', '360p', '240p']
        if v not in allowed_qualities:
            raise ValueError(f'Quality must be one of: {", ".join(allowed_qualities)}')
        return v
    
    @validator('format_preference')
    def validate_format(cls, v):
        allowed_formats = ['mp4', 'avi', 'mkv', 'mov', 'flv', 'webm']
        if v not in allowed_formats:
            raise ValueError(f'Format must be one of: {", ".join(allowed_formats)}')
        return v


class DownloadTaskResponse(BaseModel):
    """下载任务响应模型"""
    id: int
    url: str
    platform: Optional[str]
    status: str
    progress: int
    quality: Optional[str]
    format_preference: Optional[str]
    audio_only: bool
    video_id: Optional[int]
    file_path: Optional[str]
    file_size: Optional[int]
    downloaded_size: int
    download_speed: Optional[int]
    eta: Optional[int]
    error_message: Optional[str]
    error_code: Optional[str]
    priority: int
    retry_count: int
    max_retries: int
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    options: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class AnalysisTaskCreate(BaseModel):
    """分析任务创建模型"""
    video_id: int = Field(description="视频ID")
    template_id: Optional[int] = Field(default=None, description="分析模板ID")
    analysis_type: str = Field(default="full", description="分析类型")
    config: Optional[Dict[str, Any]] = Field(default=None, description="分析配置")
    
    @validator('analysis_type')
    def validate_analysis_type(cls, v):
        allowed_types = ['visual', 'audio', 'content', 'full']
        if v not in allowed_types:
            raise ValueError(f'Analysis type must be one of: {", ".join(allowed_types)}')
        return v


class AnalysisTaskResponse(BaseModel):
    """分析任务响应模型"""
    id: int
    video_id: int
    template_id: Optional[int]
    status: str
    progress: int
    analysis_type: Optional[str]
    config: Optional[Dict[str, Any]]
    result_data: Optional[Dict[str, Any]]
    result_summary: Optional[str]
    confidence_score: Optional[float]
    error_message: Optional[str]
    error_code: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TagCreate(BaseModel):
    """标签创建模型"""
    name: str = Field(min_length=1, max_length=100, description="标签名称")
    category: Optional[str] = Field(default=None, max_length=50, description="标签分类")
    description: Optional[str] = Field(default=None, description="标签描述")
    color: Optional[str] = Field(default=None, pattern=r'^#[0-9A-Fa-f]{6}$', description="颜色代码")
    parent_id: Optional[int] = Field(default=None, description="父标签ID")


class TagResponse(BaseModel):
    """标签响应模型"""
    id: int
    name: str
    category: Optional[str]
    description: Optional[str]
    color: Optional[str]
    parent_id: Optional[int]
    usage_count: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class VideoTagCreate(BaseModel):
    """视频标签关联创建模型"""
    video_id: int = Field(description="视频ID")
    tag_id: int = Field(description="标签ID")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="置信度")
    created_by: str = Field(default="user", description="创建者")
    
    @validator('created_by')
    def validate_created_by(cls, v):
        allowed_creators = ['system', 'user', 'ai']
        if v not in allowed_creators:
            raise ValueError(f'Created by must be one of: {", ".join(allowed_creators)}')
        return v


class VideoTagResponse(BaseModel):
    """视频标签关联响应模型"""
    id: int
    video_id: int
    tag_id: int
    confidence: float
    created_by: str
    created_at: datetime
    updated_at: datetime
    
    # 关联的标签信息
    tag: Optional[TagResponse] = None
    
    class Config:
        from_attributes = True


class BatchTagOperation(BaseModel):
    """批量标签操作模型"""
    video_ids: List[int] = Field(description="视频ID列表")
    tag_ids: List[int] = Field(description="标签ID列表")
    operation: str = Field(description="操作类型")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="置信度")
    
    @validator('operation')
    def validate_operation(cls, v):
        allowed_operations = ['add', 'remove', 'replace']
        if v not in allowed_operations:
            raise ValueError(f'Operation must be one of: {", ".join(allowed_operations)}')
        return v


# AI配置schemas
class AIConfigBase(BaseModel):
    """AI配置基础模型"""
    name: str = Field(description="配置名称")
    provider: str = Field(description="AI提供商")
    api_key: str = Field(description="API密钥")
    api_base: Optional[str] = Field(default=None, description="API基础URL")
    model: str = Field(description="模型名称")
    max_tokens: Optional[int] = Field(default=4000, description="最大令牌数")
    temperature: Optional[float] = Field(default=0.7, description="温度参数")
    is_active: Optional[bool] = Field(default=True, description="是否激活")


class AIConfigCreate(AIConfigBase):
    """AI配置创建模型"""
    pass


class AIConfigUpdate(BaseModel):
    """AI配置更新模型"""
    name: Optional[str] = Field(default=None, description="配置名称")
    provider: Optional[str] = Field(default=None, description="AI提供商")
    api_key: Optional[str] = Field(default=None, description="API密钥")
    api_base: Optional[str] = Field(default=None, description="API基础URL")
    model: Optional[str] = Field(default=None, description="模型名称")
    max_tokens: Optional[int] = Field(default=None, description="最大令牌数")
    temperature: Optional[float] = Field(default=None, description="温度参数")
    is_active: Optional[bool] = Field(default=None, description="是否激活")


class AIConfigResponse(AIConfigBase):
    """AI配置响应模型"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class AIConfigPublicResponse(BaseModel):
    """AI配置公开响应模型（隐藏敏感信息）"""
    id: int
    name: str
    provider: str
    model: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# 分析请求和响应schemas
class AnalysisRequest(BaseModel):
    """分析请求模型"""
    analysis_types: List[str] = Field(description="分析类型列表")
    ai_config_id: int = Field(description="AI配置ID")
    max_frames: Optional[int] = Field(default=10, description="最大帧数")
    confidence_threshold: Optional[float] = Field(default=0.7, description="置信度阈值")
    
    @validator('analysis_types')
    def validate_analysis_types(cls, v):
        allowed_types = ['visual', 'audio', 'content', 'quality']
        for analysis_type in v:
            if analysis_type not in allowed_types:
                raise ValueError(f'Analysis type must be one of: {", ".join(allowed_types)}')
        return v


class AnalysisResponse(BaseModel):
    """分析响应模型"""
    task_id: int
    video_id: int
    status: str
    progress: int
    results: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    message: Optional[str] = None