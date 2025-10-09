"""下载平台管理API端点

提供下载平台配置管理相关的API接口。
"""

from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.common import ResponseModel
from app.core.app_logging import download_logger

router = APIRouter()


# 下载平台数据模型（临时使用，后续会创建正式的模型）
class DownloadPlatform:
    """下载平台配置模型"""
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


@router.get("/platforms", response_model=ResponseModel[List[dict]])
def get_download_platforms(
    enabled_only: bool = Query(False, description="仅获取启用的平台"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """获取下载平台列表
    
    获取所有支持的下载平台配置信息。
    """
    try:
        # 查询下载平台配置
        query = "SELECT * FROM download_platforms"
        if enabled_only:
            query += " WHERE enabled = 1"
        query += " ORDER BY name"
        
        result = db.execute(query)
        platforms = []
        
        for row in result.fetchall():
            platform_data = {
                "id": row[0],
                "name": row[1],
                "display_name": row[2],
                "icon": row[3],
                "color": row[4],
                "enabled": bool(row[5]),
                "supported_features": eval(row[6]) if row[6] else [],
                "quality_options": eval(row[7]) if row[7] else [],
                "format_options": eval(row[8]) if row[8] else [],
                "api_endpoint": row[9],
                "rate_limit": row[10],
                "timeout": row[11],
                "config": eval(row[12]) if row[12] else {},
                "created_at": row[13],
                "updated_at": row[14]
            }
            platforms.append(platform_data)
        
        download_logger.info(
            "Download platforms retrieved",
            user_id=current_user.id,
            platform_count=len(platforms),
            enabled_only=enabled_only
        )
        
        return ResponseModel(
            code=200,
            message="Download platforms retrieved successfully",
            data=platforms
        )
        
    except Exception as e:
        download_logger.error(
            "Failed to retrieve download platforms",
            user_id=current_user.id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve download platforms"
        )


@router.get("/platforms/{platform_name}", response_model=ResponseModel[dict])
def get_download_platform(
    platform_name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """获取指定平台配置
    
    获取指定下载平台的详细配置信息。
    """
    try:
        query = "SELECT * FROM download_platforms WHERE name = ?"
        result = db.execute(query, (platform_name,))
        row = result.fetchone()
        
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Platform '{platform_name}' not found"
            )
        
        platform_data = {
            "id": row[0],
            "name": row[1],
            "display_name": row[2],
            "icon": row[3],
            "color": row[4],
            "enabled": bool(row[5]),
            "supported_features": eval(row[6]) if row[6] else [],
            "quality_options": eval(row[7]) if row[7] else [],
            "format_options": eval(row[8]) if row[8] else [],
            "api_endpoint": row[9],
            "rate_limit": row[10],
            "timeout": row[11],
            "config": eval(row[12]) if row[12] else {},
            "created_at": row[13],
            "updated_at": row[14]
        }
        
        download_logger.info(
            "Download platform retrieved",
            user_id=current_user.id,
            platform_name=platform_name
        )
        
        return ResponseModel(
            code=200,
            message="Download platform retrieved successfully",
            data=platform_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        download_logger.error(
            "Failed to retrieve download platform",
            user_id=current_user.id,
            platform_name=platform_name,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve download platform"
        )


@router.put("/platforms/{platform_name}/toggle", response_model=ResponseModel[dict])
def toggle_platform_status(
    platform_name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """切换平台启用状态
    
    启用或禁用指定的下载平台。
    """
    try:
        # 检查平台是否存在
        check_query = "SELECT enabled FROM download_platforms WHERE name = ?"
        result = db.execute(check_query, (platform_name,))
        row = result.fetchone()
        
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Platform '{platform_name}' not found"
            )
        
        current_status = bool(row[0])
        new_status = not current_status
        
        # 更新状态
        update_query = """
        UPDATE download_platforms 
        SET enabled = ?, updated_at = CURRENT_TIMESTAMP 
        WHERE name = ?
        """
        db.execute(update_query, (int(new_status), platform_name))
        db.commit()
        
        download_logger.info(
            "Platform status toggled",
            user_id=current_user.id,
            platform_name=platform_name,
            old_status=current_status,
            new_status=new_status
        )
        
        return ResponseModel(
            code=200,
            message=f"Platform '{platform_name}' {'enabled' if new_status else 'disabled'} successfully",
            data={
                "platform_name": platform_name,
                "enabled": new_status
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        download_logger.error(
            "Failed to toggle platform status",
            user_id=current_user.id,
            platform_name=platform_name,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to toggle platform status"
        )


@router.get("/platforms/{platform_name}/features", response_model=ResponseModel[dict])
def get_platform_features(
    platform_name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """获取平台支持的功能特性
    
    获取指定平台支持的下载功能和选项。
    """
    try:
        query = """
        SELECT supported_features, quality_options, format_options, rate_limit, timeout 
        FROM download_platforms 
        WHERE name = ? AND enabled = 1
        """
        result = db.execute(query, (platform_name,))
        row = result.fetchone()
        
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Enabled platform '{platform_name}' not found"
            )
        
        features_data = {
            "platform_name": platform_name,
            "supported_features": eval(row[0]) if row[0] else [],
            "quality_options": eval(row[1]) if row[1] else [],
            "format_options": eval(row[2]) if row[2] else [],
            "rate_limit": row[3],
            "timeout": row[4]
        }
        
        download_logger.info(
            "Platform features retrieved",
            user_id=current_user.id,
            platform_name=platform_name
        )
        
        return ResponseModel(
            code=200,
            message="Platform features retrieved successfully",
            data=features_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        download_logger.error(
            "Failed to retrieve platform features",
            user_id=current_user.id,
            platform_name=platform_name,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve platform features"
        )