"""系统配置相关数据模式

定义系统配置的数据结构。
"""

from datetime import datetime
from typing import Optional, Any, Dict

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SystemConfigBase(BaseModel):
    """系统配置基础模型"""
    key: str = Field(description="配置键")
    value: str = Field(description="配置值")
    description: Optional[str] = Field(default=None, description="配置描述")
    category: str = Field(default="general", description="配置分类")
    is_public: bool = Field(default=False, description="是否为公开配置")
    is_active: bool = Field(default=True, description="是否启用")
    data_type: str = Field(default="string", description="数据类型")
    validation_rule: Optional[str] = Field(default=None, description="验证规则")
    default_value: Optional[str] = Field(default=None, description="默认值")
    
    @field_validator("key")
    def validate_key(cls, v):
        if not v or not v.strip():
            raise ValueError('Configuration key cannot be empty')
        # 配置键只能包含字母、数字、下划线和点号
        import re
        if not re.match(r'^[a-zA-Z0-9_.]+$', v):
            raise ValueError('Configuration key can only contain letters, numbers, underscores and dots')
        return v.strip()
    
    @field_validator("data_type")
    def validate_data_type(cls, v):
        allowed_types = ['string', 'integer', 'float', 'boolean', 'json', 'text']
        if v not in allowed_types:
            raise ValueError(f'Data type must be one of: {", ".join(allowed_types)}')
        return v
    
    @field_validator("category")
    def validate_category(cls, v):
        if not v or not v.strip():
            raise ValueError('Category cannot be empty')
        return v.strip()


class SystemConfigCreate(SystemConfigBase):
    """系统配置创建模型"""
    is_encrypted: bool = Field(default=False, description="是否加密存储")


class SystemConfigUpdate(BaseModel):
    """系统配置更新模型"""
    value: Optional[str] = Field(default=None, description="配置值")
    description: Optional[str] = Field(default=None, description="配置描述")
    category: Optional[str] = Field(default=None, description="配置分类")
    is_public: Optional[bool] = Field(default=None, description="是否为公开配置")
    is_active: Optional[bool] = Field(default=None, description="是否启用")
    data_type: Optional[str] = Field(default=None, description="数据类型")
    validation_rule: Optional[str] = Field(default=None, description="验证规则")
    default_value: Optional[str] = Field(default=None, description="默认值")
    is_encrypted: Optional[bool] = Field(default=None, description="是否加密存储")
    
    @field_validator("data_type")
    def validate_data_type(cls, v):
        if v is not None:
            allowed_types = ['string', 'integer', 'float', 'boolean', 'json', 'text']
            if v not in allowed_types:
                raise ValueError(f'Data type must be one of: {", ".join(allowed_types)}')
        return v
    
    @field_validator("category")
    def validate_category(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError('Category cannot be empty')
        return v.strip() if v else v


class SystemConfigResponse(BaseModel):
    """系统配置响应模型（完整信息）"""
    id: int
    key: str
    value: str
    description: Optional[str]
    category: str
    is_public: bool
    is_encrypted: bool
    is_active: bool
    data_type: str
    validation_rule: Optional[str]
    default_value: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class SystemConfigPublicResponse(BaseModel):
    """系统配置公开响应模型（不包含敏感信息）"""
    id: int
    key: str
    value: str
    description: Optional[str]
    category: str
    data_type: str
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class SystemConfigBatchUpdate(BaseModel):
    """批量更新系统配置模型"""
    configs: Dict[str, str] = Field(description="配置键值对")
    category: Optional[str] = Field(default=None, description="限制更新的配置分类")


class SystemConfigValidation(BaseModel):
    """配置验证模型"""
    key: str = Field(description="配置键")
    value: str = Field(description="配置值")
    data_type: str = Field(description="数据类型")
    validation_rule: Optional[str] = Field(default=None, description="验证规则")


class SystemConfigCategory(BaseModel):
    """配置分类模型"""
    category: str = Field(description="分类名称")
    count: int = Field(description="配置数量")
    description: Optional[str] = Field(default=None, description="分类描述")


class SystemConfigExport(BaseModel):
    """配置导出模型"""
    categories: Optional[list[str]] = Field(default=None, description="导出的分类列表")
    include_encrypted: bool = Field(default=False, description="是否包含加密配置")
    format: str = Field(default="json", description="导出格式")
    
    @field_validator("format")
    def validate_format(cls, v):
        allowed_formats = ['json', 'yaml', 'env']
        if v not in allowed_formats:
            raise ValueError(f'Export format must be one of: {", ".join(allowed_formats)}')
        return v


class SystemConfigImport(BaseModel):
    """配置导入模型"""
    data: str = Field(description="导入数据")
    format: str = Field(default="json", description="数据格式")
    overwrite: bool = Field(default=False, description="是否覆盖已存在的配置")
    category: Optional[str] = Field(default=None, description="导入到指定分类")
    
    @field_validator("format")
    def validate_format(cls, v):
        allowed_formats = ['json', 'yaml', 'env']
        if v not in allowed_formats:
            raise ValueError(f'Import format must be one of: {", ".join(allowed_formats)}')
        return v
