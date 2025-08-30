"""数据模型模块

导入所有数据模型，确保SQLAlchemy能够正确识别和创建表。
"""

from app.models.user import User, UserSession
from app.models.video import (
    Video, DownloadTask, AnalysisTask, Tag, VideoTag, AIConfig
)
from app.models.prompt_template import PromptTemplate
from .tag_group import TagGroup, TagGroupTag

# 导出所有模型
__all__ = [
    "User",
    "UserSession", 
    "Video",
    "DownloadTask",
    "AnalysisTask",
    "Tag",
    "VideoTag",
    "AIConfig",
    "PromptTemplate",
    "TagGroup",
    "TagGroupTag",
]