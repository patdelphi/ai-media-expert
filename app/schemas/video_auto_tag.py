"""自动打标相关数据模式

定义自动打标任务、当前有效标签与修订操作的数据结构。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class VideoAutoTagStartRequest(BaseModel):
    """启动自动打标请求。"""

    video_file_id: int = Field(description="上传视频文件 ID")
    ai_config_id: int = Field(description="AI 配置 ID")
    tag_group_ids: Optional[List[int]] = Field(default=None, description="标签组 ID 列表")
    transmission_method: str = Field(default="url", description="视频传输方式")
    force_retag: bool = Field(default=False, description="是否强制重新打标")


class VideoAutoTagStartResponse(BaseModel):
    """启动自动打标响应。"""

    task_id: int
    status: str
    message: str


class VideoAutoTagItemResponse(BaseModel):
    """自动打标命中项响应。"""

    id: int
    tag_id: Optional[int] = None
    tag_name: str
    tag_group_id: Optional[int] = None
    tag_source: str
    match_type: str
    confidence: float
    evidence_text: Optional[str] = None
    evidence_start_seconds: Optional[float] = None
    evidence_end_seconds: Optional[float] = None
    reason: Optional[str] = None
    is_promoted: bool

    model_config = ConfigDict(from_attributes=True)


class VideoAutoTagTaskResponse(BaseModel):
    """自动打标任务详情响应。"""

    id: int
    video_file_id: int
    ai_config_id: int
    tag_group_ids: Optional[List[int]] = None
    prompt_version: Optional[str] = None
    prompt_content: str
    transmission_method: str
    status: str
    progress: int
    structured_summary: Optional[Any] = None
    result_metadata: Optional[Any] = None
    token_usage: Optional[Any] = None
    cost_estimate: Optional[float] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    items: List[VideoAutoTagItemResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class VideoAutoTagTaskHistoryItemResponse(BaseModel):
    """自动打标任务历史项响应。"""

    id: int
    video_file_id: int
    ai_config_id: int
    status: str
    progress: int
    prompt_version: Optional[str] = None
    transmission_method: str
    structured_summary: Optional[Any] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    items: List[VideoAutoTagItemResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class UploadedFileTagResponse(BaseModel):
    """上传文件当前有效标签响应。"""

    id: int
    video_file_id: int
    tag_id: Optional[int] = None
    tag_name: str = Field(alias="tag_name_snapshot")
    tag_name_snapshot: Optional[str] = None
    source: str
    sources: List[str] = Field(default_factory=list, description="标签历史来源去重集合")
    confidence: float
    auto_tag_task_id: Optional[int] = None
    revision_id: Optional[int] = None
    is_effective: bool
    evidence_start_seconds: Optional[float] = None
    evidence_end_seconds: Optional[float] = None
    reason: Optional[str] = None
    created_by: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class UploadedFileTagRevisionOperation(BaseModel):
    """标签修订操作。"""

    action: str = Field(description="add/remove/adjust")
    tag_id: Optional[int] = Field(default=None, description="正式标签 ID")
    tag_name: str = Field(description="标签名称")
    confidence: Optional[float] = Field(default=None, description="置信度")
    note: Optional[str] = Field(default=None, description="修订备注")
    source: Optional[str] = Field(default=None, description="标签来源（可选）：ai_assisted 等")


class UploadedFileTagRevisionCreateRequest(BaseModel):
    """创建标签修订请求。"""

    change_reason: Optional[str] = Field(default=None, description="修订原因")
    operations: List[UploadedFileTagRevisionOperation] = Field(description="修订操作列表")


class UploadedFileTagRevisionItemResponse(BaseModel):
    """标签修订明细响应。"""

    id: int
    tag_id: Optional[int] = None
    tag_name: str
    action: str
    confidence: Optional[float] = None
    note: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UploadedFileTagRevisionResponse(BaseModel):
    """标签修订版本响应。"""

    id: int
    video_file_id: int
    base_task_id: Optional[int] = None
    revision_number: int
    change_reason: Optional[str] = None
    created_by: str
    created_at: datetime
    updated_at: datetime
    items: List[UploadedFileTagRevisionItemResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
