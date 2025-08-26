"""应用启动脚本

整合FastAPI API服务和Gradio Web界面。
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from gradio.routes import mount_gradio_app

from app.core.config import settings
from app.core.logging import setup_logging
from app.main import app as fastapi_app
from app.ui.gradio_app import create_gradio_app

# 设置日志
setup_logging()

# 创建Gradio应用
gradio_app = create_gradio_app()

# 将Gradio应用挂载到FastAPI
app = mount_gradio_app(
    blocks=gradio_app,
    app=fastapi_app,
    path="/ui",
    gradio_api_url="http://localhost:7860/api/"
)

# 添加根路径重定向
@fastapi_app.get("/")
async def root():
    """根路径重定向到UI界面"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/ui")


def start_server(
    host: str = None,
    port: int = None,
    reload: bool = None,
    workers: int = None
):
    """启动服务器
    
    Args:
        host: 服务器主机地址
        port: 服务器端口
        reload: 是否启用热重载
        workers: 工作进程数
    """
    uvicorn.run(
        "app.app:app",
        host=host or settings.host,
        port=port or settings.port,
        reload=reload if reload is not None else settings.debug,
        workers=workers or (settings.workers if not settings.debug else 1),
        log_level=settings.log_level.lower(),
        access_log=True,
    )


if __name__ == "__main__":
    start_server()