from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import HTTPException

from app.api.v1.endpoints.video_analysis import get_video_token_summary
from app.models.video_analysis import VideoAnalysis
from app.models.video_auto_tag import VideoAutoTagTask
from app.tests.factories import create_uploaded_file, create_user


def test_get_video_token_summary_aggregates_tokens(
    db_session,
    temp_upload_dir: Path,
) -> None:
    owner = create_user(db_session, email="token-summary-owner@example.com")
    other = create_user(db_session, email="token-summary-other@example.com")

    video_path = temp_upload_dir / "token-summary.mp4"
    video_path.write_bytes(b"fake-video-content")
    uploaded_file = create_uploaded_file(
        db_session,
        user=owner,
        original_filename="token-summary.mp4",
        saved_filename="token-summary.mp4",
        file_path=video_path,
        file_size=video_path.stat().st_size,
    )

    analysis = VideoAnalysis(
        user_id=str(owner.id),
        video_file_id=uploaded_file.id,
        prompt_content="prompt",
        ai_config_id=1,
        status="completed",
        progress=100,
        prompt_tokens=100,
        completion_tokens=200,
        total_tokens=300,
        result_metadata={
            "analysis_tagging_runs": [
                {
                    "token_usage": {"prompt_tokens": 5, "completion_tokens": 6, "total_tokens": 11},
                }
            ]
        },
        is_active=True,
    )
    db_session.add(analysis)

    task = VideoAutoTagTask(
        user_id=str(owner.id),
        video_file_id=uploaded_file.id,
        ai_config_id=1,
        prompt_content="prompt",
        transmission_method="url",
        status="completed",
        progress=100,
        token_usage={"prompt_tokens": 7, "completion_tokens": 8, "total_tokens": 15},
        is_active=True,
    )
    db_session.add(task)
    db_session.commit()

    resp = get_video_token_summary(video_file_id=uploaded_file.id, current_user=owner, db=db_session)
    assert resp.code == 200
    assert resp.data is not None
    assert resp.data.video_file_id == uploaded_file.id
    assert resp.data.analysis.total_tokens == 300
    assert resp.data.auto_tag.total_tokens == 15
    assert resp.data.analysis_derived_tagging.total_tokens == 11
    assert resp.data.total.total_tokens == 326

    with pytest.raises(HTTPException) as exc_info:
        get_video_token_summary(video_file_id=uploaded_file.id, current_user=other, db=db_session)
    assert exc_info.value.status_code == 403

