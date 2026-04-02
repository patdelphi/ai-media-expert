"""API v1 路由汇总

汇总所有v1版本的API路由。
"""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    users,
    system_config,
    tag_groups,
    video_upload,
    video_processing,
    simple_upload,
    file_manager,
    video_analysis,
    video_download,
    websocket,
    download_platforms,
    download_statistics,
    download_queue,
)
from app.api.v1.ai_config import router as ai_config_router
from app.api.v1.prompt_template import router as prompt_template_router

# 创建API路由器
api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(users.router, prefix="/users", tags=["用户管理"])
api_router.include_router(system_config.router, prefix="/system/config", tags=["系统配置"])
api_router.include_router(tag_groups.router, prefix="/tag-groups", tags=["标签组管理"])
api_router.include_router(video_upload.router, prefix="/upload", tags=["视频上传"])
api_router.include_router(simple_upload.router, prefix="/simple-upload", tags=["简单上传"])
api_router.include_router(file_manager.router, prefix="/files", tags=["文件管理"])
api_router.include_router(video_processing.router, prefix="/processing", tags=["视频处理"])
api_router.include_router(video_analysis.router, prefix="/video-analysis", tags=["视频解析"])
api_router.include_router(video_download.router, prefix="/video-download", tags=["视频下载"])
api_router.include_router(download_platforms.router, prefix="/download/platforms", tags=["下载平台管理"])
api_router.include_router(download_statistics.router, prefix="/download/statistics", tags=["下载统计"])
api_router.include_router(download_queue.router, prefix="/download/queue", tags=["下载队列管理"])
api_router.include_router(websocket.router, prefix="/websocket", tags=["WebSocket"])
api_router.include_router(ai_config_router, prefix="/ai-config", tags=["ai-config"])
api_router.include_router(prompt_template_router, prefix="/prompt-templates", tags=["提示词模板"])
