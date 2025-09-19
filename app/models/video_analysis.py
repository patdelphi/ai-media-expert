"""视频解析数据模型

定义视频解析任务相关的数据模型，用于AI驱动的视频内容解析。
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column, Integer, String, Text, JSON, Float, Boolean, DateTime, ForeignKey
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import BaseModel


class VideoAnalysis(BaseModel):
    """视频解析任务模型
    
    用于存储基于AI的视频内容解析任务信息，包括提示词模板、
    标签组、AI配置和解析结果等。
    """
    __tablename__ = "video_analyses"
    
    # 关联信息
    user_id = Column(String, ForeignKey('users.id'), nullable=False, index=True)
    video_file_id = Column(Integer, ForeignKey('uploaded_files.id'), nullable=False, index=True)
    template_id = Column(Integer, ForeignKey('prompt_templates.id'), nullable=True, index=True)
    
    # 标签组信息（JSON数组存储多个标签组ID）
    tag_group_ids = Column(JSON, nullable=True, comment="使用的标签组ID列表")
    
    # 提示词信息
    prompt_content = Column(Text, nullable=False, comment="最终生成的完整提示词")
    
    # 视频URL信息（用于支持视频理解模型）
    video_url = Column(String(1000), nullable=True, comment="视频文件的可访问URL，用于AI视频理解")
    
    # 视频文件路径（用于Base64编码备选方案）
    video_file_path = Column(String(1000), nullable=True, comment="视频文件的本地路径，用于Base64编码")
    
    # 视频传输方式
    transmission_method = Column(String(20), default='url', nullable=False, comment="视频传输方式: url, base64, upload")
    
    # AI配置信息
    ai_config_id = Column(Integer, ForeignKey('ai_configs.id'), nullable=False, index=True, comment="AI配置ID")
    
    # 任务状态
    status = Column(String(20), default='pending', nullable=False, index=True)
    # 状态值: pending, processing, completed, failed, cancelled
    
    progress = Column(Integer, default=0, nullable=False, comment="处理进度0-100")
    
    # 解析结果
    analysis_result = Column(Text, nullable=True, comment="完整的解析结果")
    result_summary = Column(Text, nullable=True, comment="结果摘要")
    result_metadata = Column(JSON, nullable=True, comment="结果元数据")
    
    # 质量评估
    confidence_score = Column(Float, nullable=True, comment="置信度分数0-1")
    quality_score = Column(Float, nullable=True, comment="结果质量分数0-1")
    
    # 性能指标
    processing_time = Column(Float, nullable=True, comment="处理时间（秒）")
    token_usage = Column(JSON, nullable=True, comment="Token使用统计")
    cost_estimate = Column(Float, nullable=True, comment="预估成本")
    
    # AI API调试信息
    api_call_time = Column(DateTime(timezone=True), nullable=True, comment="API调用时间")
    api_response_time = Column(DateTime(timezone=True), nullable=True, comment="API响应时间")
    api_duration = Column(Float, nullable=True, comment="API调用耗时（秒）")
    prompt_tokens = Column(Integer, nullable=True, comment="输入Token数量")
    completion_tokens = Column(Integer, nullable=True, comment="输出Token数量")
    total_tokens = Column(Integer, nullable=True, comment="总Token数量")
    temperature = Column(Float, nullable=True, comment="AI温度参数")
    max_tokens = Column(Integer, nullable=True, comment="最大Token限制")
    model_name = Column(String(100), nullable=True, comment="使用的AI模型名称")
    api_provider = Column(String(50), nullable=True, comment="API提供商")
    request_id = Column(String(100), nullable=True, comment="API请求ID")
    debug_info = Column(JSON, nullable=True, comment="详细调试信息")
    
    # 错误信息
    error_message = Column(Text, nullable=True, comment="错误信息")
    error_code = Column(String(50), nullable=True, comment="错误代码")
    error_details = Column(JSON, nullable=True, comment="详细错误信息")
    
    # 时间信息
    started_at = Column(DateTime(timezone=True), nullable=True, comment="开始时间")
    completed_at = Column(DateTime(timezone=True), nullable=True, comment="完成时间")
    
    # 系统字段
    is_active = Column(Boolean, default=True, nullable=False, comment="是否有效")
    
    # 关联关系
    user = relationship("User", back_populates="video_analyses")
    video_file = relationship("UploadedFile", back_populates="video_analyses")
    template = relationship("PromptTemplate", back_populates="video_analyses")
    ai_config = relationship("AIConfig")
    
    def __repr__(self):
        return f"<VideoAnalysis(id={self.id}, video_file_id={self.video_file_id}, status='{self.status}')>"
    
    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "video_file_id": self.video_file_id,
            "template_id": self.template_id,
            "tag_group_ids": self.tag_group_ids,
            "prompt_content": self.prompt_content,
            "ai_config_id": self.ai_config_id,
            "status": self.status,
            "progress": self.progress,
            "analysis_result": self.analysis_result,
            "result_summary": self.result_summary,
            "result_metadata": self.result_metadata,
            "confidence_score": self.confidence_score,
            "quality_score": self.quality_score,
            "processing_time": self.processing_time,
            "token_usage": self.token_usage,
            "cost_estimate": self.cost_estimate,
            "api_call_time": self.api_call_time,
            "api_response_time": self.api_response_time,
            "api_duration": self.api_duration,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "model_name": self.model_name,
            "api_provider": self.api_provider,
            "request_id": self.request_id,
            "debug_info": self.debug_info,
            "error_message": self.error_message,
            "error_code": self.error_code,
            "error_details": self.error_details,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "is_active": self.is_active,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
    
    @property
    def duration_seconds(self) -> Optional[float]:
        """计算处理持续时间（秒）"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    @property
    def is_completed(self) -> bool:
        """是否已完成"""
        return self.status in ['completed', 'failed', 'cancelled']
    
    @property
    def is_successful(self) -> bool:
        """是否成功完成"""
        return self.status == 'completed' and self.analysis_result is not None