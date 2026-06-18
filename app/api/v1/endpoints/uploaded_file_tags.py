"""上传文件标签接口

提供当前有效标签查询、人工修订与修订历史查询能力。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.security import utcnow
from app.models.uploaded_file import UploadedFile
from app.models.user import User
from app.models.video import Tag
from app.models.video_auto_tag import (
    UploadedFileTag,
    UploadedFileTagRevision,
    UploadedFileTagRevisionItem,
    VideoAutoTagItem,
    VideoAutoTagTask,
)
from app.schemas.common import ResponseModel
from app.schemas.video_auto_tag import (
    UploadedFileTagResponse,
    UploadedFileTagRevisionCreateRequest,
    UploadedFileTagRevisionResponse,
)

router = APIRouter()


def _get_owned_uploaded_file(video_file_id: int, current_user: User, db: Session) -> UploadedFile:
    """获取并校验上传文件归属。"""
    video_file = db.query(UploadedFile).filter(UploadedFile.id == video_file_id).first()
    if not video_file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video file not found")

    if current_user.role != "admin" and str(video_file.user_id) != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No permission to access this video")

    return video_file


def _merge_history_tag_entry(
    tag_map: dict[str, dict[str, Any]],
    *,
    video_file_id: int,
    tag_name: str,
    tag_id: int | None,
    confidence: float | None,
    source: str,
    created_by: str,
    created_at: datetime | None,
    updated_at: datetime | None,
    auto_tag_task_id: int | None = None,
    revision_id: int | None = None,
    reason: str | None = None,
    evidence_start_seconds: float | None = None,
    evidence_end_seconds: float | None = None,
) -> None:
    """将历史来源合并为标签集合项。"""
    normalized_tag_name = (tag_name or "").strip()
    if not normalized_tag_name:
        return

    entry = tag_map.get(normalized_tag_name)
    if entry is None:
        entry = {
            "id": 0,
            "video_file_id": video_file_id,
            "tag_id": tag_id,
            "tag_name": normalized_tag_name,
            "tag_name_snapshot": normalized_tag_name,
            "source": source,
            "_sources": {source} if source else set(),
            "confidence": float(confidence) if confidence is not None else 0.0,
            "auto_tag_task_id": auto_tag_task_id,
            "revision_id": revision_id,
            "is_effective": False,
            "evidence_start_seconds": evidence_start_seconds,
            "evidence_end_seconds": evidence_end_seconds,
            "reason": reason,
            "created_by": created_by,
            "created_at": created_at,
            "updated_at": updated_at,
            "_first_seen_at": created_at,
            "_last_seen_at": updated_at or created_at,
        }
        tag_map[normalized_tag_name] = entry
        return

    if source:
        entry.setdefault("_sources", set()).add(source)

    if tag_id is not None and entry["tag_id"] is None:
        entry["tag_id"] = tag_id
    if confidence is not None:
        entry["confidence"] = max(float(confidence), float(entry["confidence"]))

    candidate_seen_at = updated_at or created_at
    if created_at and (entry["_first_seen_at"] is None or created_at < entry["_first_seen_at"]):
        entry["_first_seen_at"] = created_at
    if candidate_seen_at and (entry["_last_seen_at"] is None or candidate_seen_at >= entry["_last_seen_at"]):
        entry["_last_seen_at"] = candidate_seen_at
        entry["source"] = source
        entry["created_by"] = created_by
        entry["reason"] = reason
        entry["evidence_start_seconds"] = evidence_start_seconds
        entry["evidence_end_seconds"] = evidence_end_seconds
        entry["auto_tag_task_id"] = auto_tag_task_id
        entry["revision_id"] = revision_id


def _build_history_tag_collection(video_file_id: int, db: Session) -> list[UploadedFileTagResponse]:
    """构建历史标签集合，并标记当前是否生效。"""
    tag_map: dict[str, dict[str, Any]] = {}

    auto_items = (
        db.query(VideoAutoTagItem, VideoAutoTagTask)
        .join(VideoAutoTagTask, VideoAutoTagItem.task_id == VideoAutoTagTask.id)
        .filter(
            VideoAutoTagTask.video_file_id == video_file_id,
            VideoAutoTagTask.is_active == True,
            VideoAutoTagItem.is_active == True,
        )
        .order_by(VideoAutoTagTask.id.asc(), VideoAutoTagItem.id.asc())
        .all()
    )
    for auto_item, task in auto_items:
        _merge_history_tag_entry(
            tag_map,
            video_file_id=video_file_id,
            tag_name=auto_item.tag_name,
            tag_id=auto_item.tag_id,
            confidence=auto_item.confidence,
            source="ai_auto",
            created_by="ai",
            created_at=auto_item.created_at,
            updated_at=auto_item.updated_at,
            auto_tag_task_id=task.id,
            revision_id=None,
            reason=auto_item.reason,
            evidence_start_seconds=auto_item.evidence_start_seconds,
            evidence_end_seconds=auto_item.evidence_end_seconds,
        )

    all_tag_items = (
        db.query(UploadedFileTag)
        .filter(UploadedFileTag.video_file_id == video_file_id)
        .order_by(UploadedFileTag.id.asc())
        .all()
    )
    effective_tag_names = {item.tag_name_snapshot for item in all_tag_items if item.is_effective}
    for current_item in all_tag_items:
        _merge_history_tag_entry(
            tag_map,
            video_file_id=video_file_id,
            tag_name=current_item.tag_name_snapshot,
            tag_id=current_item.tag_id,
            confidence=current_item.confidence,
            source=current_item.source,
            created_by=current_item.created_by,
            created_at=current_item.created_at,
            updated_at=current_item.updated_at,
            auto_tag_task_id=current_item.auto_tag_task_id,
            revision_id=current_item.revision_id,
            reason=current_item.reason,
            evidence_start_seconds=current_item.evidence_start_seconds,
            evidence_end_seconds=current_item.evidence_end_seconds,
        )

    response_items: list[UploadedFileTagResponse] = []
    for index, (tag_name, entry) in enumerate(tag_map.items(), start=1):
        entry["id"] = entry["id"] or index
        entry["tag_name"] = tag_name
        entry["tag_name_snapshot"] = tag_name
        entry["is_effective"] = tag_name in effective_tag_names
        entry["created_at"] = entry["_first_seen_at"] or entry["created_at"] or utcnow()
        entry["updated_at"] = entry["_last_seen_at"] or entry["updated_at"] or entry["created_at"]
        entry["sources"] = sorted(entry.get("_sources") or [])
        response_items.append(UploadedFileTagResponse.model_validate(entry))

    response_items.sort(
        key=lambda item: (
            not item.is_effective,
            -float(item.confidence or 0.0),
            item.tag_name,
        )
    )
    return response_items


@router.get(
    "/{video_file_id}/tags",
    response_model=ResponseModel[List[UploadedFileTagResponse]],
    response_model_by_alias=False,
)
def get_uploaded_file_tags(
    video_file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """获取上传文件历史标签集合及当前生效状态。"""
    _get_owned_uploaded_file(video_file_id, current_user, db)
    items = _build_history_tag_collection(video_file_id=video_file_id, db=db)

    return ResponseModel(
        code=200,
        message="Uploaded file tags retrieved successfully",
        data=items,
    )


@router.post("/{video_file_id}/tags/revisions", response_model=ResponseModel[UploadedFileTagRevisionResponse])
def create_uploaded_file_tag_revision(
    video_file_id: int,
    request: UploadedFileTagRevisionCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """创建上传文件标签修订版本。"""
    _get_owned_uploaded_file(video_file_id, current_user, db)

    if not request.operations:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Revision operations cannot be empty")

    allowed_actions = {"add", "remove", "adjust"}
    current_items = (
        db.query(UploadedFileTag)
        .filter(
            UploadedFileTag.video_file_id == video_file_id,
            UploadedFileTag.is_effective == True,
        )
        .order_by(UploadedFileTag.id.asc())
        .all()
    )
    if not current_items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No effective tags to revise")

    latest_revision = (
        db.query(UploadedFileTagRevision)
        .filter(UploadedFileTagRevision.video_file_id == video_file_id)
        .order_by(UploadedFileTagRevision.revision_number.desc(), UploadedFileTagRevision.id.desc())
        .first()
    )
    latest_task = (
        db.query(VideoAutoTagTask)
        .filter(
            VideoAutoTagTask.video_file_id == video_file_id,
            VideoAutoTagTask.status == "completed",
            VideoAutoTagTask.is_active == True,
        )
        .order_by(VideoAutoTagTask.id.desc())
        .first()
    )

    revision = UploadedFileTagRevision(
        video_file_id=video_file_id,
        base_task_id=latest_task.id if latest_task else None,
        revision_number=(latest_revision.revision_number + 1) if latest_revision else 1,
        change_reason=request.change_reason,
        created_by=str(current_user.id),
    )

    current_map = {
        item.tag_name_snapshot: {
            "tag_id": item.tag_id,
            "tag_name": item.tag_name_snapshot,
            "confidence": item.confidence,
            "reason": item.reason,
            "evidence_start_seconds": item.evidence_start_seconds,
            "evidence_end_seconds": item.evidence_end_seconds,
            "source": item.source,
            "auto_tag_task_id": item.auto_tag_task_id,
            "revision_id": item.revision_id,
            "created_by": item.created_by,
        }
        for item in current_items
    }

    try:
        db.add(revision)
        db.flush()

        for operation in request.operations:
            if operation.action not in allowed_actions:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unsupported revision action: {operation.action}",
                )

            tag_name = operation.tag_name.strip()
            if not tag_name:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tag name cannot be empty")

            tag_record = None
            if operation.tag_id:
                tag_record = db.query(Tag).filter(Tag.id == operation.tag_id).first()
            if not tag_record:
                tag_record = db.query(Tag).filter(Tag.name == tag_name).first()

            if operation.action == "remove":
                current_map.pop(tag_name, None)
            else:
                allowed_sources = {None, "ai_assisted"}
                if operation.source not in allowed_sources:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Unsupported tag source: {operation.source}",
                    )

                if not tag_record:
                    tag_record = Tag(
                        name=tag_name,
                        category="manual",
                        description=None,
                        color=None,
                        source_type="free_promoted",
                        tag_group_id=None,
                        is_active=True,
                    )
                    db.add(tag_record)
                    db.flush()

                current_map[tag_name] = {
                    "tag_id": tag_record.id,
                    "tag_name": tag_name,
                    "confidence": operation.confidence if operation.confidence is not None else 1.0,
                    "reason": operation.note,
                    "evidence_start_seconds": None,
                    "evidence_end_seconds": None,
                    "source": operation.source or "manual_override",
                    "auto_tag_task_id": latest_task.id if latest_task else None,
                    "revision_id": revision.id,
                    "created_by": str(current_user.id),
                }

            db.add(
                UploadedFileTagRevisionItem(
                    revision_id=revision.id,
                    tag_id=tag_record.id if tag_record else operation.tag_id,
                    tag_name=tag_name,
                    action=operation.action,
                    confidence=operation.confidence,
                    note=operation.note,
                )
            )

        db.query(UploadedFileTag).filter(
            UploadedFileTag.video_file_id == video_file_id,
            UploadedFileTag.is_effective == True,
        ).update({"is_effective": False}, synchronize_session=False)

        for item in current_map.values():
            db.add(
                UploadedFileTag(
                    video_file_id=video_file_id,
                    tag_id=item["tag_id"],
                    tag_name_snapshot=item["tag_name"],
                    source=item["source"],
                    confidence=item["confidence"] if item["confidence"] is not None else 1.0,
                    auto_tag_task_id=item["auto_tag_task_id"],
                    revision_id=item["revision_id"],
                    is_effective=True,
                    evidence_start_seconds=item["evidence_start_seconds"],
                    evidence_end_seconds=item["evidence_end_seconds"],
                    reason=item["reason"],
                    created_by=item["created_by"],
                )
            )

        db.commit()
        db.refresh(revision)
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create tag revision: {str(exc)}",
        ) from exc

    return ResponseModel(
        code=200,
        message="Uploaded file tag revision created successfully",
        data=UploadedFileTagRevisionResponse.model_validate(revision),
    )


@router.get("/{video_file_id}/tags/revisions", response_model=ResponseModel[List[UploadedFileTagRevisionResponse]])
def get_uploaded_file_tag_revisions(
    video_file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """获取上传文件标签修订历史。"""
    _get_owned_uploaded_file(video_file_id, current_user, db)
    revisions = (
        db.query(UploadedFileTagRevision)
        .filter(UploadedFileTagRevision.video_file_id == video_file_id)
        .order_by(UploadedFileTagRevision.revision_number.desc(), UploadedFileTagRevision.id.desc())
        .all()
    )

    return ResponseModel(
        code=200,
        message="Uploaded file tag revisions retrieved successfully",
        data=[UploadedFileTagRevisionResponse.model_validate(item) for item in revisions],
    )


@router.get(
    "/{video_file_id}/tags/revisions/{revision_id}",
    response_model=ResponseModel[UploadedFileTagRevisionResponse],
)
def get_uploaded_file_tag_revision_detail(
    video_file_id: int,
    revision_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """获取上传文件标签修订详情。"""
    _get_owned_uploaded_file(video_file_id, current_user, db)
    revision = (
        db.query(UploadedFileTagRevision)
        .filter(
            UploadedFileTagRevision.id == revision_id,
            UploadedFileTagRevision.video_file_id == video_file_id,
        )
        .first()
    )
    if not revision:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag revision not found")

    return ResponseModel(
        code=200,
        message="Uploaded file tag revision retrieved successfully",
        data=UploadedFileTagRevisionResponse.model_validate(revision),
    )
