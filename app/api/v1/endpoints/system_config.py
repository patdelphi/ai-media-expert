"""系统配置API端点

提供系统配置管理相关的API接口。
"""

from typing import Any, List, Optional
import json
import yaml

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.api.deps import get_current_user, get_db
from app.core.security import encrypt_value, decrypt_value
from app.models.user import User
from app.models.system_config import SystemConfig
from app.schemas.system_config import (
    SystemConfigCreate,
    SystemConfigUpdate,
    SystemConfigResponse,
    SystemConfigPublicResponse,
    SystemConfigBatchUpdate,
    SystemConfigCategory,
    SystemConfigExport,
    SystemConfigImport
)
from app.schemas.common import ResponseModel
from app.core.logging import api_logger

router = APIRouter()


@router.get("/", response_model=ResponseModel[List[SystemConfigResponse]])
def get_system_configs(
    category: Optional[str] = Query(None, description="配置分类筛选"),
    is_public: Optional[bool] = Query(None, description="是否只获取公开配置"),
    include_inactive: bool = Query(False, description="是否包含未激活的配置"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """获取系统配置列表
    
    需要管理员权限才能获取完整配置信息。
    """
    # 检查权限
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can access system configurations"
        )
    
    query = db.query(SystemConfig)
    
    # 应用筛选条件
    if category:
        query = query.filter(SystemConfig.category == category)
    
    if is_public is not None:
        query = query.filter(SystemConfig.is_public == is_public)
    
    if not include_inactive:
        query = query.filter(SystemConfig.is_active == True)
    
    configs = query.order_by(SystemConfig.category, SystemConfig.key).all()
    
    api_logger.info(
        "System configs retrieved",
        user_id=current_user.id,
        count=len(configs),
        category=category
    )
    
    return ResponseModel(
        code=200,
        message="System configurations retrieved successfully",
        data=configs
    )


@router.get("/public", response_model=ResponseModel[List[SystemConfigPublicResponse]])
def get_public_configs(
    category: Optional[str] = Query(None, description="配置分类筛选"),
    db: Session = Depends(get_db)
) -> Any:
    """获取公开系统配置
    
    不需要认证，只返回标记为公开的配置。
    """
    query = db.query(SystemConfig).filter(
        SystemConfig.is_public == True,
        SystemConfig.is_active == True
    )
    
    if category:
        query = query.filter(SystemConfig.category == category)
    
    configs = query.order_by(SystemConfig.category, SystemConfig.key).all()
    
    return ResponseModel(
        code=200,
        message="Public configurations retrieved successfully",
        data=configs
    )


@router.get("/categories", response_model=ResponseModel[List[SystemConfigCategory]])
def get_config_categories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """获取配置分类列表"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can access system configurations"
        )
    
    # 查询分类统计
    result = db.query(
        SystemConfig.category,
        func.count(SystemConfig.id).label('count')
    ).filter(
        SystemConfig.is_active == True
    ).group_by(SystemConfig.category).all()
    
    categories = [
        SystemConfigCategory(
            category=row.category,
            count=row.count
        )
        for row in result
    ]
    
    return ResponseModel(
        code=200,
        message="Configuration categories retrieved successfully",
        data=categories
    )


@router.get("/{key}", response_model=ResponseModel[SystemConfigResponse])
def get_system_config(
    key: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """获取单个系统配置"""
    config = SystemConfig.get_by_key(db, key)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration not found"
        )
    
    # 检查权限
    if not config.is_public and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this configuration"
        )
    
    return ResponseModel(
        code=200,
        message="Configuration retrieved successfully",
        data=config
    )


@router.post("/", response_model=ResponseModel[SystemConfigResponse])
def create_system_config(
    config_data: SystemConfigCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """创建系统配置"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create system configurations"
        )
    
    # 检查配置键是否已存在
    existing = SystemConfig.get_by_key(db, config_data.key)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Configuration key already exists"
        )
    
    # 创建配置
    config_dict = config_data.dict()
    
    # 如果需要加密，加密值
    if config_data.is_encrypted:
        config_dict["value"] = encrypt_value(config_data.value)
    
    db_config = SystemConfig(**config_dict)
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    
    api_logger.info(
        "System config created",
        user_id=current_user.id,
        config_key=db_config.key,
        category=db_config.category
    )
    
    return ResponseModel(
        code=200,
        message="Configuration created successfully",
        data=db_config
    )


