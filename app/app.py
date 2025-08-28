"""应用启动脚本

纯FastAPI API服务，前端已分离。
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import setup_logging
from app.api.v1 import api_router

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

# 包含API路由
fastapi_app.include_router(api_router, prefix="/api/v1")

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

if __name__ == "__main__":
    uvicorn.run(
        "app.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )