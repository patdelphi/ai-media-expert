"""API v1版本

第一版API接口定义。
"""

from fastapi import APIRouter
from .upload import router as upload_router
from .videos import router as videos_router
from .analysis import router as analysis_router
from .ai_config import router as ai_config_router

api_router = APIRouter()
api_router.include_router(upload_router, prefix="/upload", tags=["upload"])
api_router.include_router(videos_router, prefix="/videos", tags=["videos"])
api_router.include_router(analysis_router, prefix="/analysis", tags=["analysis"])
api_router.include_router(ai_config_router, prefix="/ai-config", tags=["ai-config"])