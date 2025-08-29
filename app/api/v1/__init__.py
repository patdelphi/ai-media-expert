"""API v1版本

第一版API接口定义。
"""

from fastapi import APIRouter
from .endpoints import auth, users, system_config
from .upload import router as upload_router
from .videos import router as videos_router
from .analysis import router as analysis_router
from .ai_config import router as ai_config_router

api_router = APIRouter()

# 认证相关路由
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(users.router, prefix="/users", tags=["用户管理"])
api_router.include_router(system_config.router, prefix="/system/config", tags=["系统配置"])

# 其他功能路由
api_router.include_router(upload_router, prefix="/upload", tags=["upload"])
api_router.include_router(videos_router, prefix="/videos", tags=["videos"])
api_router.include_router(analysis_router, prefix="/analysis", tags=["analysis"])
api_router.include_router(ai_config_router, prefix="/ai-config", tags=["ai-config"])