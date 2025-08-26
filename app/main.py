"""FastAPI应用主入口

配置和启动AI新媒体专家系统的Web应用。
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.database import create_tables
from app.api.v1.api import api_router
from app.core.logging import setup_logging

# 设置日志
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("Starting AI Media Expert System...")
    
    # 创建数据库表
    try:
        create_tables()
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise
    
    # 创建必要的目录
    settings.create_directories()
    logger.info("Required directories created")
    
    yield
    
    # 关闭时执行
    logger.info("Shutting down AI Media Expert System...")


# 创建FastAPI应用实例
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI新媒体专家系统 - 提供视频下载、内容分析、字幕处理等专业服务",
    openapi_url="/api/v1/openapi.json" if settings.debug else None,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan,
)

# 添加CORS中间件
if settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# 添加可信主机中间件
if settings.allowed_hosts:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.allowed_hosts
    )


# 全局异常处理器
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理"""
    logger.error(f"Global exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "code": 500,
            "message": "Internal server error",
            "detail": str(exc) if settings.debug else "An unexpected error occurred"
        }
    )


# 健康检查端点
@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment
    }


# 就绪检查端点
@app.get("/ready")
async def readiness_check():
    """就绪检查端点"""
    # 这里可以添加数据库连接检查等
    return {
        "status": "ready",
        "timestamp": "2025-01-26T00:00:00Z"
    }


# 包含API路由
app.include_router(api_router, prefix="/api/v1")


# 静态文件服务（如果需要）
static_dir = Path("static")
if static_dir.exists():
    app.mount("/static", StaticFiles(directory="static"), name="static")


# 根路径重定向
@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "Welcome to AI Media Expert System",
        "version": settings.app_version,
        "docs_url": "/docs" if settings.debug else None,
        "api_url": "/api/v1"
    }


def main():
    """主函数，用于命令行启动"""
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        workers=settings.workers if not settings.debug else 1,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()