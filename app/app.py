"""应用启动脚本

纯FastAPI API服务，前端已分离。
"""

from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

import uvicorn
from fastapi.responses import JSONResponse
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.v1 import api_router
from app.core.app_logging import setup_logging
from app.core.config import settings
from app.core.database import SessionLocal
from app.core.db_manager import ensure_database_ready
from app.middleware.exception_handler import ExceptionHandlerMiddleware


@contextmanager
def lifespan(_app: FastAPI) -> Generator[None, None, None]:
    """应用生命周期钩子。"""
    if settings.is_development:
        ok = ensure_database_ready()
        if not ok:
            raise RuntimeError("Database is not ready")
    yield


def _get_allowed_origins() -> list[str]:
    """返回当前环境允许的 CORS 来源。"""
    origins = settings.cors_origins or []
    if settings.is_production and "*" in origins:
        raise RuntimeError("Production CORS origins must not contain '*'")
    return origins


def _get_allowed_hosts() -> list[str]:
    """返回当前环境允许的 Host 白名单。"""
    hosts = settings.allowed_hosts or ["*"]
    if settings.is_production and "*" in hosts:
        raise RuntimeError("Production allowed hosts must not contain '*'")
    if not settings.is_production:
        return sorted({*hosts, "localhost", "127.0.0.1", "test", "testserver"})
    return hosts


def _is_database_ready() -> bool:
    """执行最小化数据库探活，不泄露内部错误细节。"""
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
    finally:
        db.close()

# 创建FastAPI应用
fastapi_app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI新媒体专家系统API",
    lifespan=lifespan,
)

# 添加受信任主机校验，避免生产环境接受任意 Host 头。
fastapi_app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=_get_allowed_hosts(),
)

# 添加CORS中间件
fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=_get_allowed_origins(),
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

# 健康检查端点
@fastapi_app.get("/health")
async def health_check():
    return {"status": "healthy"}


@fastapi_app.get("/health/liveness")
async def liveness_check():
    """存活检查只确认服务进程可响应。"""
    return {"status": "alive"}


@fastapi_app.get("/health/readiness")
async def readiness_check():
    """就绪检查只返回最小状态，不暴露内部细节。"""
    if _is_database_ready():
        return {"status": "ready"}
    return JSONResponse(status_code=503, content={"status": "not_ready"})

# API根路径
@fastapi_app.get("/")
async def root():
    return {
        "message": "AI新媒体专家系统API",
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health/liveness",
        "readiness": "/health/readiness",
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
