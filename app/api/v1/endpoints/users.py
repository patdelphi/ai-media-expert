"""用户管理API端点

提供用户信息管理相关的API接口。
"""

from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from app.api.deps import get_current_user, get_db, require_admin
from app.core.security import get_password_hash, verify_password
from app.models.user import User
from app.schemas.auth import PasswordChange, UserResponse, UserUpdate
from app.schemas.user import (
    AdminUserCreate, AdminUserUpdate, UserListResponse, UserListItem,
    UserStatusUpdate, UserSearchParams
)
from app.schemas.common import ResponseModel, PaginationParams
from app.core.app_logging import api_logger

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
        data=UserResponse.model_validate(current_user)
    )


@router.get("/me", response_model=ResponseModel[UserResponse])
def get_user_me(
    current_user: User = Depends(get_current_user)
) -> Any:
    return ResponseModel(
        code=200,
        message="User profile retrieved successfully",
        data=UserResponse.model_validate(current_user)
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
        data=UserResponse.model_validate(current_user)
    )


@router.put("/me", response_model=ResponseModel[UserResponse])
def update_user_me(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    return update_user_profile(user_update=user_update, current_user=current_user, db=db)


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


@router.put("/me/password", response_model=ResponseModel[dict])
def change_password_me(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    return change_password(password_data=password_data, current_user=current_user, db=db)


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


# 管理员用户管理接口

@router.get("/list", response_model=ResponseModel[UserListResponse])
def get_users_list(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    role: Optional[str] = Query(None, description="角色筛选"),
    is_active: Optional[bool] = Query(None, description="状态筛选"),
    is_verified: Optional[bool] = Query(None, description="验证状态筛选"),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
) -> Any:
    """获取用户列表（管理员）
    
    管理员获取系统中所有用户的列表，支持分页、搜索和筛选。
    """
    # 构建查询
    query = db.query(User)
    
    # 搜索条件
    if search:
        search_filter = or_(
            User.username.ilike(f"%{search}%"),
            User.email.ilike(f"%{search}%"),
            User.full_name.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)
    
    # 角色筛选
    if role:
        query = query.filter(User.role == role)
    
    # 状态筛选
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    
    # 验证状态筛选
    if is_verified is not None:
        query = query.filter(User.is_verified == is_verified)
    
    # 总数统计
    total = query.count()
    
    # 分页
    offset = (page - 1) * size
    users = query.offset(offset).limit(size).all()
    
    # 转换为响应模型
    user_items = [UserListItem.model_validate(user) for user in users]
    
    api_logger.info(
        "Users list retrieved",
        admin_user_id=current_user.id,
        total_users=total,
        page=page,
        size=size
    )
    
    return ResponseModel(
        code=200,
        message="Users list retrieved successfully",
        data=UserListResponse(
            items=user_items,
            total=total,
            page=page,
            size=size,
            pages=(total + size - 1) // size
        )
    )


@router.post("/create", response_model=ResponseModel[UserResponse])
def create_user(
    user_data: AdminUserCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
) -> Any:
    """创建用户（管理员）
    
    管理员创建新用户，邮箱和密码可以为空。
    """
    # 检查邮箱是否已存在（如果提供了邮箱）
    if user_data.email:
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    # 检查用户名是否已存在（如果提供了用户名）
    if user_data.username:
        existing_user = db.query(User).filter(User.username == user_data.username).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
    
    # 如果没有提供邮箱，生成一个临时邮箱
    email = user_data.email or f"temp_{db.query(User).count() + 1}@temp.local"
    
    # 创建用户
    user_dict = user_data.dict(exclude_unset=True)
    user_dict["email"] = email
    
    # 处理密码
    if user_data.password:
        user_dict["hashed_password"] = get_password_hash(user_data.password)
    else:
        # 如果没有提供密码，生成一个随机密码哈希
        import secrets
        temp_password = secrets.token_urlsafe(16)
        user_dict["hashed_password"] = get_password_hash(temp_password)
    
    # 移除原始密码字段
    user_dict.pop("password", None)
    
    # 创建用户对象
    new_user = User(**user_dict)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    api_logger.info(
        "User created by admin",
        admin_user_id=current_user.id,
        new_user_id=new_user.id,
        new_user_email=new_user.email
    )
    
    return ResponseModel(
        code=200,
        message="User created successfully",
        data=UserResponse.model_validate(new_user)
    )


@router.get("/{user_id}", response_model=ResponseModel[UserResponse])
def get_user_by_id(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
) -> Any:
    """获取用户详情（管理员）
    
    管理员根据用户ID获取用户详细信息。
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return ResponseModel(
        code=200,
        message="User retrieved successfully",
        data=UserResponse.model_validate(user)
    )


@router.put("/{user_id}", response_model=ResponseModel[UserResponse])
def update_user(
    user_id: int,
    user_update: AdminUserUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
) -> Any:
    """更新用户信息（管理员）
    
    管理员更新指定用户的信息。
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # 检查邮箱是否已被其他用户使用
    if user_update.email and user_update.email != user.email:
        existing_user = db.query(User).filter(
            User.email == user_update.email,
            User.id != user_id
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    # 检查用户名是否已被其他用户使用
    if user_update.username and user_update.username != user.username:
        existing_user = db.query(User).filter(
            User.username == user_update.username,
            User.id != user_id
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
    
    # 更新用户信息
    update_data = user_update.dict(exclude_unset=True)
    if "password" in update_data and update_data["password"]:
        user.hashed_password = get_password_hash(update_data.pop("password"))
    for field, value in update_data.items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    
    api_logger.info(
        "User updated by admin",
        admin_user_id=current_user.id,
        updated_user_id=user.id,
        updated_fields=list(update_data.keys())
    )
    
    return ResponseModel(
        code=200,
        message="User updated successfully",
        data=UserResponse.model_validate(user)
    )


@router.put("/{user_id}/status", response_model=ResponseModel[UserResponse])
def update_user_status(
    user_id: int,
    status_update: UserStatusUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
) -> Any:
    """更新用户状态（管理员）
    
    管理员启用或禁用用户账户。
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # 防止管理员禁用自己的账户
    if user_id == current_user.id and not status_update.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account"
        )
    
    user.is_active = status_update.is_active
    db.commit()
    db.refresh(user)
    
    api_logger.info(
        "User status updated by admin",
        admin_user_id=current_user.id,
        updated_user_id=user.id,
        new_status=status_update.is_active,
        reason=status_update.reason
    )
    
    return ResponseModel(
        code=200,
        message=f"User {'activated' if status_update.is_active else 'deactivated'} successfully",
        data=UserResponse.model_validate(user)
    )


@router.delete("/{user_id}", response_model=ResponseModel[dict])
def delete_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
) -> Any:
    """删除用户（管理员）
    
    管理员软删除用户账户（设置为非活跃状态）。
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # 防止管理员删除自己的账户
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    # 软删除：设置为非活跃状态
    user.is_active = False
    db.commit()
    
    api_logger.info(
        "User deleted by admin",
        admin_user_id=current_user.id,
        deleted_user_id=user.id,
        deleted_user_email=user.email
    )
    
    return ResponseModel(
        code=200,
        message="User deleted successfully",
        data={"message": "User has been deactivated"}
    )
