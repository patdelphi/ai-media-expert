"""基于解析结果生成候选标签测试

覆盖：
- 生成候选标签接口缓存逻辑
- 权限校验
- 采纳候选标签写入 source=ai_assisted
- 标签被排除后历史集合仍保留来源信息
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import HTTPException

from app.api.v1.endpoints.uploaded_file_tags import create_uploaded_file_tag_revision, get_uploaded_file_tags
from app.api.v1.endpoints.video_analysis import generate_analysis_tag_candidates
from app.models.video import AIConfig
from app.models.video_analysis import VideoAnalysis
from app.models.video_auto_tag import UploadedFileTag
from app.schemas.video_auto_tag import UploadedFileTagRevisionCreateRequest, UploadedFileTagRevisionOperation
from app.services.analysis_tagging_service import analysis_tagging_service
from app.tests.factories import create_uploaded_file, create_user


def _create_ai_config(db_session) -> AIConfig:
    ai_config = AIConfig(
        name="analysis-tag-config",
        provider="openai",
        api_key="test-key",
        api_base="https://example.com/chat/completions",
        model="gpt-4o-mini",
        is_active=True,
        temperature=0.7,
        max_tokens=1200,
    )
    db_session.add(ai_config)
    db_session.commit()
    db_session.refresh(ai_config)
    return ai_config


def _create_ai_config_alt(db_session) -> AIConfig:
    ai_config = AIConfig(
        name="analysis-tag-config-alt",
        provider="openai",
        api_key="test-key",
        api_base="https://example.com/chat/completions",
        model="gpt-4o-mini",
        is_active=True,
        temperature=0.7,
        max_tokens=1200,
    )
    db_session.add(ai_config)
    db_session.commit()
    db_session.refresh(ai_config)
    return ai_config


def _create_completed_analysis(db_session, *, user_id: str, video_file_id: int, ai_config_id: int) -> VideoAnalysis:
    analysis = VideoAnalysis(
        user_id=user_id,
        video_file_id=video_file_id,
        prompt_content="prompt",
        ai_config_id=ai_config_id,
        status="completed",
        progress=100,
        analysis_result="这里是一段解析结果文本，用于生成候选标签",
        result_summary="摘要",
        result_metadata=None,
        is_active=True,
    )
    db_session.add(analysis)
    db_session.commit()
    db_session.refresh(analysis)
    return analysis


def test_extract_structured_payload_supports_fenced_json() -> None:
    payload = analysis_tagging_service._extract_structured_payload(
        """下面是结果：

```json
{"tag_candidates":[{"tag_name":"品牌曝光","confidence":0.91,"reason":"品牌多次出现","evidence_start_seconds":null,"evidence_end_seconds":null}]}
```
"""
    )

    assert payload["tag_candidates"][0]["tag_name"] == "品牌曝光"


def test_extract_structured_payload_supports_python_like_json() -> None:
    payload = analysis_tagging_service._extract_structured_payload(
        """这里是候选标签结果：
{
  'tag_candidates': [
    {
      'tag_name': '品牌曝光',
      'confidence': 0.91,
      'reason': '品牌多次出现',
      'evidence_start_seconds': None,
      'evidence_end_seconds': None,
    },
  ],
}
"""
    )

    assert payload["tag_candidates"][0]["tag_name"] == "品牌曝光"


def test_extract_structured_payload_supports_root_array() -> None:
    payload = analysis_tagging_service._extract_structured_payload(
        """候选标签如下：
