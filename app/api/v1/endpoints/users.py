"""用户管理API端点

提供用户信息管理相关的API接口。
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.security import get_password_hash, verify_password
from app.models.user import User
from app.schemas.auth import PasswordChange, UserResponse, UserUpdate
from app.schemas.common import ResponseModel
from app.core.logging import api_logger

router = APIRouter()


@router.get("/profile", response_model=ResponseModel[UserResponse])
def get_user_profile(
    current_user: User = Depends(get_current_user)
) -> Any:
    """获取用户个人资料
    
    返回当前登录用户的详细信息。
    """
    return ResponseModel(
        code=200,
        message="User profile retrieved successfully",
        data=UserResponse.from_attributes(current_user)
    )


@router.put("/profile", response_model=ResponseModel[UserResponse])
def update_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """更新用户个人资料
    
    更新当前用户的个人信息。
    """
    # 检查用户名是否已被其他用户使用
    if user_update.username and user_update.username != current_user.username:
        existing_user = db.query(User).filter(
            User.username == user_update.username,
            User.id != current_user.id
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
    
    # 更新用户信息
    update_data = user_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(current_user, field, value)
    
    db.commit()
    db.refresh(current_user)
    
    api_logger.info(
        "User profile updated",
        user_id=current_user.id,
        updated_fields=list(update_data.keys())
    )
    
    return ResponseModel(
        code=200,
        message="User profile updated successfully",
        data=UserResponse.from_attributes(current_user)
    )


@router.post("/change-password", response_model=ResponseModel[dict])
def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """修改用户密码
    
    验证当前密码后更新为新密码。
    """
    # 验证当前密码
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # 检查新密码是否与当前密码相同
    if verify_password(password_data.new_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password"
        )
    
    # 更新密码
    current_user.hashed_password = get_password_hash(password_data.new_password)
    db.commit()
    
    api_logger.info(
        "User password changed",
        user_id=current_user.id
    )
    
    return ResponseModel(
        code=200,
        message="Password changed successfully",
        data={"message": "Password has been updated"}
    )


@router.delete("/account", response_model=ResponseModel[dict])
def delete_user_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """删除用户账户
    
    软删除用户账户（设置为非活跃状态）。
    """
    # 软删除：设置用户为非活跃状态
    current_user.is_active = False
    db.commit()
    
    api_logger.info(
        "User account deleted",
        user_id=current_user.id,
        email=current_user.email
    )
    
    return ResponseModel(
        code=200,
        message="Account deleted successfully",
        data={"message": "Your account has been deactivated"}
    )