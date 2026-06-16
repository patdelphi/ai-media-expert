"""视频解析历史列表字段测试

确保解析历史列表接口会返回用于前端展示的性能与模型信息字段，
避免前端只能展示占位的“置信度”。
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from app.api.v1.endpoints.video_analysis import get_analysis_history
from app.models.video import AIConfig
from app.models.video_analysis import VideoAnalysis
from app.schemas.common import PaginationParams
from app.tests.factories import create_uploaded_file, create_user


def test_get_analysis_history_returns_model_and_token_fields(
    db_session,
    temp_upload_dir: Path,
) -> None:
    user = create_user(db_session, email="analysis-history@example.com")
    video_path = temp_upload_dir / "analysis-history.mp4"
    video_path.write_bytes(b"fake-video-content")

    uploaded_file = create_uploaded_file(
        db_session,
        user=user,
        original_filename="analysis-history.mp4",
        saved_filename="analysis-history.mp4",
        file_path=video_path,
        file_size=video_path.stat().st_size,
    )

    ai_config = AIConfig(
        name="history-config",
        provider="openai",
        api_key="test-key",
        model="gpt-4o-mini",
        is_active=True,
    )
    db_session.add(ai_config)
    db_session.commit()
    db_session.refresh(ai_config)

    analysis = VideoAnalysis(
        user_id=str(user.id),
        video_file_id=uploaded_file.id,
        template_id=None,
        tag_group_ids=None,
        prompt_content="test-prompt",
        video_url="http://example.com/video.mp4",
        transmission_method="url",
        ai_config_id=ai_config.id,
        status="completed",
        progress=100,
        result_summary="summary",
        confidence_score=0.85,
        processing_time=12.5,
        prompt_tokens=100,
        completion_tokens=200,
        total_tokens=300,
        model_name="gpt-4o-mini",
        api_provider="openai",
        completed_at=datetime.now(timezone.utc),
    )
    db_session.add(analysis)
    db_session.commit()

    response = get_analysis_history(
        pagination=PaginationParams(page=1, size=20),
        status_filter=None,
        db=db_session,
    )

    assert response.code == 200
    assert response.data is not None
    assert response.data.total == 1
    assert len(response.data.items) == 1

    item = response.data.items[0]
    assert item.processing_time == 12.5
    assert item.model_name == "gpt-4o-mini"
    assert item.api_provider == "openai"
    assert item.prompt_tokens == 100
    assert item.completion_tokens == 200
    assert item.total_tokens == 300


def test_get_analysis_result_returns_debug_fields(
    db_session,
    temp_upload_dir: Path,
) -> None:
    from app.api.v1.endpoints.video_analysis import get_analysis_result

    user = create_user(db_session, email="analysis-detail@example.com")
    video_path = temp_upload_dir / "analysis-detail.mp4"
    video_path.write_bytes(b"fake-video-content")

    uploaded_file = create_uploaded_file(
        db_session,
        user=user,
        original_filename="analysis-detail.mp4",
        saved_filename="analysis-detail.mp4",
        file_path=video_path,
        file_size=video_path.stat().st_size,
    )

    ai_config = AIConfig(
        name="detail-config",
        provider="openai",
        api_key="test-key",
        model="gpt-4o-mini",
        is_active=True,
    )
    db_session.add(ai_config)
    db_session.commit()
    db_session.refresh(ai_config)

    now = datetime.now(timezone.utc)
    analysis = VideoAnalysis(
        user_id=str(user.id),
        video_file_id=uploaded_file.id,
        template_id=None,
        tag_group_ids=None,
        prompt_content="test-prompt",
        video_url="http://example.com/video.mp4",
        transmission_method="url",
        ai_config_id=ai_config.id,
        status="completed",
        progress=100,
        result_summary="summary",
        processing_time=12.5,
        api_call_time=now,
        api_response_time=now,
        api_duration=3.2,
        prompt_tokens=100,
        completion_tokens=200,
        total_tokens=300,
        temperature=0.7,
        max_tokens=4096,
        model_name="gpt-4o-mini",
        api_provider="openai",
        request_id="req_test_123",
        debug_info={"stage": "completed"},
        completed_at=now,
    )
    db_session.add(analysis)
    db_session.commit()
    db_session.refresh(analysis)

    response = get_analysis_result(analysis.id, db=db_session)

    assert response.code == 200
    assert response.data is not None
    assert response.data.api_duration == 3.2
    assert response.data.prompt_tokens == 100
    assert response.data.completion_tokens == 200
    assert response.data.total_tokens == 300
    assert response.data.model_name == "gpt-4o-mini"
    assert response.data.api_provider == "openai"
    assert response.data.request_id == "req_test_123"
    assert response.data.api_call_time is not None
    assert response.data.api_response_time is not None
    assert response.data.api_call_time.replace(tzinfo=timezone.utc) == now
    assert response.data.api_response_time.replace(tzinfo=timezone.utc) == now