[
  {"tag_name":"品牌曝光","confidence":0.91,"reason":"品牌多次出现","evidence_start_seconds":null,"evidence_end_seconds":null}
]
"""
    )

    assert payload["tag_candidates"][0]["tag_name"] == "品牌曝光"


def test_extract_structured_payload_supports_stringified_tag_candidates() -> None:
    payload = analysis_tagging_service._extract_structured_payload(
        """这里是候选标签结果：
{"tag_candidates":"[{\\\"tag_name\\\":\\\"品牌曝光\\\",\\\"confidence\\\":0.91,\\\"reason\\\":\\\"品牌多次出现\\\",\\\"evidence_start_seconds\\\":null,\\\"evidence_end_seconds\\\":null}]"}
"""
    )

    assert payload["tag_candidates"][0]["tag_name"] == "品牌曝光"


def test_extract_openai_compatible_text_supports_list_blocks() -> None:
    payload = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": [
                        {"type": "text", "text": "```json\n"},
                        {"type": "text", "text": "{\"tag_candidates\": []}"},
                        {"type": "text", "text": "\n```"},
                    ],
                }
            }
        ]
    }
    assert analysis_tagging_service._extract_openai_compatible_text(payload) == '```json\n{"tag_candidates": []}\n```'


def test_extract_openai_compatible_text_supports_choice_text() -> None:
    payload = {"choices": [{"text": "{\"tag_candidates\": []}"}]}
    assert analysis_tagging_service._extract_openai_compatible_text(payload) == "{\"tag_candidates\": []}"


def test_extract_openai_compatible_text_supports_delta_content() -> None:
    payload = {"choices": [{"delta": {"content": "{\"tag_candidates\": []}"}}]}
    assert analysis_tagging_service._extract_openai_compatible_text(payload) == "{\"tag_candidates\": []}"


def test_extract_openai_compatible_text_supports_reasoning_content() -> None:
    payload = {
        "choices": [
            {
                "finish_reason": "length",
                "message": {
                    "role": "assistant",
                    "content": "",
                    "reasoning_content": "{\"tag_candidates\": []}",
                },
            }
        ]
    }
    assert analysis_tagging_service._extract_openai_compatible_text(payload) == "{\"tag_candidates\": []}"


@pytest.mark.asyncio
async def test_generate_analysis_tag_candidates_caches_result(
    db_session,
    temp_upload_dir: Path,
    monkeypatch,
) -> None:
    owner = create_user(db_session, email="analysis-tag-owner@example.com")
    other = create_user(db_session, email="analysis-tag-other@example.com")
    video_path = temp_upload_dir / "analysis-tag-source.mp4"
    video_path.write_bytes(b"fake-video-content")
    uploaded_file = create_uploaded_file(
        db_session,
        user=owner,
        original_filename="analysis-tag-source.mp4",
        saved_filename="analysis-tag-source.mp4",
        file_path=video_path,
        file_size=video_path.stat().st_size,
    )
    ai_config = _create_ai_config(db_session)
    alt_ai_config = _create_ai_config_alt(db_session)
    analysis = _create_completed_analysis(
        db_session,
        user_id=str(owner.id),
        video_file_id=uploaded_file.id,
        ai_config_id=ai_config.id,
    )

    calls = {"count": 0}

    async def fake_generate(*_args, **_kwargs):
        calls["count"] += 1
        return (
            [
                {
                    "tag_name": "品牌曝光",
                    "confidence": 0.91,
                    "reason": "解析中多次出现品牌露出",
                    "evidence_start_seconds": None,
                    "evidence_end_seconds": None,
                }
            ],
            {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
        )

    monkeypatch.setattr("app.services.analysis_tagging_service.analysis_tagging_service.generate_tag_candidates", fake_generate)

    resp = await generate_analysis_tag_candidates(
        analysis_id=analysis.id,
        force=False,
        ai_config_id=None,
        tag_group_ids=None,
        current_user=owner,
        db=db_session,
    )
    assert resp.code == 200
    assert resp.data.analysis_id == analysis.id
    assert resp.data.video_file_id == uploaded_file.id
    assert resp.data.tag_candidates[0].tag_name == "品牌曝光"

    db_session.refresh(analysis)
    assert analysis.result_metadata is not None
    assert analysis.result_metadata.get("tag_candidates")[0]["tag_name"] == "品牌曝光"
    runs = analysis.result_metadata.get("analysis_tagging_runs")
    assert isinstance(runs, list)
    assert len(runs) == 1
    assert runs[0]["token_usage"]["total_tokens"] == 30
    assert calls["count"] == 1

    cached = await generate_analysis_tag_candidates(
        analysis_id=analysis.id,
        force=False,
        ai_config_id=None,
        tag_group_ids=None,
        current_user=owner,
        db=db_session,
    )
    assert cached.data.tag_candidates[0].tag_name == "品牌曝光"
    db_session.refresh(analysis)
    runs = analysis.result_metadata.get("analysis_tagging_runs")
    assert isinstance(runs, list)
    assert len(runs) == 1
    assert calls["count"] == 1

    override_no_cache = await generate_analysis_tag_candidates(
        analysis_id=analysis.id,
        force=False,
        ai_config_id=alt_ai_config.id,
        tag_group_ids=None,
        current_user=owner,
        db=db_session,
    )
    assert override_no_cache.data.tag_candidates[0].tag_name == "品牌曝光"
    db_session.refresh(analysis)
    runs = analysis.result_metadata.get("analysis_tagging_runs")
    assert isinstance(runs, list)
    assert len(runs) == 2
    assert calls["count"] == 2

    async def fake_generate_second(*_args, **_kwargs):
        calls["count"] += 1
        return (
            [{"tag_name": "教程", "confidence": 0.66, "reason": "偏教程", "evidence_start_seconds": None, "evidence_end_seconds": None}],
            {"prompt_tokens": 1, "completion_tokens": 2, "total_tokens": 3},
        )

    monkeypatch.setattr(
        "app.services.analysis_tagging_service.analysis_tagging_service.generate_tag_candidates",
        fake_generate_second,
    )
    forced = await generate_analysis_tag_candidates(
        analysis_id=analysis.id,
        force=True,
        ai_config_id=None,
        tag_group_ids=None,
        current_user=owner,
        db=db_session,
    )
    assert forced.data.tag_candidates[0].tag_name == "教程"
    db_session.refresh(analysis)
    runs = analysis.result_metadata.get("analysis_tagging_runs")
    assert isinstance(runs, list)
    assert len(runs) == 3
    assert calls["count"] == 3

    with pytest.raises(HTTPException) as exc_info:
        await generate_analysis_tag_candidates(
            analysis_id=analysis.id,
            force=False,
            ai_config_id=None,
            tag_group_ids=None,
            current_user=other,
            db=db_session,
        )
    assert exc_info.value.status_code == 403


def test_accept_analysis_tag_candidate_sets_source_ai_assisted(
    db_session,
    temp_upload_dir: Path,
) -> None:
    owner = create_user(db_session, email="analysis-tag-accept-owner@example.com")
    video_path = temp_upload_dir / "analysis-tag-accept.mp4"
    video_path.write_bytes(b"fake-video-content")
    uploaded_file = create_uploaded_file(
        db_session,
        user=owner,
        original_filename="analysis-tag-accept.mp4",
        saved_filename="analysis-tag-accept.mp4",
        file_path=video_path,
        file_size=video_path.stat().st_size,
    )

    db_session.add(
        UploadedFileTag(
            video_file_id=uploaded_file.id,
            tag_id=None,
            tag_name_snapshot="旧标签",
            source="ai_auto",
            confidence=0.9,
            auto_tag_task_id=None,
            revision_id=None,
            is_effective=True,
            evidence_start_seconds=None,
            evidence_end_seconds=None,
            reason=None,
            created_by="ai",
        )
    )
    db_session.commit()

    create_uploaded_file_tag_revision(
        video_file_id=uploaded_file.id,
        request=UploadedFileTagRevisionCreateRequest(
            change_reason="采纳解析候选标签",
            operations=[
                UploadedFileTagRevisionOperation(
                    action="add",
                    tag_name="品牌曝光",
                    confidence=0.91,
                    note="analysis_id=1",
                    source="ai_assisted",
                )
            ],
        ),
        current_user=owner,
        db=db_session,
    )

    effective_tags = (
        db_session.query(UploadedFileTag)
        .filter(UploadedFileTag.video_file_id == uploaded_file.id, UploadedFileTag.is_effective == True)
        .all()
    )
    assert {tag.tag_name_snapshot for tag in effective_tags} == {"旧标签", "品牌曝光"}
    accepted = next(tag for tag in effective_tags if tag.tag_name_snapshot == "品牌曝光")
    assert accepted.source == "ai_assisted"


def test_excluded_ai_assisted_tag_keeps_source_in_history_collection(
    db_session,
    temp_upload_dir: Path,
) -> None:
    owner = create_user(db_session, email="analysis-tag-exclude-owner@example.com")
    video_path = temp_upload_dir / "analysis-tag-exclude.mp4"
    video_path.write_bytes(b"fake-video-content")
    uploaded_file = create_uploaded_file(
        db_session,
        user=owner,
        original_filename="analysis-tag-exclude.mp4",
        saved_filename="analysis-tag-exclude.mp4",
        file_path=video_path,
        file_size=video_path.stat().st_size,
    )

    db_session.add(
        UploadedFileTag(
            video_file_id=uploaded_file.id,
            tag_id=None,
            tag_name_snapshot="品牌曝光",
            source="ai_assisted",
            confidence=0.91,
            auto_tag_task_id=None,
            revision_id=None,
            is_effective=True,
            evidence_start_seconds=None,
            evidence_end_seconds=None,
            reason=None,
            created_by="ai",
        )
    )
    db_session.commit()

    create_uploaded_file_tag_revision(
        video_file_id=uploaded_file.id,
        request=UploadedFileTagRevisionCreateRequest(
            change_reason="排除标签",
            operations=[UploadedFileTagRevisionOperation(action="remove", tag_name="品牌曝光", note="exclude")],
        ),
        current_user=owner,
        db=db_session,
    )

    resp = get_uploaded_file_tags(
        video_file_id=uploaded_file.id,
        current_user=owner,
        db=db_session,
    )
    entry = next(item for item in resp.data if item.tag_name == "品牌曝光")
    assert entry.is_effective is False
    assert entry.source == "ai_assisted"


def test_history_collection_returns_sources_union_and_max_confidence(
    db_session,
    temp_upload_dir: Path,
) -> None:
    owner = create_user(db_session, email="analysis-tag-sources-owner@example.com")
    video_path = temp_upload_dir / "analysis-tag-sources.mp4"
    video_path.write_bytes(b"fake-video-content")
    uploaded_file = create_uploaded_file(
        db_session,
        user=owner,
        original_filename="analysis-tag-sources.mp4",
        saved_filename="analysis-tag-sources.mp4",
        file_path=video_path,
        file_size=video_path.stat().st_size,
    )

    db_session.add_all(
        [
            UploadedFileTag(
                video_file_id=uploaded_file.id,
                tag_id=None,
                tag_name_snapshot="品牌曝光",
                source="ai_auto",
                confidence=0.55,
                auto_tag_task_id=None,
                revision_id=None,
                is_effective=True,
                evidence_start_seconds=None,
                evidence_end_seconds=None,
                reason=None,
                created_by="ai",
            ),
            UploadedFileTag(
                video_file_id=uploaded_file.id,
                tag_id=None,
                tag_name_snapshot="品牌曝光",
                source="ai_assisted",
                confidence=0.88,
                auto_tag_task_id=None,
                revision_id=None,
                is_effective=False,
                evidence_start_seconds=None,
                evidence_end_seconds=None,
                reason=None,
                created_by="ai",
            ),
        ]
    )
    db_session.commit()

    resp = get_uploaded_file_tags(video_file_id=uploaded_file.id, current_user=owner, db=db_session)
    assert resp.code == 200
    assert resp.data is not None
    entry = next(item for item in resp.data if item.tag_name == "品牌曝光")
    assert entry.is_effective is True
    assert entry.confidence == pytest.approx(0.88)
    assert set(entry.sources or []) == {"ai_auto", "ai_assisted"}
