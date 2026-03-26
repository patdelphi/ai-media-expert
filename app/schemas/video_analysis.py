"""视频解析相关数据模式

定义视频解析任务、AI配置等相关的数据结构。
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class VideoAnalysisBase(BaseModel):
    """视频解析基础模型"""
    video_file_id: int = Field(description="视频文件ID")
    template_id: Optional[int] = Field(default=None, description="提示词模板ID")
    tag_group_ids: Optional[List[int]] = Field(default=None, description="标签组ID列表")
    ai_config_id: int = Field(description="AI配置ID")


class VideoAnalysisCreate(VideoAnalysisBase):
    """创建视频解析任务模型"""
    prompt_content: Optional[str] = Field(default=None, description="自定义提示词内容")


class VideoAnalysisUpdate(BaseModel):
    """更新视频解析任务模型"""
    status: Optional[str] = Field(default=None, description="任务状态")
    progress: Optional[int] = Field(default=None, ge=0, le=100, description="处理进度")
    analysis_result: Optional[str] = Field(default=None, description="解析结果")
    result_summary: Optional[str] = Field(default=None, description="结果摘要")
    result_metadata: Optional[Dict[str, Any]] = Field(default=None, description="结果元数据")
    confidence_score: Optional[float] = Field(default=None, ge=0, le=1, description="置信度分数")
    quality_score: Optional[float] = Field(default=None, ge=0, le=1, description="质量分数")
    error_message: Optional[str] = Field(default=None, description="错误信息")
    error_code: Optional[str] = Field(default=None, description="错误代码")
    
    @field_validator("status")
    def validate_status(cls, v):
        if v is not None:
            allowed_statuses = ['pending', 'processing', 'completed', 'failed', 'cancelled']
            if v not in allowed_statuses:
                raise ValueError(f'Status must be one of: {", ".join(allowed_statuses)}')
        return v


class VideoAnalysisResponse(VideoAnalysisBase):
    """视频解析响应模型"""
    id: int
    prompt_content: str
    video_url: Optional[str] = Field(default=None, description="视频文件的可访问URL")
    status: str
    progress: int
    analysis_result: Optional[str] = None
    result_summary: Optional[str] = None
    result_metadata: Optional[Dict[str, Any]] = None
    confidence_score: Optional[float] = None
    quality_score: Optional[float] = None
    processing_time: Optional[float] = None
    token_usage: Optional[Dict[str, Any]] = None
    cost_estimate: Optional[float] = None
    # AI API调试信息
    api_call_time: Optional[datetime] = None
    api_response_time: Optional[datetime] = None
    api_duration: Optional[float] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    model_name: Optional[str] = None
    api_provider: Optional[str] = None
    request_id: Optional[str] = None
    debug_info: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class VideoAnalysisListResponse(BaseModel):
    """视频解析列表响应模型"""
    id: int
    video_file_id: int
    template_id: Optional[int] = None
    ai_config_id: int
    status: str
    progress: int
    result_summary: Optional[str] = None
    confidence_score: Optional[float] = None
    processing_time: Optional[float] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)





class PromptTemplateResponse(BaseModel):
    """提示词模板响应模型"""
    id: int
    title: str
    content: str
    is_active: bool
    usage_count: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class TagGroupResponse(BaseModel):
    """标签组响应模型"""
    id: int
    name: str
    description: Optional[str] = None
    is_active: bool
    tags: List[Dict[str, Any]] = []
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class VideoFileInfo(BaseModel):
    """视频文件信息模型"""
    id: int
    original_filename: str
    saved_filename: str
    title: Optional[str] = None
    file_size: int
    duration: Optional[float] = None
    width: Optional[int] = None
    height: Optional[int] = None
    format_name: Optional[str] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class AnalysisStreamChunk(BaseModel):
    """流式解析数据块模型"""
    type: str = Field(description="数据类型: progress, content, error, complete")
    content: Optional[str] = Field(default=None, description="内容数据")
    progress: Optional[int] = Field(default=None, description="进度百分比")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="元数据")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")


class AnalysisStartRequest(BaseModel):
    """开始解析请求模型"""
    video_file_id: int = Field(description="视频文件ID")
    template_id: Optional[int] = Field(default=None, description="提示词模板ID")
    tag_group_ids: Optional[List[int]] = Field(default=None, description="标签组ID列表")
    custom_prompt: Optional[str] = Field(default=None, description="自定义提示词")
    ai_config_id: int = Field(description="AI配置ID")
    transmission_method: Optional[str] = Field(default="url", description="视频传输方式: url, base64, upload")
    
    @field_validator("transmission_method")
    def validate_transmission_method(cls, v):
        if v is not None:
            allowed_methods = ['url', 'base64', 'upload']
            if v not in allowed_methods:
                raise ValueError(f'Transmission method must be one of: {", ".join(allowed_methods)}')
        return v


class AnalysisStartResponse(BaseModel):
    """开始解析响应模型"""
    analysis_id: int = Field(description="解析任务ID")
    status: str = Field(description="任务状态")
    message: str = Field(description="响应消息")
    stream_url: Optional[str] = Field(default=None, description="流式结果URL")
