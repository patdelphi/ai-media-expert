"""认证相关数据模式

定义用户认证、注册、登录等相关的数据结构。
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserBase(BaseModel):
    """用户基础模型"""
    email: EmailStr = Field(description="用户邮箱")
    username: Optional[str] = Field(default=None, min_length=3, max_length=50, description="用户名")
    full_name: Optional[str] = Field(default=None, max_length=100, description="全名")
    
    @field_validator("username")
    def validate_username(cls, v):
        if v is not None:
            # 用户名只能包含字母、数字、下划线和连字符
            import re
            if not re.match(r'^[a-zA-Z0-9_-]+$', v):
                raise ValueError('Username can only contain letters, numbers, underscores and hyphens')
        return v


class UserCreate(UserBase):
    """用户创建模型"""
    password: str = Field(min_length=8, max_length=100, description="密码")
    
    @field_validator("password")
    def validate_password(cls, v):
        # 密码强度验证
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        # 检查是否包含字母和数字
        has_letter = any(c.isalpha() for c in v)
        has_digit = any(c.isdigit() for c in v)
        
        if not (has_letter and has_digit):
            raise ValueError('Password must contain both letters and numbers')
        
        return v


class UserUpdate(BaseModel):
    """用户更新模型"""
    username: Optional[str] = Field(default=None, min_length=3, max_length=50)
    full_name: Optional[str] = Field(default=None, max_length=100)
    avatar_url: Optional[str] = Field(default=None)
    
    @field_validator("username")
    def validate_username(cls, v):
        if v is not None:
            import re
            if not re.match(r'^[a-zA-Z0-9_-]+$', v):
                raise ValueError('Username can only contain letters, numbers, underscores and hyphens')
        return v


class UserResponse(BaseModel):
    """用户响应模型"""
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
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    """用户登录模型"""
    username: str = Field(description="用户名或邮箱")
    password: str = Field(description="密码")


class Token(BaseModel):
    """令牌响应模型"""
    access_token: str = Field(description="访问令牌")
    refresh_token: str = Field(description="刷新令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: int = Field(description="过期时间（秒）")
    user: UserResponse = Field(description="用户信息")


class TokenRefresh(BaseModel):
    """令牌刷新模型"""
    refresh_token: str = Field(description="刷新令牌")


class PasswordChange(BaseModel):
    """密码修改模型"""
    current_password: str = Field(description="当前密码")
    new_password: str = Field(min_length=8, max_length=100, description="新密码")
    
    @field_validator("new_password")
    def validate_new_password(cls, v):
        # 密码强度验证
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        has_letter = any(c.isalpha() for c in v)
        has_digit = any(c.isdigit() for c in v)
        
        if not (has_letter and has_digit):
            raise ValueError('Password must contain both letters and numbers')
        
        return v


class PasswordReset(BaseModel):
    """密码重置模型"""
    email: EmailStr = Field(description="用户邮箱")


class PasswordResetConfirm(BaseModel):
    """密码重置确认模型"""
    token: str = Field(description="重置令牌")
    new_password: str = Field(min_length=8, max_length=100, description="新密码")
    
    @field_validator("new_password")
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        has_letter = any(c.isalpha() for c in v)
        has_digit = any(c.isdigit() for c in v)
        
        if not (has_letter and has_digit):
            raise ValueError('Password must contain both letters and numbers')
        
        return v


class EmailVerification(BaseModel):
    """邮箱验证模型"""
    token: str = Field(description="验证令牌")


class UserSession(BaseModel):
    """用户会话模型"""
    id: int
    device_info: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    is_active: bool
    expires_at: datetime
    last_activity_at: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True
