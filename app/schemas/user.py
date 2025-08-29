"""用户管理相关数据模式

定义用户管理、用户列表等相关的数据结构。
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, validator

from app.schemas.auth import UserResponse
from app.schemas.common import PaginatedResponse


class UserListItem(BaseModel):
    """用户列表项模型"""
    id: int
    email: EmailStr
    username: Optional[str]
    full_name: Optional[str]
    avatar_url: Optional[str]
    is_active: bool
    is_verified: bool
    role: str
    last_login_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserListResponse(PaginatedResponse[UserListItem]):
    """用户列表响应模型"""
    pass


class AdminUserCreate(BaseModel):
    """管理员创建用户模型"""
    email: Optional[EmailStr] = Field(default=None, description="用户邮箱")
    username: Optional[str] = Field(default=None, min_length=3, max_length=50, description="用户名")
    full_name: Optional[str] = Field(default=None, max_length=100, description="全名")
    password: Optional[str] = Field(default=None, min_length=8, max_length=100, description="密码")
    role: str = Field(default="user", description="用户角色")
    is_active: bool = Field(default=True, description="是否激活")
    is_verified: bool = Field(default=False, description="是否验证")
    
    @validator('username')
    def validate_username(cls, v):
        if v is not None:
            import re
            if not re.match(r'^[a-zA-Z0-9_-]+$', v):
                raise ValueError('Username can only contain letters, numbers, underscores and hyphens')
        return v
    
    @validator('password')
    def validate_password(cls, v):
        if v is not None:
            if len(v) < 8:
                raise ValueError('Password must be at least 8 characters long')
            
            has_letter = any(c.isalpha() for c in v)
            has_digit = any(c.isdigit() for c in v)
            
            if not (has_letter and has_digit):
                raise ValueError('Password must contain both letters and numbers')
        return v
    
    @validator('role')
    def validate_role(cls, v):
        allowed_roles = ['user', 'premium', 'admin']
        if v not in allowed_roles:
            raise ValueError(f'Role must be one of: {", ".join(allowed_roles)}')
        return v


class AdminUserUpdate(BaseModel):
    """管理员更新用户模型"""
    email: Optional[EmailStr] = Field(default=None, description="用户邮箱")
    username: Optional[str] = Field(default=None, min_length=3, max_length=50, description="用户名")
    full_name: Optional[str] = Field(default=None, max_length=100, description="全名")
    role: Optional[str] = Field(default=None, description="用户角色")
    is_active: Optional[bool] = Field(default=None, description="是否激活")
    is_verified: Optional[bool] = Field(default=None, description="是否验证")
    
    @validator('username')
    def validate_username(cls, v):
        if v is not None:
            import re
            if not re.match(r'^[a-zA-Z0-9_-]+$', v):
                raise ValueError('Username can only contain letters, numbers, underscores and hyphens')
        return v
    
    @validator('role')
    def validate_role(cls, v):
        if v is not None:
            allowed_roles = ['user', 'premium', 'admin']
            if v not in allowed_roles:
                raise ValueError(f'Role must be one of: {", ".join(allowed_roles)}')
        return v


class UserStatusUpdate(BaseModel):
    """用户状态更新模型"""
    is_active: bool = Field(description="是否激活")
    reason: Optional[str] = Field(default=None, max_length=500, description="操作原因")


class UserSearchParams(BaseModel):
    """用户搜索参数模型"""
    search: Optional[str] = Field(default=None, description="搜索关键词（用户名、邮箱、全名）")
    role: Optional[str] = Field(default=None, description="角色筛选")
    is_active: Optional[bool] = Field(default=None, description="状态筛选")
    is_verified: Optional[bool] = Field(default=None, description="验证状态筛选")
    
    @validator('role')
    def validate_role(cls, v):
        if v is not None:
            allowed_roles = ['user', 'premium', 'admin']
            if v not in allowed_roles:
                raise ValueError(f'Role must be one of: {", ".join(allowed_roles)}')
        return v