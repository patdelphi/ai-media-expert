"""自动打标相关数据模型

定义自动打标任务、命中项、当前有效标签与修订历史模型。
"""

from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship

from app.core.database import BaseModel


class VideoAutoTagTask(BaseModel):
    """自动打标任务模型。"""

    __tablename__ = "video_auto_tag_tasks"

    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    video_file_id = Column(Integer, ForeignKey("uploaded_files.id"), nullable=False, index=True)
    ai_config_id = Column(Integer, ForeignKey("ai_configs.id"), nullable=False, index=True)
    tag_group_ids = Column(JSON, nullable=True, comment="本次打标使用的标签组 ID 列表")

    prompt_version = Column(String(50), nullable=True, comment="自动打标提示词版本")
    prompt_content = Column(Text, nullable=False, comment="自动打标完整提示词")
    transmission_method = Column(String(20), default="url", nullable=False, comment="视频传输方式")
    video_url = Column(String(1000), nullable=True, comment="调试用视频 URL，不含敏感 token")
    video_file_path = Column(String(1000), nullable=True, comment="本地视频文件路径")

    status = Column(String(20), default="pending", nullable=False, index=True)
    progress = Column(Integer, default=0, nullable=False)

    request_payload_summary = Column(JSON, nullable=True, comment="请求摘要")
    raw_response = Column(Text, nullable=True, comment="原始模型响应")
    structured_summary = Column(JSON, nullable=True, comment="结构化摘要")
    result_metadata = Column(JSON, nullable=True, comment="结果元数据")

    processing_time = Column(Float, nullable=True, comment="处理耗时（秒）")
    token_usage = Column(JSON, nullable=True, comment="Token 使用统计")
    cost_estimate = Column(Float, nullable=True, comment="预估成本")

    error_message = Column(Text, nullable=True, comment="错误信息")
    debug_info = Column(JSON, nullable=True, comment="调试信息")

    started_at = Column(String(50), nullable=True, comment="开始时间 ISO 字符串")
    completed_at = Column(String(50), nullable=True, comment="完成时间 ISO 字符串")
    is_active = Column(Boolean, default=True, nullable=False, comment="是否有效")

    user = relationship("User")
    video_file = relationship("UploadedFile", back_populates="auto_tag_tasks")
    ai_config = relationship("AIConfig")
    items = relationship("VideoAutoTagItem", back_populates="task", cascade="all, delete-orphan")


class VideoAutoTagItem(BaseModel):
    """自动打标命中项模型。"""

    __tablename__ = "video_auto_tag_items"

    task_id = Column(Integer, ForeignKey("video_auto_tag_tasks.id"), nullable=False, index=True)
    tag_id = Column(Integer, ForeignKey("tags.id"), nullable=True, index=True)
    tag_name = Column(String(100), nullable=False, index=True)
    tag_group_id = Column(Integer, ForeignKey("tag_groups.id"), nullable=True, index=True)
    tag_source = Column(String(20), nullable=False, comment="标签来源：library/free")
    match_type = Column(String(20), default="ai_detected", nullable=False, comment="命中类型")
    confidence = Column(Float, nullable=False, default=0.0)
    evidence_text = Column(Text, nullable=True)
    evidence_start_seconds = Column(Float, nullable=True)
    evidence_end_seconds = Column(Float, nullable=True)
    reason = Column(Text, nullable=True)
    is_promoted = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    task = relationship("VideoAutoTagTask", back_populates="items")
    tag = relationship("Tag")
    tag_group = relationship("TagGroup")


class UploadedFileTag(BaseModel):
    """上传文件当前有效标签模型。"""

    __tablename__ = "uploaded_file_tags"

    video_file_id = Column(Integer, ForeignKey("uploaded_files.id"), nullable=False, index=True)
    tag_id = Column(Integer, ForeignKey("tags.id"), nullable=True, index=True)
    tag_name_snapshot = Column(String(100), nullable=False, index=True)
    source = Column(String(20), nullable=False, comment="标签来源：ai_auto/manual/manual_override")
    confidence = Column(Float, default=1.0, nullable=False)
    auto_tag_task_id = Column(Integer, ForeignKey("video_auto_tag_tasks.id"), nullable=True, index=True)
    revision_id = Column(Integer, ForeignKey("uploaded_file_tag_revisions.id"), nullable=True, index=True)
    is_effective = Column(Boolean, default=True, nullable=False)
    evidence_start_seconds = Column(Float, nullable=True)
    evidence_end_seconds = Column(Float, nullable=True)
    reason = Column(Text, nullable=True)
    created_by = Column(String(20), default="system", nullable=False)

    video_file = relationship("UploadedFile", back_populates="effective_tags")
    tag = relationship("Tag")
    task = relationship("VideoAutoTagTask")


class UploadedFileTagRevision(BaseModel):
    """上传文件标签修订版本模型。"""

    __tablename__ = "uploaded_file_tag_revisions"

    video_file_id = Column(Integer, ForeignKey("uploaded_files.id"), nullable=False, index=True)
    base_task_id = Column(Integer, ForeignKey("video_auto_tag_tasks.id"), nullable=True, index=True)
    revision_number = Column(Integer, nullable=False, default=1)
    change_reason = Column(Text, nullable=True)
    created_by = Column(String(20), nullable=False)

    video_file = relationship("UploadedFile", back_populates="tag_revisions")
    base_task = relationship("VideoAutoTagTask")
    items = relationship("UploadedFileTagRevisionItem", back_populates="revision", cascade="all, delete-orphan")


class UploadedFileTagRevisionItem(BaseModel):
    """上传文件标签修订明细模型。"""

    __tablename__ = "uploaded_file_tag_revision_items"

    revision_id = Column(Integer, ForeignKey("uploaded_file_tag_revisions.id"), nullable=False, index=True)
    tag_id = Column(Integer, ForeignKey("tags.id"), nullable=True, index=True)
    tag_name = Column(String(100), nullable=False, index=True)
    action = Column(String(20), nullable=False, comment="add/remove/adjust")
    confidence = Column(Float, nullable=True)
    note = Column(Text, nullable=True)

    revision = relationship("UploadedFileTagRevision", back_populates="items")
    tag = relationship("Tag")
