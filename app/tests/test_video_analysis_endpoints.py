"""视频解析接口测试

验证解析任务创建时会继承所选视频的归属用户，避免写库时触发
`video_analyses.user_id` 为空的数据库约束错误。
"""

from __future__ import annotations

from pathlib import Path
from typing import AsyncGenerator

import pytest
from fastapi import BackgroundTasks

from app.api.v1.endpoints.video_analysis import process_video_analysis, start_video_analysis
from app.models.video import AIConfig, Tag
from app.models.video_auto_tag import UploadedFileTag, VideoAutoTagTask
from app.models.video_analysis import VideoAnalysis
from app.services.ai_service import ai_service
from app.schemas.video_analysis import AnalysisStartRequest
from app.tests.factories import create_uploaded_file, create_user


def test_start_video_analysis_uses_video_owner_as_analysis_user(
    db_session,
    temp_upload_dir: Path,
) -> None:
    """启动解析任务时应写入视频归属用户，避免 user_id 为空。"""
    user = create_user(db_session, email="analysis-owner@example.com")
    video_path = temp_upload_dir / "analysis-source.mp4"
    video_path.write_bytes(b"fake-video-content")

    uploaded_file = create_uploaded_file(
        db_session,
        user=user,
        original_filename="analysis-source.mp4",
        saved_filename="analysis-source.mp4",
        file_path=video_path,
        file_size=video_path.stat().st_size,
    )

    ai_config = AIConfig(
        name="test-config",
        provider="openai",
        api_key="test-key",
        model="gpt-4o-mini",
        is_active=True,
    )
    db_session.add(ai_config)
    db_session.commit()
    db_session.refresh(ai_config)

    request = AnalysisStartRequest(
        video_file_id=uploaded_file.id,
        ai_config_id=ai_config.id,
        transmission_method="url",
    )

    response = start_video_analysis(
        request=request,
        background_tasks=BackgroundTasks(),
        db=db_session,
    )

    analysis = db_session.query(VideoAnalysis).filter(VideoAnalysis.id == response.data.analysis_id).first()

    assert analysis is not None
    assert str(analysis.user_id) == str(uploaded_file.user_id)
    assert analysis.video_file_id == uploaded_file.id


@pytest.mark.asyncio
async def test_process_video_analysis_generates_runtime_video_url_for_mimo(
    db_session,
    temp_upload_dir: Path,
    monkeypatch,
) -> None:
    """Mimo 视频模型应走视频理解分支，并生成运行时视频 URL。"""
    user = create_user(db_session, email="mimo-analysis-owner@example.com")
    video_path = temp_upload_dir / "mimo-source.mp4"
    video_path.write_bytes(b"fake-video-content")

    uploaded_file = create_uploaded_file(
        db_session,
        user=user,
        original_filename="mimo-source.mp4",
        saved_filename="mimo-source.mp4",
        file_path=video_path,
        file_size=video_path.stat().st_size,
    )

    ai_config = AIConfig(
        name="mimo-config",
        provider="custom",
        api_key="test-key",
        api_base="https://example.com/chat/completions",
        model="mimo-v2.5",
        is_active=True,
    )
    db_session.add(ai_config)
    db_session.commit()
    db_session.refresh(ai_config)

    analysis = VideoAnalysis(
        user_id=str(user.id),
        video_file_id=uploaded_file.id,
        prompt_content="请分析视频内容",
        ai_config_id=ai_config.id,
        status="pending",
        progress=0,
    )
    db_session.add(analysis)
    db_session.commit()
    db_session.refresh(analysis)

    async def fake_call_ai_api(*args, **kwargs) -> AsyncGenerator[str, None]:
        yield "ok"

    monkeypatch.setattr(ai_service, "call_ai_api", fake_call_ai_api)
    monkeypatch.setattr("app.core.config.Settings.get_base_url", lambda self: "http://example.com")

    await process_video_analysis(analysis.id, db_session)
    db_session.refresh(analysis)

    assert analysis.status == "completed"
    assert analysis.video_url == "http://example.com/api/v1/files/stream/mimo-source.mp4"
    assert analysis.runtime_video_url is not None
    assert analysis.runtime_video_url.startswith("http://example.com/api/v1/files/stream/mimo-source.mp4?token=")


