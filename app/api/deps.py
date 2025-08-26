"""API依赖项

提供FastAPI路由的通用依赖项，如认证、数据库会话等。
"""

from typing import Generator, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import verify_token
from app.models.user import User

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    auto_error=False
)


def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """获取当前认证用户
    
    从JWT令牌中解析用户信息并返回用户对象。
    
    Args:
        token: JWT访问令牌
        db: 数据库会话
    
    Returns:
        当前用户对象
    
    Raises:
        HTTPException: 认证失败时抛出401错误
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not token:
        raise credentials_exception
    
    # 验证令牌
    payload = verify_token(token)
    if not payload:
        raise credentials_exception
    
    # 检查令牌类型
    if payload.get("type") != "access":
        raise credentials_exception
    
    # 获取用户ID
    user_id = payload.get("sub")
    if not user_id:
        raise credentials_exception
    
    # 查询用户
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise credentials_exception
    
    # 检查用户状态
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """获取当前活跃用户
    
    确保用户是活跃状态。
    
    Args:
        current_user: 当前用户
    
    Returns:
        活跃用户对象
    
    Raises:
        HTTPException: 用户不活跃时抛出400错误
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


def get_current_superuser(
    current_user: User = Depends(get_current_user)
) -> User:
    """获取当前超级用户
    
    确保用户具有超级用户权限。
    
    Args:
        current_user: 当前用户
    
    Returns:
        超级用户对象
    
    Raises:
        HTTPException: 用户不是超级用户时抛出403错误
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """获取当前用户（可选）
    
    如果提供了有效令牌则返回用户，否则返回None。
    用于可选认证的端点。
    
    Args:
        token: JWT访问令牌
        db: 数据库会话
    
    Returns:
        用户对象或None
    """
    if not token:
        return None
    
    try:
        return get_current_user(token, db)
    except HTTPException:
        return None


def check_user_permission(
    required_role: str = "user"
):
    """检查用户权限装饰器工厂
    
    创建一个依赖项来检查用户是否具有指定角色。
    
    Args:
        required_role: 所需的用户角色
    
    Returns:
        依赖项函数
    """
    def permission_checker(
        current_user: User = Depends(get_current_user)
    ) -> User:
        role_hierarchy = {
            "user": 1,
            "premium": 2,
            "admin": 3,
            "superuser": 4
        }
        
        user_level = role_hierarchy.get(current_user.role, 0)
        required_level = role_hierarchy.get(required_role, 0)
        
        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {required_role}"
            )
        
        return current_user
    
    return permission_checker


# 常用权限检查器
require_admin = check_user_permission("admin")
require_premium = check_user_permission("premium")