"""应用启动脚本

纯FastAPI API服务，前端已分离。
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.core.config import settings
from app.core.app_logging import setup_logging
from app.core.db_manager import ensure_database_ready
from app.api.v1 import api_router
from app.middleware.exception_handler import ExceptionHandlerMiddleware

# 创建FastAPI应用
fastapi_app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI新媒体专家系统API"
)

# 添加CORS中间件
fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加全局异常处理中间件
fastapi_app.add_middleware(ExceptionHandlerMiddleware)

# 挂载静态文件目录
uploads_dir = Path("uploads")
if uploads_dir.exists():
    fastapi_app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# 包含API路由
fastapi_app.include_router(api_router, prefix="/api/v1")

@fastapi_app.on_event("startup")
def startup_database_setup() -> None:
    if settings.is_development:
        ok = ensure_database_ready()
        if not ok:
            raise RuntimeError("Database is not ready")

# 健康检查端点
@fastapi_app.get("/health")
async def health_check():
    return {"status": "healthy"}

# API根路径
@fastapi_app.get("/")
async def root():
    return {
        "message": "AI新媒体专家系统API",
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health"
    }

# 设置日志
setup_logging()

# 导出应用实例
app = fastapi_app

def start_server():
    """启动服务器"""
    uvicorn.run(
        "app.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

if __name__ == "__main__":
    start_server()