@pytest.mark.asyncio
async def test_process_video_analysis_generates_runtime_video_url_for_qwen_video_model(
    db_session,
    temp_upload_dir: Path,
    monkeypatch,
) -> None:
    """Qwen 视频模型应走视频理解分支，并生成运行时视频 URL。"""
    user = create_user(db_session, email="qwen-analysis-owner@example.com")
    video_path = temp_upload_dir / "qwen-source.mp4"
    video_path.write_bytes(b"fake-video-content")

    uploaded_file = create_uploaded_file(
        db_session,
        user=user,
        original_filename="qwen-source.mp4",
        saved_filename="qwen-source.mp4",
        file_path=video_path,
        file_size=video_path.stat().st_size,
    )

    ai_config = AIConfig(
        name="qwen-config",
        provider="custom",
        api_key="test-key",
        api_base="https://example.com/chat/completions",
        model="qwen3.7-plus",
        is_active=True,
    )
    db_session.add(ai_config)
    db_session.commit()
    db_session.refresh(ai_config)

    analysis = VideoAnalysis(
        user_id=str(user.id),
        video_file_id=uploaded_file.id,
        prompt_content="请分析视频内容",
        ai_config_id=ai_config.id,
        status="pending",
        progress=0,
    )
    db_session.add(analysis)
    db_session.commit()
    db_session.refresh(analysis)

    async def fake_call_ai_api(*args, **kwargs) -> AsyncGenerator[str, None]:
        yield "ok"

    monkeypatch.setattr(ai_service, "call_ai_api", fake_call_ai_api)
    monkeypatch.setattr("app.core.config.Settings.get_base_url", lambda self: "http://example.com")

    await process_video_analysis(analysis.id, db_session)
    db_session.refresh(analysis)

    assert analysis.status == "completed"
    assert analysis.video_url == "http://example.com/api/v1/files/stream/qwen-source.mp4"
    assert analysis.runtime_video_url is not None
    assert analysis.runtime_video_url.startswith("http://example.com/api/v1/files/stream/qwen-source.mp4?token=")


def test_start_video_analysis_reuses_auto_tag_context_by_default(
    db_session,
    temp_upload_dir: Path,
) -> None:
    """模板解析默认应复用当前有效标签和最近一次自动打标摘要。"""
    user = create_user(db_session, email="analysis-auto-tag-context@example.com")
    video_path = temp_upload_dir / "analysis-auto-tag-context.mp4"
    video_path.write_bytes(b"fake-video-content")

    uploaded_file = create_uploaded_file(
        db_session,
        user=user,
        original_filename="analysis-auto-tag-context.mp4",
        saved_filename="analysis-auto-tag-context.mp4",
        file_path=video_path,
        file_size=video_path.stat().st_size,
    )

    ai_config = AIConfig(
        name="analysis-context-config",
        provider="custom",
        api_key="test-key",
        api_base="https://example.com/chat/completions",
        model="qwen3.7-plus",
        is_active=True,
    )
    db_session.add(ai_config)
    db_session.commit()
    db_session.refresh(ai_config)

    tag = Tag(
        name="品牌曝光",
        category="营销",
        source_type="free_promoted",
        is_active=True,
    )
    db_session.add(tag)
    db_session.commit()
    db_session.refresh(tag)

    auto_tag_task = VideoAutoTagTask(
        user_id=str(user.id),
        video_file_id=uploaded_file.id,
        ai_config_id=ai_config.id,
        prompt_version="auto-tag-v1",
        prompt_content="auto tag prompt",
        transmission_method="url",
        status="completed",
        progress=100,
        structured_summary={"overview": "品牌信息突出，节奏稳定"},
        is_active=True,
    )
    db_session.add(auto_tag_task)
    db_session.commit()
    db_session.refresh(auto_tag_task)

    effective_tag = UploadedFileTag(
        video_file_id=uploaded_file.id,
        tag_id=tag.id,
        tag_name_snapshot="品牌曝光",
        source="ai_auto",
        confidence=0.93,
        auto_tag_task_id=auto_tag_task.id,
        is_effective=True,
        created_by="ai",
    )
    db_session.add(effective_tag)
    db_session.commit()

    response = start_video_analysis(
        request=AnalysisStartRequest(
            video_file_id=uploaded_file.id,
            ai_config_id=ai_config.id,
            custom_prompt="请给出品牌视频分析结论",
            transmission_method="url",
        ),
        background_tasks=BackgroundTasks(),
        db=db_session,
    )

    analysis = db_session.query(VideoAnalysis).filter(VideoAnalysis.id == response.data.analysis_id).first()

    assert analysis is not None
    assert "当前有效标签" in analysis.prompt_content
    assert "品牌曝光" in analysis.prompt_content
    assert "自动打标摘要" in analysis.prompt_content
    assert "品牌信息突出，节奏稳定" in analysis.prompt_content
