"""下载统计API端点

提供下载数据统计和分析相关的API接口。
"""

from typing import Any, List, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.common import ResponseModel
from app.core.app_logging import download_logger

router = APIRouter()


@router.get("/statistics/overview", response_model=ResponseModel[dict])
def get_download_overview(
    days: int = Query(30, description="统计天数", ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """获取下载统计概览
    
    获取用户指定时间范围内的下载统计概览数据。
    """
    try:
        # 计算时间范围
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        # 查询用户下载任务统计
        task_stats_query = """
        SELECT 
            COUNT(*) as total_tasks,
            SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_tasks,
            SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_tasks,
            SUM(CASE WHEN status IN ('pending', 'analyzing', 'downloading') THEN 1 ELSE 0 END) as active_tasks
        FROM download_tasks 
        WHERE user_id = ? AND DATE(created_at) BETWEEN ? AND ?
        """
        
        result = db.execute(task_stats_query, (current_user.id, start_date, end_date))
        task_row = result.fetchone()
        
        # 查询平台统计
        platform_stats_query = """
        SELECT 
            platform,
            COUNT(*) as task_count,
            SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as success_count
        FROM download_tasks 
        WHERE user_id = ? AND DATE(created_at) BETWEEN ? AND ?
        GROUP BY platform
        ORDER BY task_count DESC
        """
        
        result = db.execute(platform_stats_query, (current_user.id, start_date, end_date))
        platform_rows = result.fetchall()
        
        # 查询每日统计
        daily_stats_query = """
        SELECT 
            DATE(created_at) as date,
            COUNT(*) as total_downloads,
            SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as successful_downloads
        FROM download_tasks 
        WHERE user_id = ? AND DATE(created_at) BETWEEN ? AND ?
        GROUP BY DATE(created_at)
        ORDER BY date DESC
        LIMIT 7
        """
        
        result = db.execute(daily_stats_query, (current_user.id, start_date, end_date))
        daily_rows = result.fetchall()
        
        # 构建响应数据
        overview_data = {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days
            },
            "summary": {
                "total_tasks": task_row[0] if task_row else 0,
                "completed_tasks": task_row[1] if task_row else 0,
                "failed_tasks": task_row[2] if task_row else 0,
                "active_tasks": task_row[3] if task_row else 0,
                "success_rate": round((task_row[1] / task_row[0] * 100) if task_row and task_row[0] > 0 else 0, 2)
            },
            "platform_stats": [
                {
                    "platform": row[0],
                    "task_count": row[1],
                    "success_count": row[2],
                    "success_rate": round((row[2] / row[1] * 100) if row[1] > 0 else 0, 2)
                }
                for row in platform_rows
            ],
            "daily_stats": [
                {
                    "date": row[0].isoformat() if hasattr(row[0], 'isoformat') else str(row[0]),
                    "total_downloads": row[1],
                    "successful_downloads": row[2],
                    "success_rate": round((row[2] / row[1] * 100) if row[1] > 0 else 0, 2)
                }
                for row in daily_rows
            ]
        }
        
        download_logger.info(
            "Download overview retrieved",
            user_id=current_user.id,
            days=days,
            total_tasks=overview_data["summary"]["total_tasks"]
        )
        
        return ResponseModel(
            code=200,
            message="Download overview retrieved successfully",
            data=overview_data
        )
        
    except Exception as e:
        download_logger.error(
            "Failed to retrieve download overview",
            user_id=current_user.id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve download overview"
        )


@router.get("/statistics/platforms", response_model=ResponseModel[List[dict]])
def get_platform_statistics(
    days: int = Query(30, description="统计天数", ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """获取平台下载统计
    
    获取各平台的详细下载统计数据。
    """
    try:
        # 计算时间范围
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        # 查询平台详细统计
        platform_query = """
        SELECT 
            dt.platform,
            dp.display_name,
            dp.icon,
            dp.color,
            COUNT(*) as total_downloads,
            SUM(CASE WHEN dt.status = 'completed' THEN 1 ELSE 0 END) as successful_downloads,
            SUM(CASE WHEN dt.status = 'failed' THEN 1 ELSE 0 END) as failed_downloads,
            AVG(CASE WHEN dt.status = 'completed' AND dt.file_size > 0 THEN dt.file_size ELSE NULL END) as avg_file_size,
            SUM(CASE WHEN dt.status = 'completed' THEN dt.file_size ELSE 0 END) as total_size
        FROM download_tasks dt
        LEFT JOIN download_platforms dp ON dt.platform = dp.name
        WHERE dt.user_id = ? AND DATE(dt.created_at) BETWEEN ? AND ?
        GROUP BY dt.platform, dp.display_name, dp.icon, dp.color
        ORDER BY total_downloads DESC
        """
        
        result = db.execute(platform_query, (current_user.id, start_date, end_date))
        platform_rows = result.fetchall()
        
        platform_stats = []
        for row in platform_rows:
            platform_data = {
                "platform": row[0],
                "display_name": row[1] or row[0],
                "icon": row[2],
                "color": row[3],
                "total_downloads": row[4],
                "successful_downloads": row[5],
                "failed_downloads": row[6],
                "success_rate": round((row[5] / row[4] * 100) if row[4] > 0 else 0, 2),
                "avg_file_size": int(row[7]) if row[7] else 0,
                "total_size": row[8] or 0,
                "total_size_mb": round((row[8] or 0) / (1024 * 1024), 2)
            }
            platform_stats.append(platform_data)
        
        download_logger.info(
            "Platform statistics retrieved",
            user_id=current_user.id,
            days=days,
            platform_count=len(platform_stats)
        )
        
        return ResponseModel(
            code=200,
            message="Platform statistics retrieved successfully",
            data=platform_stats
        )
        
    except Exception as e:
        download_logger.error(
            "Failed to retrieve platform statistics",
            user_id=current_user.id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve platform statistics"
        )


@router.get("/statistics/trends", response_model=ResponseModel[dict])
def get_download_trends(
    days: int = Query(30, description="统计天数", ge=7, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """获取下载趋势数据
    
    获取指定时间范围内的下载趋势分析数据。
    """
    try:
        # 计算时间范围
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        # 查询每日趋势数据
        daily_trend_query = """
        SELECT 
            DATE(created_at) as date,
            COUNT(*) as total_downloads,
            SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as successful_downloads,
            SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_downloads,
            SUM(CASE WHEN status = 'completed' THEN file_size ELSE 0 END) as total_size
        FROM download_tasks 
        WHERE user_id = ? AND DATE(created_at) BETWEEN ? AND ?
        GROUP BY DATE(created_at)
        ORDER BY date ASC
        """
        
        result = db.execute(daily_trend_query, (current_user.id, start_date, end_date))
        daily_rows = result.fetchall()
        
        # 查询小时分布（最近7天）
        recent_start = end_date - timedelta(days=7)
        hourly_query = """
        SELECT 
            CAST(strftime('%H', created_at) AS INTEGER) as hour,
            COUNT(*) as download_count
        FROM download_tasks 
        WHERE user_id = ? AND DATE(created_at) BETWEEN ? AND ?
        GROUP BY CAST(strftime('%H', created_at) AS INTEGER)
        ORDER BY hour ASC
        """
        
        result = db.execute(hourly_query, (current_user.id, recent_start, end_date))
        hourly_rows = result.fetchall()
        
        # 构建趋势数据
        trends_data = {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days
            },
            "daily_trends": [
                {
                    "date": row[0].isoformat() if hasattr(row[0], 'isoformat') else str(row[0]),
                    "total_downloads": row[1],
                    "successful_downloads": row[2],
                    "failed_downloads": row[3],
                    "success_rate": round((row[2] / row[1] * 100) if row[1] > 0 else 0, 2),
                    "total_size_mb": round((row[4] or 0) / (1024 * 1024), 2)
                }
                for row in daily_rows
            ],
            "hourly_distribution": [
                {
                    "hour": row[0],
                    "download_count": row[1]
                }
                for row in hourly_rows
            ]
        }
        
        download_logger.info(
            "Download trends retrieved",
            user_id=current_user.id,
            days=days,
            daily_points=len(trends_data["daily_trends"])
        )
        
        return ResponseModel(
            code=200,
            message="Download trends retrieved successfully",
            data=trends_data
        )
        
    except Exception as e:
        download_logger.error(
            "Failed to retrieve download trends",
            user_id=current_user.id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve download trends"
        )