"""提示词模板数据模式

定义提示词模板API的请求和响应数据结构。
"""

from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime


class PromptTemplateBase(BaseModel):
    """提示词模板基础模型"""
    title: str = Field(description="模板标题")
    content: str = Field(description="模板内容")
    is_active: Optional[bool] = Field(default=True, description="是否启用")


class PromptTemplateCreate(PromptTemplateBase):
    """创建提示词模板模型"""
    pass


class PromptTemplateUpdate(BaseModel):
    """更新提示词模板模型"""
    title: Optional[str] = Field(default=None, description="模板标题")
    content: Optional[str] = Field(default=None, description="模板内容")
    is_active: Optional[bool] = Field(default=None, description="是否启用")


class PromptTemplateResponse(PromptTemplateBase):
    """提示词模板响应模型"""
    id: int
    usage_count: int = Field(description="使用次数")
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
