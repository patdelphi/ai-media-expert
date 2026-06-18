"""自动打标功能测试

覆盖自动打标任务创建、任务处理与当前有效标签查询的最小闭环。
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import BackgroundTasks

from app.api.v1.endpoints.tag_groups import create_tag_group
from app.api.v1.endpoints.uploaded_file_tags import (
    create_uploaded_file_tag_revision,
    get_uploaded_file_tag_revision_detail,
    get_uploaded_file_tag_revisions,
    get_uploaded_file_tags,
)
from app.api.v1.endpoints.video_auto_tags import (
    get_video_auto_tag_task,
    list_video_auto_tag_tasks,
    start_video_auto_tag_task,
)
from app.models.tag_group import TagGroup
from app.models.video import AIConfig, Tag
from app.models.video_auto_tag import (
    UploadedFileTag,
    UploadedFileTagRevision,
    UploadedFileTagRevisionItem,
    VideoAutoTagItem,
    VideoAutoTagTask,
)
from app.schemas.tag_group import TagCreate, TagGroupCreate
from app.schemas.video_auto_tag import UploadedFileTagRevisionCreateRequest, VideoAutoTagStartRequest
from app.services.video_auto_tag_service import video_auto_tag_service
from app.tests.factories import create_admin, create_uploaded_file, create_user


def _create_video_ai_config(db_session, *, name: str = "auto-tag-config") -> AIConfig:
    """创建可用于自动打标的 AI 配置。"""
    config = AIConfig(
        name=name,
        provider="custom",
        api_key="plain-api-key",
        api_base="https://example.com/chat/completions",
        model="qwen3.7-plus",
        max_tokens=1200,
        temperature=0.2,
        is_active=True,
    )
    db_session.add(config)
    db_session.commit()
    db_session.refresh(config)
    return config


def test_start_video_auto_tag_task_creates_pending_task(
    db_session,
    temp_upload_dir: Path,
) -> None:
    """启动自动打标时应创建待处理任务并保存生成的提示词。"""
    admin = create_admin(db_session, email="auto-tag-admin@example.com")
    owner = create_user(db_session, email="auto-tag-owner@example.com")
    video_path = temp_upload_dir / "auto-tag-source.mp4"
    video_path.write_bytes(b"fake-video-content")

    uploaded_file = create_uploaded_file(
        db_session,
        user=owner,
        original_filename="auto-tag-source.mp4",
        saved_filename="auto-tag-source.mp4",
        file_path=video_path,
        file_size=video_path.stat().st_size,
    )
    ai_config = _create_video_ai_config(db_session)

    tag_group_resp = create_tag_group(
        tag_group_data=TagGroupCreate(
            name="内容类型",
            description="自动打标测试标签组",
            tags=[TagCreate(name="教育", color="#3B82F6")],
        ),
        current_user=admin,
        db=db_session,
    )

    request = VideoAutoTagStartRequest(
        video_file_id=uploaded_file.id,
        ai_config_id=ai_config.id,
        tag_group_ids=[tag_group_resp.data.id],
        transmission_method="url",
    )

    response = start_video_auto_tag_task(
        request=request,
        background_tasks=BackgroundTasks(),
        current_user=owner,
        db=db_session,
    )

    task = db_session.query(VideoAutoTagTask).filter(VideoAutoTagTask.id == response.data.task_id).first()

    assert response.code == 200
    assert task is not None
    assert task.status == "pending"
    assert task.video_file_id == uploaded_file.id
    assert task.ai_config_id == ai_config.id
    assert task.tag_group_ids == [tag_group_resp.data.id]
    assert task.prompt_content is not None
    assert "JSON" in task.prompt_content
    assert "教育" in task.prompt_content


@pytest.mark.asyncio
async def test_process_video_auto_tag_task_persists_items_and_effective_tags(
    db_session,
    temp_upload_dir: Path,
    monkeypatch,
) -> None:
    """自动打标处理完成后应保存命中项并同步当前有效标签。"""
    admin = create_admin(db_session, email="auto-tag-admin-process@example.com")
    owner = create_user(db_session, email="auto-tag-owner-process@example.com")
    video_path = temp_upload_dir / "auto-tag-process.mp4"
    video_path.write_bytes(b"fake-video-content")

    uploaded_file = create_uploaded_file(
        db_session,
        user=owner,
        original_filename="auto-tag-process.mp4",
        saved_filename="auto-tag-process.mp4",
        file_path=video_path,
        file_size=video_path.stat().st_size,
    )
    ai_config = _create_video_ai_config(db_session, name="auto-tag-process-config")

    tag_group_resp = create_tag_group(
        tag_group_data=TagGroupCreate(
            name="商业属性",
            description="自动打标处理标签组",
            tags=[TagCreate(name="商业", color="#EF4444")],
        ),
        current_user=admin,
        db=db_session,
    )

    start_resp = start_video_auto_tag_task(
        request=VideoAutoTagStartRequest(
            video_file_id=uploaded_file.id,
            ai_config_id=ai_config.id,
            tag_group_ids=[tag_group_resp.data.id],
            transmission_method="url",
        ),
        background_tasks=BackgroundTasks(),
        current_user=owner,
        db=db_session,
    )

    async def fake_call_structured_tagging_api(*_args, **_kwargs):
        return {
            "raw_response_text": '{"summary":{"overview":"测试摘要"},"library_tags":[{"tag_group_tag_id":1,"tag_name":"商业","confidence":0.96,"reason":"包含商业导向表达","evidence":{"text":"商业合作","start_seconds":1.5,"end_seconds":3.0}}],"free_tags":[{"tag_name":"品牌曝光","confidence":0.88,"reason":"品牌标识明显","evidence":{"text":"LOGO展示","start_seconds":4.0,"end_seconds":6.5}}]}',
            "structured_payload": {
                "summary": {"overview": "测试摘要"},
                "library_tags": [
                    {
                        "tag_group_tag_id": 1,
                        "tag_name": "商业",
                        "confidence": 0.96,
                        "reason": "包含商业导向表达",
                        "evidence": {
                            "text": "商业合作",
                            "start_seconds": 1.5,
                            "end_seconds": 3.0,
                        },
                    }
                ],
                "free_tags": [
                    {
                        "tag_name": "品牌曝光",
                        "confidence": 0.88,
                        "reason": "品牌标识明显",
                        "evidence": {
                            "text": "LOGO展示",
                            "start_seconds": 4.0,
                            "end_seconds": 6.5,
                        },
                    }
                ],
            },
            "request_payload_summary": {"model": ai_config.model},
            "token_usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
            "cost_estimate": 0.12,
        }

    monkeypatch.setattr(video_auto_tag_service, "_call_structured_tagging_api", fake_call_structured_tagging_api)
    monkeypatch.setattr("app.core.config.Settings.get_base_url", lambda self: "http://example.com")
    monkeypatch.setattr(
        "app.services.video_auto_tag_service.create_media_access_token",
        lambda subject, saved_filename: f"token-{subject}-{saved_filename}",
    )

    await video_auto_tag_service.process_task(start_resp.data.task_id, db_session)

    task = db_session.query(VideoAutoTagTask).filter(VideoAutoTagTask.id == start_resp.data.task_id).first()
    task_items = (
        db_session.query(VideoAutoTagItem)
        .filter(VideoAutoTagItem.task_id == task.id)
        .order_by(VideoAutoTagItem.id.asc())
        .all()
    )
    effective_tags = (
        db_session.query(UploadedFileTag)
        .filter(UploadedFileTag.video_file_id == uploaded_file.id, UploadedFileTag.is_effective == True)
        .order_by(UploadedFileTag.id.asc())
        .all()
    )

    assert task is not None
    assert task.status == "completed"
    assert task.structured_summary == {"overview": "测试摘要"}
    assert task.token_usage == {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150}
    assert len(task_items) == 2
    assert {item.tag_name for item in task_items} == {"商业", "品牌曝光"}
    assert len(effective_tags) == 2
    assert {item.tag_name_snapshot for item in effective_tags} == {"商业", "品牌曝光"}
    assert db_session.query(Tag).filter(Tag.name == "品牌曝光").first() is not None


@pytest.mark.asyncio
async def test_get_uploaded_file_tags_returns_effective_tags(
    db_session,
    temp_upload_dir: Path,
    monkeypatch,
) -> None:
    """查询视频当前有效标签时应返回自动打标同步后的结果。"""
    admin = create_admin(db_session, email="auto-tag-admin-read@example.com")
    owner = create_user(db_session, email="auto-tag-owner-read@example.com")
    video_path = temp_upload_dir / "auto-tag-read.mp4"
    video_path.write_bytes(b"fake-video-content")

    uploaded_file = create_uploaded_file(
        db_session,
        user=owner,
        original_filename="auto-tag-read.mp4",
        saved_filename="auto-tag-read.mp4",
        file_path=video_path,
        file_size=video_path.stat().st_size,
    )
    ai_config = _create_video_ai_config(db_session, name="auto-tag-read-config")

    tag_group_resp = create_tag_group(
        tag_group_data=TagGroupCreate(
            name="内容风格",
            description="当前标签读取测试",
            tags=[TagCreate(name="正式", color="#6B7280")],
        ),
        current_user=admin,
        db=db_session,
    )

    start_resp = start_video_auto_tag_task(
        request=VideoAutoTagStartRequest(
            video_file_id=uploaded_file.id,
            ai_config_id=ai_config.id,
            tag_group_ids=[tag_group_resp.data.id],
            transmission_method="url",
        ),
        background_tasks=BackgroundTasks(),
        current_user=owner,
        db=db_session,
    )

    async def fake_call_structured_tagging_api(*_args, **_kwargs):
        return {
            "raw_response_text": '{"summary":{"overview":"测试摘要"},"library_tags":[{"tag_group_tag_id":1,"tag_name":"正式","confidence":0.91,"reason":"旁白与画面稳定","evidence":{"text":"稳定讲解","start_seconds":2.0,"end_seconds":5.0}}],"free_tags":[]}',
            "structured_payload": {
                "summary": {"overview": "测试摘要"},
                "library_tags": [
                    {
                        "tag_group_tag_id": 1,
                        "tag_name": "正式",
                        "confidence": 0.91,
                        "reason": "旁白与画面稳定",
                        "evidence": {
                            "text": "稳定讲解",
                            "start_seconds": 2.0,
                            "end_seconds": 5.0,
                        },
                    }
                ],
                "free_tags": [],
            },
            "request_payload_summary": {"model": ai_config.model},
            "token_usage": {"prompt_tokens": 80, "completion_tokens": 30, "total_tokens": 110},
            "cost_estimate": 0.05,
        }

    monkeypatch.setattr(video_auto_tag_service, "_call_structured_tagging_api", fake_call_structured_tagging_api)
    monkeypatch.setattr("app.core.config.Settings.get_base_url", lambda self: "http://example.com")
    monkeypatch.setattr(
        "app.services.video_auto_tag_service.create_media_access_token",
        lambda subject, saved_filename: f"token-{subject}-{saved_filename}",
    )

    await video_auto_tag_service.process_task(start_resp.data.task_id, db_session)

    response = get_uploaded_file_tags(
        video_file_id=uploaded_file.id,
        current_user=owner,
        db=db_session,
    )

    assert response.code == 200
    assert response.data is not None
    assert len(response.data) == 1
    assert response.data[0].tag_name == "正式"
    assert response.data[0].source == "ai_auto"
    assert response.data[0].sources == ["ai_auto"]


@pytest.mark.asyncio
async def test_create_uploaded_file_tag_revision_creates_history_and_rebuilds_effective_tags(
    db_session,
    temp_upload_dir: Path,
    monkeypatch,
) -> None:
    """人工修订后应生成新版本，并重建当前有效标签。"""
    admin = create_admin(db_session, email="auto-tag-admin-revision@example.com")
    owner = create_user(db_session, email="auto-tag-owner-revision@example.com")
    video_path = temp_upload_dir / "auto-tag-revision.mp4"
    video_path.write_bytes(b"fake-video-content")

    uploaded_file = create_uploaded_file(
        db_session,
        user=owner,
        original_filename="auto-tag-revision.mp4",
        saved_filename="auto-tag-revision.mp4",
        file_path=video_path,
        file_size=video_path.stat().st_size,
    )
    ai_config = _create_video_ai_config(db_session, name="auto-tag-revision-config")

    tag_group_resp = create_tag_group(
        tag_group_data=TagGroupCreate(
            name="气质风格",
            description="标签修订测试",
            tags=[TagCreate(name="专业", color="#111827")],
        ),
        current_user=admin,
        db=db_session,
    )

    start_resp = start_video_auto_tag_task(
        request=VideoAutoTagStartRequest(
            video_file_id=uploaded_file.id,
            ai_config_id=ai_config.id,
            tag_group_ids=[tag_group_resp.data.id],
            transmission_method="url",
        ),
        background_tasks=BackgroundTasks(),
        current_user=owner,
        db=db_session,
    )

    async def fake_call_structured_tagging_api(*_args, **_kwargs):
        return {
            "raw_response_text": '{"summary":{"overview":"测试摘要"},"library_tags":[{"tag_group_tag_id":1,"tag_name":"专业","confidence":0.90,"reason":"画面专业","evidence":{"text":"专业镜头","start_seconds":1.0,"end_seconds":2.5}}],"free_tags":[]}',
            "structured_payload": {
                "summary": {"overview": "测试摘要"},
                "library_tags": [
                    {
                        "tag_group_tag_id": 1,
                        "tag_name": "专业",
                        "confidence": 0.90,
                        "reason": "画面专业",
                        "evidence": {"text": "专业镜头", "start_seconds": 1.0, "end_seconds": 2.5},
                    }
                ],
                "free_tags": [],
            },
            "request_payload_summary": {"model": ai_config.model},
            "token_usage": {"prompt_tokens": 80, "completion_tokens": 30, "total_tokens": 110},
            "cost_estimate": 0.05,
        }

    monkeypatch.setattr(video_auto_tag_service, "_call_structured_tagging_api", fake_call_structured_tagging_api)
    monkeypatch.setattr("app.core.config.Settings.get_base_url", lambda self: "http://example.com")
    monkeypatch.setattr(
        "app.services.video_auto_tag_service.create_media_access_token",
        lambda subject, saved_filename: f"token-{subject}-{saved_filename}",
    )

    await video_auto_tag_service.process_task(start_resp.data.task_id, db_session)

    revision_response = create_uploaded_file_tag_revision(
        video_file_id=uploaded_file.id,
        request=UploadedFileTagRevisionCreateRequest(
            change_reason="人工补充内容导向标签",
            operations=[
                {"action": "remove", "tag_name": "专业"},
                {"action": "add", "tag_name": "教程", "confidence": 0.95, "note": "人工确认"},
            ],
        ),
        current_user=owner,
        db=db_session,
    )

    revisions = get_uploaded_file_tag_revisions(
        video_file_id=uploaded_file.id,
        current_user=owner,
        db=db_session,
    )
    revision_detail = get_uploaded_file_tag_revision_detail(
        video_file_id=uploaded_file.id,
        revision_id=revision_response.data.id,
        current_user=owner,
        db=db_session,
    )
    effective_tags = get_uploaded_file_tags(
        video_file_id=uploaded_file.id,
        current_user=owner,
        db=db_session,
    )

    assert revision_response.code == 200
    assert revisions.code == 200
    assert len(revisions.data) == 1
    assert revision_detail.code == 200
    assert len(revision_detail.data.items) == 2
    assert effective_tags.code == 200
    assert len(effective_tags.data) == 2
    result_by_name = {item.tag_name: item for item in effective_tags.data}
    assert result_by_name["教程"].is_effective is True
    assert result_by_name["教程"].source == "manual_override"
    assert set(result_by_name["教程"].sources) == {"manual_override"}
    assert result_by_name["专业"].is_effective is False
    assert "ai_auto" in set(result_by_name["专业"].sources)

    revision_row = (
        db_session.query(UploadedFileTagRevision)
        .filter(UploadedFileTagRevision.id == revision_response.data.id)
        .first()
    )
    revision_items = (
        db_session.query(UploadedFileTagRevisionItem)
        .filter(UploadedFileTagRevisionItem.revision_id == revision_response.data.id)
        .all()
    )

    assert revision_row is not None
    assert revision_row.revision_number == 1
    assert len(revision_items) == 2


@pytest.mark.asyncio
async def test_get_uploaded_file_tags_returns_history_collection_with_effective_flags(
    db_session,
    temp_upload_dir: Path,
    monkeypatch,
) -> None:
    """历史标签集合应保留所有出现过的标签，并区分当前是否生效。"""
    admin = create_admin(db_session, email="auto-tag-admin-history-collection@example.com")
    owner = create_user(db_session, email="auto-tag-owner-history-collection@example.com")
    video_path = temp_upload_dir / "auto-tag-history-collection.mp4"
    video_path.write_bytes(b"fake-video-content")

    uploaded_file = create_uploaded_file(
        db_session,
        user=owner,
        original_filename="auto-tag-history-collection.mp4",
        saved_filename="auto-tag-history-collection.mp4",
        file_path=video_path,
        file_size=video_path.stat().st_size,
    )
    ai_config = _create_video_ai_config(db_session, name="auto-tag-history-collection-config")

    tag_group_resp = create_tag_group(
        tag_group_data=TagGroupCreate(
            name="历史集合标签组",
            description="历史标签集合测试",
            tags=[TagCreate(name="专业", color="#111827")],
        ),
        current_user=admin,
        db=db_session,
    )

    start_resp = start_video_auto_tag_task(
        request=VideoAutoTagStartRequest(
            video_file_id=uploaded_file.id,
            ai_config_id=ai_config.id,
            tag_group_ids=[tag_group_resp.data.id],
            transmission_method="url",
        ),
        background_tasks=BackgroundTasks(),
        current_user=owner,
        db=db_session,
    )

    async def fake_call_structured_tagging_api(*_args, **_kwargs):
        return {
            "raw_response_text": '{"summary":{"overview":"测试摘要"},"library_tags":[{"tag_group_tag_id":1,"tag_name":"专业","confidence":0.90,"reason":"画面专业","evidence":{"text":"专业镜头","start_seconds":1.0,"end_seconds":2.5}}],"free_tags":[{"tag_name":"教程","confidence":0.72,"reason":"有教学表达","evidence":{"text":"步骤演示","start_seconds":3.0,"end_seconds":5.0}}]}',
            "structured_payload": {
                "summary": {"overview": "测试摘要"},
                "library_tags": [
                    {
                        "tag_group_tag_id": 1,
                        "tag_name": "专业",
                        "confidence": 0.90,
                        "reason": "画面专业",
                        "evidence": {"text": "专业镜头", "start_seconds": 1.0, "end_seconds": 2.5},
                    }
                ],
                "free_tags": [
                    {
                        "tag_name": "教程",
                        "confidence": 0.72,
                        "reason": "有教学表达",
                        "evidence": {"text": "步骤演示", "start_seconds": 3.0, "end_seconds": 5.0},
                    }
                ],
            },
            "request_payload_summary": {"model": ai_config.model},
            "token_usage": {"prompt_tokens": 80, "completion_tokens": 30, "total_tokens": 110},
            "cost_estimate": 0.05,
        }

    monkeypatch.setattr(video_auto_tag_service, "_call_structured_tagging_api", fake_call_structured_tagging_api)
    monkeypatch.setattr("app.core.config.Settings.get_base_url", lambda self: "http://example.com")
    monkeypatch.setattr(
        "app.services.video_auto_tag_service.create_media_access_token",
        lambda subject, saved_filename: f"token-{subject}-{saved_filename}",
    )

    await video_auto_tag_service.process_task(start_resp.data.task_id, db_session)

    create_uploaded_file_tag_revision(
        video_file_id=uploaded_file.id,
        request=UploadedFileTagRevisionCreateRequest(
            change_reason="移除当前专业标签",
            operations=[
                {"action": "remove", "tag_name": "专业"},
            ],
        ),
        current_user=owner,
        db=db_session,
    )

    response = get_uploaded_file_tags(
        video_file_id=uploaded_file.id,
        current_user=owner,
        db=db_session,
    )

    assert response.code == 200
    assert response.data is not None
    result_by_name = {item.tag_name: item for item in response.data}
    assert set(result_by_name.keys()) == {"专业", "教程"}
    assert result_by_name["专业"].is_effective is False
    assert result_by_name["专业"].confidence == pytest.approx(0.90)
    assert result_by_name["教程"].is_effective is True
    assert result_by_name["教程"].confidence == pytest.approx(0.72)
    assert result_by_name["教程"].source == "ai_auto"


@pytest.mark.asyncio
async def test_list_video_auto_tag_tasks_returns_history_in_desc_order(
    db_session,
    temp_upload_dir: Path,
    monkeypatch,
) -> None:
    """同一视频多次自动打标后，应能查看按时间倒序排列的任务历史。"""
    admin = create_admin(db_session, email="auto-tag-admin-history@example.com")
    owner = create_user(db_session, email="auto-tag-owner-history@example.com")
    video_path = temp_upload_dir / "auto-tag-history.mp4"
    video_path.write_bytes(b"fake-video-content")

    uploaded_file = create_uploaded_file(
        db_session,
        user=owner,
        original_filename="auto-tag-history.mp4",
        saved_filename="auto-tag-history.mp4",
        file_path=video_path,
        file_size=video_path.stat().st_size,
    )
    ai_config = _create_video_ai_config(db_session, name="auto-tag-history-config")

    tag_group_resp = create_tag_group(
        tag_group_data=TagGroupCreate(
            name="历史标签组",
            description="自动打标历史测试",
            tags=[TagCreate(name="品牌", color="#111827")],
        ),
        current_user=admin,
        db=db_session,
    )

    responses = [
        {
            "raw_response_text": '{"summary":{"overview":"第一次摘要"},"library_tags":[{"tag_group_tag_id":1,"tag_name":"品牌","confidence":0.91,"reason":"第一次","evidence":{"text":"第一次证据","start_seconds":1.0,"end_seconds":2.0}}],"free_tags":[]}',
            "structured_payload": {
                "summary": {"overview": "第一次摘要"},
                "library_tags": [
                    {
                        "tag_group_tag_id": 1,
                        "tag_name": "品牌",
                        "confidence": 0.91,
                        "reason": "第一次",
                        "evidence": {"text": "第一次证据", "start_seconds": 1.0, "end_seconds": 2.0},
                    }
                ],
                "free_tags": [],
            },
            "request_payload_summary": {"model": ai_config.model},
            "token_usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
            "cost_estimate": 0.01,
        },
        {
            "raw_response_text": '{"summary":{"overview":"第二次摘要"},"library_tags":[{"tag_group_tag_id":1,"tag_name":"品牌","confidence":0.95,"reason":"第二次","evidence":{"text":"第二次证据","start_seconds":2.0,"end_seconds":4.0}}],"free_tags":[]}',
            "structured_payload": {
                "summary": {"overview": "第二次摘要"},
                "library_tags": [
                    {
                        "tag_group_tag_id": 1,
                        "tag_name": "品牌",
                        "confidence": 0.95,
                        "reason": "第二次",
                        "evidence": {"text": "第二次证据", "start_seconds": 2.0, "end_seconds": 4.0},
                    }
                ],
                "free_tags": [],
            },
            "request_payload_summary": {"model": ai_config.model},
            "token_usage": {"prompt_tokens": 12, "completion_tokens": 6, "total_tokens": 18},
            "cost_estimate": 0.02,
        },
    ]

    async def fake_call_structured_tagging_api(*_args, **_kwargs):
        return responses.pop(0)

    monkeypatch.setattr(video_auto_tag_service, "_call_structured_tagging_api", fake_call_structured_tagging_api)
    monkeypatch.setattr("app.core.config.Settings.get_base_url", lambda self: "http://example.com")
    monkeypatch.setattr(
        "app.services.video_auto_tag_service.create_media_access_token",
        lambda subject, saved_filename: f"token-{subject}-{saved_filename}",
    )

    first_task = start_video_auto_tag_task(
        request=VideoAutoTagStartRequest(
            video_file_id=uploaded_file.id,
            ai_config_id=ai_config.id,
            tag_group_ids=[tag_group_resp.data.id],
            transmission_method="url",
        ),
        background_tasks=BackgroundTasks(),
        current_user=owner,
        db=db_session,
    )
    await video_auto_tag_service.process_task(first_task.data.task_id, db_session)

    second_task = start_video_auto_tag_task(
        request=VideoAutoTagStartRequest(
            video_file_id=uploaded_file.id,
            ai_config_id=ai_config.id,
            tag_group_ids=[tag_group_resp.data.id],
            transmission_method="url",
        ),
        background_tasks=BackgroundTasks(),
        current_user=owner,
        db=db_session,
    )
    await video_auto_tag_service.process_task(second_task.data.task_id, db_session)

    response = list_video_auto_tag_tasks(
        video_file_id=uploaded_file.id,
        current_user=owner,
        db=db_session,
    )

    assert response.code == 200
    assert response.data is not None
    assert len(response.data) == 2
    assert [item.id for item in response.data] == [second_task.data.task_id, first_task.data.task_id]
    assert response.data[0].structured_summary == {"overview": "第二次摘要"}
    assert response.data[1].structured_summary == {"overview": "第一次摘要"}
