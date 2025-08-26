"""认证相关API端点

提供用户登录、注册、令牌刷新等认证功能。
"""

from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
    verify_token
)
from app.models.user import User
from app.schemas.auth import (
    Token,
    TokenRefresh,
    UserCreate,
    UserLogin,
    UserResponse
)
from app.schemas.common import ResponseModel
from app.core.logging import security_logger

router = APIRouter()


@router.post("/register", response_model=ResponseModel[UserResponse])
def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
) -> Any:
    """用户注册
    
    创建新用户账户。
    """
    # 检查邮箱是否已存在
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # 检查用户名是否已存在（如果提供了用户名）
    if user_data.username:
        existing_username = db.query(User).filter(User.username == user_data.username).first()
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
    
    # 创建新用户
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        email=user_data.email,
        username=user_data.username,
        full_name=user_data.full_name,
        hashed_password=hashed_password,
        is_active=True,
        is_verified=False,  # 需要邮箱验证
        role="user"
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    security_logger.info(
        "User registered",
        user_id=db_user.id,
        email=db_user.email,
        username=db_user.username
    )
    
    return ResponseModel(
        code=200,
        message="User registered successfully",
        data=UserResponse.from_orm(db_user)
    )


@router.post("/login", response_model=ResponseModel[Token])
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
) -> Any:
    """用户登录
    
    使用邮箱/用户名和密码登录，返回访问令牌。
    """
    # 查找用户（支持邮箱或用户名登录）
    user = db.query(User).filter(
        (User.email == form_data.username) | 
        (User.username == form_data.username)
    ).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        security_logger.warning(
            "Failed login attempt",
            username=form_data.username
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email/username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # 更新最后登录时间
    user.last_login_at = datetime.utcnow()
    db.commit()
    
    # 创建访问令牌和刷新令牌
    access_token = create_access_token(subject=user.id)
    refresh_token = create_refresh_token(subject=user.id)
    
    security_logger.info(
        "User logged in",
        user_id=user.id,
        email=user.email
    )
    
    return ResponseModel(
        code=200,
        message="Login successful",
        data=Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=1800,  # 30分钟
            user=UserResponse.from_orm(user)
        )
    )


@router.post("/refresh", response_model=ResponseModel[Token])
def refresh_token(
    token_data: TokenRefresh,
    db: Session = Depends(get_db)
) -> Any:
    """刷新访问令牌
    
    使用刷新令牌获取新的访问令牌。
    """
    # 验证刷新令牌
    payload = verify_token(token_data.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # 查找用户
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # 创建新的访问令牌
    access_token = create_access_token(subject=user.id)
    
    security_logger.info(
        "Token refreshed",
        user_id=user.id
    )
    
    return ResponseModel(
        code=200,
        message="Token refreshed successfully",
        data=Token(
            access_token=access_token,
            refresh_token=token_data.refresh_token,  # 保持原刷新令牌
            token_type="bearer",
            expires_in=1800,
            user=UserResponse.from_orm(user)
        )
    )


@router.post("/logout", response_model=ResponseModel[dict])
def logout(
    current_user: User = Depends(get_current_user)
) -> Any:
    """用户登出
    
    登出当前用户（客户端应删除令牌）。
    """
    security_logger.info(
        "User logged out",
        user_id=current_user.id
    )
    
    return ResponseModel(
        code=200,
        message="Logout successful",
        data={"message": "Please delete the token on client side"}
    )


@router.get("/me", response_model=ResponseModel[UserResponse])
def get_current_user_info(
    current_user: User = Depends(get_current_user)
) -> Any:
    """获取当前用户信息
    
    返回当前登录用户的详细信息。
    """
    return ResponseModel(
        code=200,
        message="User info retrieved successfully",
        data=UserResponse.from_orm(current_user)
    )