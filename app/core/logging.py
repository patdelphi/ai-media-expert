"""日志配置模块

配置结构化日志记录，支持文件和控制台输出。
"""

import logging
import logging.handlers
import sys
from pathlib import Path

import structlog

from app.core.config import settings


def setup_logging():
    """设置应用日志配置"""
    
    # 创建日志目录
    if settings.log_file:
        settings.log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # 配置标准库日志
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level.upper()),
    )
    
    # 配置文件日志处理器
    handlers = []
    
    if settings.log_file:
        file_handler = logging.handlers.RotatingFileHandler(
            settings.log_file,
            maxBytes=settings.log_max_size,
            backupCount=settings.log_backup_count,
            encoding="utf-8"
        )
        handlers.append(file_handler)
    
    # 配置structlog
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]
    
    # 根据环境选择输出格式
    if settings.is_development:
        # 开发环境使用彩色输出
        processors.append(structlog.dev.ConsoleRenderer())
    else:
        # 生产环境使用JSON格式
        processors.append(structlog.processors.JSONRenderer())
    
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # 配置第三方库的日志级别
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.debug else logging.WARNING
    )
    
    # 如果不是调试模式，降低一些库的日志级别
    if not settings.debug:
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("requests").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)


def get_logger(name: str = None):
    """获取结构化日志记录器
    
    Args:
        name: 日志记录器名称
    
    Returns:
        结构化日志记录器实例
    """
    return structlog.get_logger(name)


# 创建应用级别的日志记录器
app_logger = get_logger("app")
api_logger = get_logger("api")
download_logger = get_logger("download")
analysis_logger = get_logger("analysis")
security_logger = get_logger("security")