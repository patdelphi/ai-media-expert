"""数据模式模块

定义API请求和响应的数据结构。
"""

from app.schemas.auth import (
    UserCreate, UserLogin, UserResponse, UserUpdate,
    Token, TokenRefresh, PasswordChange
)
from app.schemas.common import (
    ResponseModel, PaginatedResponse, PaginationParams,
    ErrorResponse, TaskStatus, FileInfo
)
from app.schemas.video import (
    VideoResponse, VideoListResponse, VideoCreate, VideoUpdate,
    DownloadTaskCreate, DownloadTaskResponse,
    AnalysisTaskCreate, AnalysisTaskResponse,
    TagCreate, TagResponse, VideoTagCreate, VideoTagResponse
)
from app.schemas.prompt_template import (
    PromptTemplateCreate, PromptTemplateUpdate, PromptTemplateResponse
)

__all__ = [
    # Auth schemas
    "UserCreate", "UserLogin", "UserResponse", "UserUpdate",
    "Token", "TokenRefresh", "PasswordChange",
    
    # Common schemas
    "ResponseModel", "PaginatedResponse", "PaginationParams",
    "ErrorResponse", "TaskStatus", "FileInfo",
    
    # Video schemas
    "VideoResponse", "VideoListResponse", "VideoCreate", "VideoUpdate",
    "DownloadTaskCreate", "DownloadTaskResponse",
    "AnalysisTaskCreate", "AnalysisTaskResponse",
    "TagCreate", "TagResponse", "VideoTagCreate", "VideoTagResponse",
    
    # Prompt Template schemas
    "PromptTemplateCreate", "PromptTemplateUpdate", "PromptTemplateResponse",
]