"""API v1版本

第一版API接口定义。
"""

from fastapi import APIRouter
from .endpoints import auth, users, system_config, tag_groups, video_upload, video_processing, simple_upload, test_upload, minimal_upload, file_manager, video_analysis, video_download, websocket, download_platforms, download_statistics, download_queue, download
from .upload import router as upload_router
from .videos import router as videos_router
from .analysis import router as analysis_router
from .ai_config import router as ai_config_router
from .prompt_template import router as prompt_template_router

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(users.router, prefix="/users", tags=["用户管理"])
api_router.include_router(system_config.router, prefix="/system/config", tags=["系统配置"])
api_router.include_router(tag_groups.router, prefix="/tag-groups", tags=["标签组管理"])
api_router.include_router(video_upload.router, prefix="/upload", tags=["视频上传"])
api_router.include_router(simple_upload.router, prefix="/simple-upload", tags=["简单上传"])
api_router.include_router(test_upload.router, prefix="/test-upload", tags=["测试上传"])
api_router.include_router(minimal_upload.router, prefix="/minimal", tags=["最简上传"])
api_router.include_router(file_manager.router, prefix="/files", tags=["文件管理"])
api_router.include_router(video_processing.router, prefix="/processing", tags=["视频处理"])
api_router.include_router(video_analysis.router, prefix="/video-analysis", tags=["视频解析"])
api_router.include_router(video_download.router, prefix="/video-download", tags=["视频下载"])
# 添加下载相关API路由
api_router.include_router(download.router, prefix="/download", tags=["下载任务管理"])
api_router.include_router(download_platforms.router, prefix="/download/platforms", tags=["下载平台管理"])
api_router.include_router(download_statistics.router, prefix="/download/statistics", tags=["下载统计"])
api_router.include_router(download_queue.router, prefix="/download/queue", tags=["下载队列管理"])
api_router.include_router(websocket.router, prefix="/websocket", tags=["WebSocket"])

# 其他功能路由
api_router.include_router(upload_router, prefix="/upload", tags=["upload"])
api_router.include_router(videos_router, prefix="/videos", tags=["videos"])
api_router.include_router(analysis_router, prefix="/analysis", tags=["analysis"])
api_router.include_router(ai_config_router, prefix="/ai-config", tags=["ai-config"])
api_router.include_router(prompt_template_router, prefix="/prompt-templates", tags=["提示词模板"])