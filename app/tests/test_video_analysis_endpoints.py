"""视频解析接口测试

验证解析任务创建时会继承所选视频的归属用户，避免写库时触发
`video_analyses.user_id` 为空的数据库约束错误。
"""

from __future__ import annotations

from pathlib import Path

from fastapi import BackgroundTasks

from app.api.v1.endpoints.video_analysis import start_video_analysis
from app.models.video import AIConfig
from app.models.video_analysis import VideoAnalysis
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
