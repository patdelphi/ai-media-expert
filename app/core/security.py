"""安全和认证工具模块

提供密码哈希、JWT令牌生成和验证等安全功能。
"""

from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(
    subject: Union[str, Any], 
    expires_delta: Optional[timedelta] = None
) -> str:
    """创建访问令牌
    
    Args:
        subject: 令牌主体（通常是用户ID）
        expires_delta: 过期时间增量
    
    Returns:
        JWT访问令牌字符串
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.jwt_access_token_expire_minutes
        )
    
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "access"
    }
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.jwt_secret_key, 
        algorithm=settings.jwt_algorithm
    )
    
    return encoded_jwt


def create_refresh_token(
    subject: Union[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """创建刷新令牌
    
    Args:
        subject: 令牌主体（通常是用户ID）
        expires_delta: 过期时间增量
    
    Returns:
        JWT刷新令牌字符串
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            days=settings.jwt_refresh_token_expire_days
        )
    
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "refresh"
    }
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )
    
    return encoded_jwt


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """验证JWT令牌
    
    Args:
        token: JWT令牌字符串
    
    Returns:
        令牌载荷字典，如果验证失败返回None
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        return payload
    except JWTError:
        return None


def get_password_hash(password: str) -> str:
    """生成密码哈希
    
    Args:
        password: 明文密码
    
    Returns:
        密码哈希字符串
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码
    
    Args:
        plain_password: 明文密码
        hashed_password: 哈希密码
    
    Returns:
        密码是否匹配
    """
    return pwd_context.verify(plain_password, hashed_password)


def generate_password_reset_token(email: str) -> str:
    """生成密码重置令牌
    
    Args:
        email: 用户邮箱
    
    Returns:
        密码重置令牌
    """
    delta = timedelta(hours=1)  # 1小时有效期
    now = datetime.utcnow()
    expires = now + delta
    
    exp = expires.timestamp()
    encoded_jwt = jwt.encode(
        {"exp": exp, "nbf": now, "sub": email, "type": "password_reset"},
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    
    return encoded_jwt


def verify_password_reset_token(token: str) -> Optional[str]:
    """验证密码重置令牌
    
    Args:
        token: 密码重置令牌
    
    Returns:
        用户邮箱，如果验证失败返回None
    """
    try:
        decoded_token = jwt.decode(
            token, 
            settings.jwt_secret_key, 
            algorithms=[settings.jwt_algorithm]
        )
        
        # 检查令牌类型
        if decoded_token.get("type") != "password_reset":
            return None
            
        return decoded_token["sub"]
    except JWTError:
        return None


def generate_email_verification_token(email: str) -> str:
    """生成邮箱验证令牌
    
    Args:
        email: 用户邮箱
    
    Returns:
        邮箱验证令牌
    """
    delta = timedelta(hours=24)  # 24小时有效期
    now = datetime.utcnow()
    expires = now + delta
    
    exp = expires.timestamp()
    encoded_jwt = jwt.encode(
        {"exp": exp, "nbf": now, "sub": email, "type": "email_verification"},
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    
    return encoded_jwt


def verify_email_verification_token(token: str) -> Optional[str]:
    """验证邮箱验证令牌
    
    Args:
        token: 邮箱验证令牌
    
    Returns:
        用户邮箱，如果验证失败返回None
    """
    try:
        decoded_token = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        
        # 检查令牌类型
        if decoded_token.get("type") != "email_verification":
            return None
            
        return decoded_token["sub"]
    except JWTError:
        return None