@router.put("/{key}", response_model=ResponseModel[SystemConfigResponse])
def update_system_config(
    key: str,
    config_update: SystemConfigUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """更新系统配置"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can update system configurations"
        )
    
    config = SystemConfig.get_by_key(db, key)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration not found"
        )
    
    # 更新字段
    update_data = config_update.dict(exclude_unset=True)
    
    # 如果更新值且配置是加密的，需要加密新值
    if "value" in update_data and config.is_encrypted:
        update_data["value"] = encrypt_value(update_data["value"])
    
    for field, value in update_data.items():
        setattr(config, field, value)
    
    db.commit()
    db.refresh(config)
    
    api_logger.info(
        "System config updated",
        user_id=current_user.id,
        config_key=config.key,
        updated_fields=list(update_data.keys())
    )
    
    return ResponseModel(
        code=200,
        message="Configuration updated successfully",
        data=config
    )


@router.delete("/{key}")
def delete_system_config(
    key: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """删除系统配置"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete system configurations"
        )
    
    config = SystemConfig.get_by_key(db, key)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration not found"
        )
    
    db.delete(config)
    db.commit()
    
    api_logger.info(
        "System config deleted",
        user_id=current_user.id,
        config_key=key
    )
    
    return ResponseModel(
        code=200,
        message="Configuration deleted successfully",
        data=None
    )


@router.post("/batch-update")
def batch_update_configs(
    batch_data: SystemConfigBatchUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """批量更新系统配置"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can batch update system configurations"
        )
    
    updated_configs = []
    errors = []
    
    for key, value in batch_data.configs.items():
        try:
            config = SystemConfig.get_by_key(db, key)
            if not config:
                errors.append(f"Configuration '{key}' not found")
                continue
            
            # 如果指定了分类，检查配置是否属于该分类
            if batch_data.category and config.category != batch_data.category:
                errors.append(f"Configuration '{key}' does not belong to category '{batch_data.category}'")
                continue
            
            # 更新值
            if config.is_encrypted:
                config.value = encrypt_value(value)
            else:
                config.value = value
            
            updated_configs.append(key)
            
        except Exception as e:
            errors.append(f"Error updating '{key}': {str(e)}")
    
    if updated_configs:
        db.commit()
    
    api_logger.info(
        "Batch config update",
        user_id=current_user.id,
        updated_count=len(updated_configs),
        error_count=len(errors)
    )
    
    return ResponseModel(
        code=200,
        message=f"Batch update completed. Updated: {len(updated_configs)}, Errors: {len(errors)}",
        data={
            "updated": updated_configs,
            "errors": errors
        }
    )


@router.post("/export")
def export_configs(
    export_data: SystemConfigExport,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """导出系统配置"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can export system configurations"
        )
    
    query = db.query(SystemConfig).filter(SystemConfig.is_active == True)
    
    # 筛选分类
    if export_data.categories:
        query = query.filter(SystemConfig.category.in_(export_data.categories))
    
    # 是否包含加密配置
    if not export_data.include_encrypted:
        query = query.filter(SystemConfig.is_encrypted == False)
    
    configs = query.order_by(SystemConfig.category, SystemConfig.key).all()
    
    # 构建导出数据
    export_dict = {}
    for config in configs:
        value = config.value
        if config.is_encrypted and export_data.include_encrypted:
            try:
                value = decrypt_value(config.value)
            except Exception:
                value = "[ENCRYPTED]"
        
        export_dict[config.key] = {
            "value": value,
            "description": config.description,
            "category": config.category,
            "data_type": config.data_type
        }
    
    # 根据格式转换
    if export_data.format == "json":
        result = json.dumps(export_dict, indent=2, ensure_ascii=False)
    elif export_data.format == "yaml":
        result = yaml.dump(export_dict, default_flow_style=False, allow_unicode=True)
    elif export_data.format == "env":
        result = "\n".join([f"{k}={v['value']}" for k, v in export_dict.items()])
    else:
        result = str(export_dict)
    
    api_logger.info(
        "Configs exported",
        user_id=current_user.id,
        format=export_data.format,
        count=len(configs)
    )
    
    return ResponseModel(
        code=200,
        message="Configurations exported successfully",
        data={
            "format": export_data.format,
            "count": len(configs),
            "data": result
        }
    )