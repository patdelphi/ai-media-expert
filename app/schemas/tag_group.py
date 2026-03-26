"""标签组相关数据模式

定义标签组和标签的数据结构。
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TagBase(BaseModel):
    """标签基础模型"""
    name: str = Field(min_length=1, max_length=50, description="标签名称")
    color: Optional[str] = Field(default=None, description="标签颜色（十六进制）")
    is_active: bool = Field(default=True, description="是否激活")
    
    @field_validator("color")
    def validate_color(cls, v):
        if v is not None:
            if not v.startswith('#') or len(v) != 7:
                raise ValueError('Color must be a valid hex color code (e.g., #FF0000)')
            try:
                int(v[1:], 16)
            except ValueError:
                raise ValueError('Color must be a valid hex color code')
        return v


class TagCreate(TagBase):
    """创建标签模型"""
    pass


class TagUpdate(BaseModel):
    """更新标签模型"""
    name: Optional[str] = Field(default=None, min_length=1, max_length=50)
    color: Optional[str] = Field(default=None)
    is_active: Optional[bool] = Field(default=None)
    
    @field_validator("color")
    def validate_color(cls, v):
        if v is not None:
            if not v.startswith('#') or len(v) != 7:
                raise ValueError('Color must be a valid hex color code (e.g., #FF0000)')
            try:
                int(v[1:], 16)
            except ValueError:
                raise ValueError('Color must be a valid hex color code')
        return v


class TagResponse(TagBase):
    """标签响应模型"""
    id: int
    tag_group_id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class TagGroupBase(BaseModel):
    """标签组基础模型"""
    name: str = Field(min_length=1, max_length=100, description="标签组名称")
    description: Optional[str] = Field(default=None, description="标签组描述")
    is_active: bool = Field(default=True, description="是否激活")


class TagGroupCreate(TagGroupBase):
    """创建标签组模型"""
    tags: Optional[List[TagCreate]] = Field(default=[], description="标签列表")


class TagGroupUpdate(BaseModel):
    """更新标签组模型"""
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = Field(default=None)
    is_active: Optional[bool] = Field(default=None)


class TagGroupResponse(TagGroupBase):
    """标签组响应模型"""
    id: int
    tags: List[TagResponse] = Field(default=[], description="标签列表")
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class TagGroupListResponse(BaseModel):
    """标签组列表响应模型"""
    id: int
    name: str
    description: Optional[str]
    is_active: bool
    tag_count: int = Field(description="标签数量")
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class BatchTagOperation(BaseModel):
    """批量标签操作模型"""
    tag_group_id: int
    tags: List[str] = Field(description="标签名称列表")


class TagGroupSearchParams(BaseModel):
    """标签组搜索参数"""
    search: Optional[str] = Field(default=None, description="搜索关键词")
    is_active: Optional[bool] = Field(default=None, description="是否激活")
    include_tags: bool = Field(default=True, description="是否包含标签列表")
