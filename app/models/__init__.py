"""数据模型模块

导入所有数据模型，确保SQLAlchemy能够正确识别和创建表。
"""

from app.models.user import User, UserSession
from app.models.video import (
    Video, DownloadTask, AnalysisTask, Tag, VideoTag, AIConfig
)
from app.models.uploaded_file import UploadedFile
from app.models.prompt_template import PromptTemplate
from app.models.video_analysis import VideoAnalysis
from app.models.download_history import (
    DownloadHistory, DownloadStatistics, PlatformStatistics, 
    DownloadTag, DownloadHistoryTag
)
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
    "UploadedFile",
    "PromptTemplate",
    "VideoAnalysis",
<<<<<<< HEAD
    "DownloadHistory",
    "DownloadStatistics",
    "PlatformStatistics",
    "DownloadTag",
    "DownloadHistoryTag",
=======
>>>>>>> bf58121 (feat: 优化视频分析流式输出和历史记录功能)
    "TagGroup",
    "TagGroupTag",
]