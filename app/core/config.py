"""应用配置模块

统一管理应用的所有配置项，支持环境变量和配置文件。
"""

import os
from pathlib import Path
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置类"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    
    # 应用基础配置
    app_name: str = Field(default="AI新媒体专家系统", validation_alias="APP_NAME")
    app_version: str = Field(default="0.1.0", validation_alias="APP_VERSION")
    environment: str = Field(default="development", validation_alias="ENVIRONMENT")
    debug: bool = Field(default=True, validation_alias="DEBUG")
    secret_key: str = Field(validation_alias="SECRET_KEY")
    
    # 服务器配置
    host: str = Field(default="0.0.0.0", validation_alias="HOST")
    port: int = Field(default=8000, validation_alias="PORT")
    workers: int = Field(default=1, validation_alias="WORKERS")
    
    # 公网访问配置（用于GLM-4.5V等视频理解模型）
    ngrok_url: Optional[str] = Field(default=None, validation_alias="NGROK_URL")
    public_base_url: Optional[str] = Field(default=None, validation_alias="PUBLIC_BASE_URL")
    
    # 数据库配置
    database_url: str = Field(validation_alias="DATABASE_URL")
    
    # Redis配置
    redis_url: str = Field(default="redis://localhost:6379/0", validation_alias="REDIS_URL")
    
    # Celery配置 - 使用内存作为后备方案
    celery_broker_url: str = Field(default="memory://", validation_alias="CELERY_BROKER_URL")
    celery_result_backend: str = Field(default="cache+memory://", validation_alias="CELERY_RESULT_BACKEND")
    
    # 下载API配置
    download_api_url: str = Field(default="http://localhost:8001", description="下载API服务地址")
    download_api_timeout: int = Field(default=30, description="下载API请求超时时间(秒)")
    
    # JWT配置
    jwt_secret_key: str = Field(validation_alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", validation_alias="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(default=30, validation_alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
    jwt_refresh_token_expire_days: int = Field(default=30, validation_alias="JWT_REFRESH_TOKEN_EXPIRE_DAYS")
    
    # 文件存储配置
    upload_dir: Path = Field(default=Path("./uploads"), validation_alias="UPLOAD_DIR")
    max_file_size: int = Field(default=1073741824, validation_alias="MAX_FILE_SIZE")
    allowed_video_extensions: List[str] = Field(
        default=[".mp4", ".avi", ".mov", ".mkv", ".flv", ".wmv", ".webm"],
        validation_alias="ALLOWED_VIDEO_EXTENSIONS",
    )
    
    # 视频上传配置
    chunk_size: int = Field(default=1048576, validation_alias="CHUNK_SIZE")
    max_chunks: int = Field(default=10000, validation_alias="MAX_CHUNKS")
    upload_session_timeout: int = Field(default=86400, validation_alias="UPLOAD_SESSION_TIMEOUT")
    concurrent_uploads: int = Field(default=3, validation_alias="CONCURRENT_UPLOADS")
    
    # FFmpeg配置
    ffmpeg_path: str = Field(default="ffmpeg", validation_alias="FFMPEG_PATH")
    ffprobe_path: str = Field(default="ffprobe", validation_alias="FFPROBE_PATH")
    thumbnail_quality: int = Field(default=2, validation_alias="THUMBNAIL_QUALITY")
    preview_image_count: int = Field(default=6, validation_alias="PREVIEW_IMAGE_COUNT")
    
    # 视频下载配置
    download_dir: Path = Field(default=Path("./downloads"), validation_alias="DOWNLOAD_DIR")
    max_concurrent_downloads: int = Field(default=5, validation_alias="MAX_CONCURRENT_DOWNLOADS")
    download_timeout: int = Field(default=3600, validation_alias="DOWNLOAD_TIMEOUT")
    
    # AI模型配置
    model_cache_dir: Path = Field(default=Path("./models"), validation_alias="MODEL_CACHE_DIR")
    device: str = Field(default="cpu", validation_alias="DEVICE")
    batch_size: int = Field(default=1, validation_alias="BATCH_SIZE")
    
    # 日志配置
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")
    log_file: Optional[Path] = Field(default=Path("./logs/app.log"), validation_alias="LOG_FILE")
    log_max_size: int = Field(default=10485760, validation_alias="LOG_MAX_SIZE")
    log_backup_count: int = Field(default=5, validation_alias="LOG_BACKUP_COUNT")
    
    # 监控配置
    prometheus_enabled: bool = Field(default=False, validation_alias="PROMETHEUS_ENABLED")
    prometheus_port: int = Field(default=9090, validation_alias="PROMETHEUS_PORT")
    
    # 安全配置
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:3001", "http://localhost:8080"],
        validation_alias="CORS_ORIGINS",
    )
    allowed_hosts: List[str] = Field(
        default=["localhost", "127.0.0.1"],
        validation_alias="ALLOWED_HOSTS",
    )
    
    # 限流配置
    rate_limit_enabled: bool = Field(default=True, validation_alias="RATE_LIMIT_ENABLED")
    rate_limit_requests: int = Field(default=100, validation_alias="RATE_LIMIT_REQUESTS")
    rate_limit_period: int = Field(default=60, validation_alias="RATE_LIMIT_PERIOD")
    
    @field_validator("allowed_video_extensions", mode="before")
    def parse_video_extensions(cls, v):
        """解析视频扩展名列表"""
        if isinstance(v, str):
            return [ext.strip() for ext in v.split(",")]
        return v
    
    @field_validator("cors_origins", mode="before")
    def parse_cors_origins(cls, v):
        """解析CORS源列表"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @field_validator("allowed_hosts", mode="before")
    def parse_allowed_hosts(cls, v):
        """解析允许的主机列表"""
        if isinstance(v, str):
            return [host.strip() for host in v.split(",")]
        return v
    
    def create_directories(self):
        """创建必要的目录"""
        directories = [
            self.upload_dir,
            self.download_dir,
            self.model_cache_dir,
        ]
        
        if self.log_file:
            directories.append(self.log_file.parent)
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    @property
    def is_development(self) -> bool:
        """是否为开发环境"""
        return self.environment.lower() == "development"
    
    @property
    def is_production(self) -> bool:
        """是否为生产环境"""
        return self.environment.lower() == "production"
    
    @property
    def database_url_sync(self) -> str:
        """同步数据库URL"""
        if self.database_url.startswith("sqlite"):
            return self.database_url
        # 将异步PostgreSQL URL转换为同步版本
        return self.database_url.replace("postgresql+asyncpg://", "postgresql://")
    
    def get_base_url(self) -> str:
        """获取基础URL，优先使用公网地址"""
        if self.public_base_url:
            return self.public_base_url
        elif self.ngrok_url:
            return self.ngrok_url
        else:
            return f"http://{self.host}:{self.port}"
    
# 创建全局配置实例
settings = Settings()

# 创建必要的目录
settings.create_directories()
