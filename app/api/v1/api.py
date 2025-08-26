"""API v1 路由汇总

汇总所有v1版本的API路由。
"""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, users, videos, download, analysis

# 创建API路由器
api_router = APIRouter()

# 包含各个模块的路由
api_router.include_router(
    auth.router, 
    prefix="/auth", 
    tags=["认证"]
)

api_router.include_router(
    users.router, 
    prefix="/users", 
    tags=["用户管理"]
)

api_router.include_router(
    videos.router, 
    prefix="/videos", 
    tags=["视频管理"]
)

api_router.include_router(
    download.router, 
    prefix="/download", 
    tags=["视频下载"]
)

api_router.include_router(
    analysis.router, 
    prefix="/analysis", 
    tags=["视频分析"]
)