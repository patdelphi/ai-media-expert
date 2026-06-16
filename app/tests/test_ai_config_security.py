"""AI 配置安全与事务测试

覆盖管理员启停权限，以及异常时的事务回滚。
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.api.v1.ai_config import activate_ai_config, deactivate_ai_config
from app.api.v1.ai_config import get_ai_configs_full
from app.api.v1.ai_config import test_ai_config as run_ai_config_test
from app.models.video import AIConfig
from app.models.video_analysis import VideoAnalysis
from app.schemas.video import AIConfigCreate, AIConfigUpdate
from app.models.user import User
from app.services.ai_service import ai_service
from app.utils.video_base64 import video_base64_encoder
from app.tests.factories import create_admin


def _create_ai_config_record(db: Session, *, name: str, is_active: bool) -> AIConfig:
    record = AIConfig(
        name=name,
        provider="openai",
        api_key="enc:test",
        api_base="https://example.com/v1",
        model="gpt-4o-mini",
        max_tokens=256,
        temperature=0.7,
        is_active=is_active,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@pytest.mark.asyncio
async def test_ai_config_activate_and_deactivate_for_admin(override_db) -> None:
    admin = create_admin(override_db, email="aiconfig-admin@example.com")
    config = _create_ai_config_record(override_db, name="cfg-1", is_active=False)

    activate_resp = await activate_ai_config(config_id=config.id, current_user=admin, db=override_db)
    assert activate_resp.code == 200
    assert config.is_active is True

    deactivate_resp = await deactivate_ai_config(config_id=config.id, current_user=admin, db=override_db)
    assert deactivate_resp.code == 200
    assert config.is_active is False


@pytest.mark.asyncio
async def test_ai_config_activate_rolls_back_on_commit_error() -> None:
    admin = User(email="admin@example.com", hashed_password="x", role="admin", is_active=True)
    config = AIConfig(
        name="cfg-rollback",
        provider="openai",
        api_key="enc:test",
        api_base="https://example.com/v1",
        model="gpt-4o-mini",
        is_active=False,
    )
    config.id = 3

    db = Mock(spec=Session)
    db.query.return_value.filter.return_value.first.return_value = config
    db.commit.side_effect = RuntimeError("db down")

    with pytest.raises(HTTPException) as exc:
        await activate_ai_config(config_id=config.id, current_user=admin, db=db)

    assert exc.value.status_code == 500
    assert db.rollback.called is True


@pytest.mark.asyncio
async def test_ai_config_full_list_masks_invalid_encrypted_key(override_db) -> None:
    admin = create_admin(override_db, email="aiconfig-full@example.com")
    override_db.add(
        AIConfig(
            name="cfg-invalid",
            provider="custom",
            api_key="enc:not-a-valid-fernet-payload",
            api_base="http://example.com",
            model="m",
            max_tokens=10,
            temperature=0.1,
            is_active=True,
        )
    )
    override_db.commit()

    resp = await get_ai_configs_full(include_inactive=False, current_user=admin, db=override_db)
    assert resp.code == 200
    assert resp.data is not None
    assert any(item.name == "cfg-invalid" and item.api_key == "****" for item in resp.data)


@pytest.mark.asyncio
async def test_ai_config_full_list_masks_invalid_upload_api_key(override_db) -> None:
    admin = create_admin(override_db, email="aiconfig-upload-full@example.com")
    override_db.add(
        AIConfig(
            name="cfg-upload-invalid",
            provider="custom",
            api_key="enc:not-a-valid-fernet-payload",
            upload_api_key="enc:not-a-valid-fernet-payload",
            api_base="http://example.com",
            model="qwen3.7-plus",
            max_tokens=10,
            temperature=0.1,
            is_active=True,
        )
    )
    override_db.commit()

    resp = await get_ai_configs_full(include_inactive=False, current_user=admin, db=override_db)
    assert resp.code == 200
    assert resp.data is not None
    assert any(item.name == "cfg-upload-invalid" and item.upload_api_key == "****" for item in resp.data)


@pytest.mark.asyncio
async def test_ai_config_test_returns_hint_when_api_key_cannot_decrypt(override_db) -> None:
    admin = create_admin(override_db, email="aiconfig-test@example.com")
    override_db.add(
        AIConfig(
            name="cfg-test-invalid",
            provider="custom",
            api_key="enc:not-a-valid-fernet-payload",
            api_base="http://example.com",
            model="m",
            max_tokens=10,
            temperature=0.1,
            is_active=True,
        )
    )
    override_db.commit()

    config_id = override_db.query(AIConfig).filter(AIConfig.name == "cfg-test-invalid").first().id
    resp = await run_ai_config_test(config_id=config_id, current_user=admin, db=override_db)
    assert resp.code == 200
    assert resp.data is not None
    assert resp.data.get("success") is False
    assert "无法解密" in resp.data.get("message", "")


@pytest.mark.asyncio
async def test_ai_config_test_uses_raw_api_base_without_appending_path(override_db) -> None:
    admin = create_admin(override_db, email="aiconfig-raw-url@example.com")
    override_db.add(
        AIConfig(
            name="cfg-raw-url",
            provider="custom",
            api_key="plain-test-api-key",
            api_base="https://example.com/custom-endpoint",
            model="qwen-plus",
            max_tokens=10,
            temperature=0.1,
            is_active=True,
        )
    )
    override_db.commit()

    config_id = override_db.query(AIConfig).filter(AIConfig.name == "cfg-raw-url").first().id

    response = Mock(status_code=200)
    response.text = '{"ok": true}'
    client = AsyncMock()
    client.post = AsyncMock(return_value=response)
    client_cm = AsyncMock()
    client_cm.__aenter__.return_value = client
    client_cm.__aexit__.return_value = None

    with patch("httpx.AsyncClient", return_value=client_cm):
        resp = await run_ai_config_test(config_id=config_id, current_user=admin, db=override_db)

    assert resp.code == 200
    assert resp.data is not None
    assert resp.data.get("success") is True
    assert client.post.await_args.args[0] == "https://example.com/custom-endpoint"


@pytest.mark.asyncio
async def test_ai_service_uses_raw_api_base_without_appending_path() -> None:
    ai_config = AIConfig(
        name="cfg-runtime-raw-url",
        provider="custom",
        api_key="plain-test-api-key",
        api_base="https://example.com/raw-chat-endpoint",
        model="qwen-plus",
        max_tokens=32,
        temperature=0.7,
        is_active=True,
    )
    analysis = VideoAnalysis(
        user_id="1",
        video_file_id=1,
        prompt_content="分析测试",
        ai_config_id=1,
        status="processing",
        progress=0,
    )
    analysis.id = 100
    analysis.api_call_time = datetime.now()
    analysis.prompt_tokens = 0

    response = Mock()
    response.status_code = 200
    response.headers = {}
    response.aiter_lines = Mock(return_value=_async_line_iter(["data: [DONE]"]))

    response_cm = AsyncMock()
    response_cm.__aenter__.return_value = response
    response_cm.__aexit__.return_value = None

    client = Mock()
    client.stream.return_value = response_cm

    client_cm = AsyncMock()
    client_cm.__aenter__.return_value = client
    client_cm.__aexit__.return_value = None

    db = Mock(spec=Session)

    with patch("app.services.ai_service.httpx.AsyncClient", return_value=client_cm):
        result = [chunk async for chunk in ai_service._call_openai_compatible_api(ai_config, "hello", analysis, db)]

    assert result == []
    assert client.stream.call_args.args[1] == "https://example.com/raw-chat-endpoint"
    assert analysis.debug_info["api_url"] == "https://example.com/raw-chat-endpoint"


@pytest.mark.asyncio
async def test_ai_service_formats_mimo_video_request_with_video_content() -> None:
    ai_config = AIConfig(
        name="cfg-mimo-video",
        provider="custom",
        api_key="plain-test-api-key",
        api_base="https://example.com/mimo-chat-endpoint",
        model="mimo-v2.5",
        max_tokens=1024,
        temperature=0.7,
        is_active=True,
    )
    analysis = VideoAnalysis(
        user_id="1",
        video_file_id=1,
        prompt_content="分析测试",
        ai_config_id=1,
        status="processing",
        progress=0,
    )
    analysis.id = 101
    analysis.api_call_time = datetime.now()
    analysis.prompt_tokens = 0
    analysis.runtime_video_url = "https://example.com/video.mp4?token=abc"
    analysis.transmission_method = "url"

    response = Mock()
    response.status_code = 200
    response.headers = {}
    response.aiter_lines = Mock(return_value=_async_line_iter(["data: [DONE]"]))

    response_cm = AsyncMock()
    response_cm.__aenter__.return_value = response
    response_cm.__aexit__.return_value = None

    client = Mock()
    client.stream.return_value = response_cm

    client_cm = AsyncMock()
    client_cm.__aenter__.return_value = client
    client_cm.__aexit__.return_value = None

    db = Mock(spec=Session)

    with patch("app.services.ai_service.httpx.AsyncClient", return_value=client_cm):
        result = [chunk async for chunk in ai_service._call_openai_compatible_api(ai_config, "hello mimo", analysis, db)]

    assert result == []
    request_data = client.stream.call_args.kwargs["json"]
    assert request_data["model"] == "mimo-v2.5"
    assert request_data["messages"][0]["content"][0]["type"] == "video_url"
    assert request_data["messages"][0]["content"][0]["video_url"]["url"] == "https://example.com/video.mp4?token=abc"
    assert request_data["messages"][0]["content"][0]["fps"] == 2
    assert request_data["messages"][0]["content"][0]["media_resolution"] == "default"
    assert request_data["messages"][0]["content"][1]["type"] == "text"
    assert request_data["messages"][0]["content"][1]["text"] == "hello mimo"
    assert request_data["max_completion_tokens"] == 1024
    assert "max_tokens" not in request_data


def test_ai_service_recognizes_qwen_video_models_by_rule() -> None:
    assert ai_service.supports_video_understanding_model("qwen3.7-plus") is True
    assert ai_service.supports_video_understanding_model("qwen3.6-plus-2026-04-02") is True
    assert ai_service.supports_video_understanding_model("qwen3-vl-plus") is True
    assert ai_service.supports_video_understanding_model("qwen-vl-max") is True
    assert ai_service.supports_video_understanding_model("qvq-plus") is True
    assert ai_service.supports_video_understanding_model("qwen-plus") is False
    assert ai_service.supports_video_understanding_model("qwen3.7-max") is False


@pytest.mark.asyncio
async def test_ai_service_formats_qwen_video_request_with_video_content() -> None:
    ai_config = AIConfig(
        name="cfg-qwen-video",
        provider="custom",
        api_key="plain-test-api-key",
        api_base="https://example.com/qwen-chat-endpoint",
        model="qwen3.7-plus",
        max_tokens=1024,
        temperature=0.7,
        is_active=True,
    )
    analysis = VideoAnalysis(
        user_id="1",
        video_file_id=1,
        prompt_content="分析测试",
        ai_config_id=1,
        status="processing",
        progress=0,
    )
    analysis.id = 104
    analysis.api_call_time = datetime.now()
    analysis.prompt_tokens = 0
    analysis.runtime_video_url = "https://example.com/video.mp4?token=qwen"
    analysis.transmission_method = "url"

    response = Mock()
    response.status_code = 200
    response.headers = {}
    response.aiter_lines = Mock(return_value=_async_line_iter(["data: [DONE]"]))

    response_cm = AsyncMock()
    response_cm.__aenter__.return_value = response
    response_cm.__aexit__.return_value = None

    client = Mock()
    client.stream.return_value = response_cm

    client_cm = AsyncMock()
    client_cm.__aenter__.return_value = client
    client_cm.__aexit__.return_value = None

    db = Mock(spec=Session)

    with patch("app.services.ai_service.httpx.AsyncClient", return_value=client_cm):
        result = [chunk async for chunk in ai_service._call_openai_compatible_api(ai_config, "hello qwen", analysis, db)]

    assert result == []
    request_data = client.stream.call_args.kwargs["json"]
    assert request_data["model"] == "qwen3.7-plus"
    assert request_data["messages"][0]["content"][0]["type"] == "video_url"
    assert request_data["messages"][0]["content"][0]["video_url"]["url"] == "https://example.com/video.mp4?token=qwen"
    assert request_data["messages"][0]["content"][1]["type"] == "text"
    assert request_data["messages"][0]["content"][1]["text"] == "hello qwen"
    assert request_data["max_tokens"] == 1024
    assert "max_completion_tokens" not in request_data


@pytest.mark.asyncio
async def test_ai_service_prefers_public_url_for_qwen_when_base64_selected() -> None:
    ai_config = AIConfig(
        name="cfg-qwen-public-url",
        provider="custom",
        api_key="plain-test-api-key",
        api_base="https://example.com/qwen-chat-endpoint",
        model="qwen3.7-plus",
        max_tokens=1024,
        temperature=0.7,
        is_active=True,
    )
    analysis = VideoAnalysis(
        user_id="1",
        video_file_id=1,
        prompt_content="分析测试",
        ai_config_id=1,
        status="processing",
        progress=0,
        transmission_method="base64",
    )
    analysis.id = 105
    analysis.api_call_time = datetime.now()
    analysis.prompt_tokens = 0
    analysis.runtime_video_url = "https://example.com/video.mp4?token=public"

    response = Mock()
    response.status_code = 200
    response.headers = {}
    response.aiter_lines = Mock(return_value=_async_line_iter(["data: [DONE]"]))

    response_cm = AsyncMock()
    response_cm.__aenter__.return_value = response
    response_cm.__aexit__.return_value = None

    client = Mock()
    client.stream.return_value = response_cm

    client_cm = AsyncMock()
    client_cm.__aenter__.return_value = client
    client_cm.__aexit__.return_value = None

    db = Mock(spec=Session)

    with (
        patch("app.services.ai_service.httpx.AsyncClient", return_value=client_cm),
        patch.object(video_base64_encoder, "is_suitable_for_base64", side_effect=AssertionError("不应进入Base64分支")),
    ):
        result = [chunk async for chunk in ai_service._call_openai_compatible_api(ai_config, "hello qwen", analysis, db)]

    assert result == []
    request_data = client.stream.call_args.kwargs["json"]
    assert request_data["messages"][0]["content"][0]["video_url"]["url"] == "https://example.com/video.mp4?token=public"


@pytest.mark.asyncio
async def test_ai_service_raises_clear_error_when_qwen_base64_exceeds_limit(
    temp_upload_dir: Path,
) -> None:
    video_path = temp_upload_dir / "qwen-too-large.mp4"
    video_path.write_bytes(b"x")

    ai_config = AIConfig(
        name="cfg-qwen-too-large",
        provider="custom",
        api_key="plain-test-api-key",
        api_base="https://example.com/qwen-chat-endpoint",
        model="qwen3.7-plus",
        max_tokens=1024,
        temperature=0.7,
        is_active=True,
    )
    analysis = VideoAnalysis(
        user_id="1",
        video_file_id=1,
        prompt_content="分析测试",
        ai_config_id=1,
        status="processing",
        progress=0,
        transmission_method="base64",
        video_file_path=str(video_path),
    )
    analysis.id = 106
    analysis.api_call_time = datetime.now()
    analysis.prompt_tokens = 0
    analysis.runtime_video_url = "http://0.0.0.0:8000/video.mp4?token=local"

    db = Mock(spec=Session)

    with (
        patch("app.services.ai_service.os.path.getsize", return_value=ai_service.qwen_max_raw_file_size + 1),
        patch.object(video_base64_encoder, "check_ffmpeg_available", return_value=False),
    ):
        with pytest.raises(ValueError, match="Qwen Base64 超限"):
            [chunk async for chunk in ai_service._call_openai_compatible_api(ai_config, "hello qwen", analysis, db)]


@pytest.mark.asyncio
async def test_ai_service_uploads_file_to_dashscope_and_sets_oss_header(
    temp_upload_dir: Path,
) -> None:
    video_path = temp_upload_dir / "qwen-upload.mp4"
    video_path.write_bytes(b"fake-video-content")

    ai_config = AIConfig(
        name="cfg-qwen-upload",
        provider="custom",
        api_key="plain-parse-api-key",
        upload_api_key="plain-upload-api-key",
        api_base="https://coding.dashscope.aliyuncs.com/v1/chat/completions",
        model="qwen3.7-plus",
        max_tokens=1024,
        temperature=0.7,
        is_active=True,
    )
    analysis = VideoAnalysis(
        user_id="1",
        video_file_id=1,
        prompt_content="分析测试",
        ai_config_id=1,
        status="processing",
        progress=0,
        transmission_method="upload",
        video_file_path=str(video_path),
    )
    analysis.id = 107
    analysis.api_call_time = datetime.now()
    analysis.prompt_tokens = 0

    policy_response = Mock()
    policy_response.status_code = 200
    policy_response.text = ""
    policy_response.json = Mock(
        return_value={
            "data": {
                "upload_host": "https://oss-example.aliyuncs.com",
                "upload_dir": "dashscope-instant/unit-test",
                "oss_access_key_id": "ak",
                "signature": "sign",
                "policy": "policy-value",
                "x_oss_object_acl": "private",
                "x_oss_forbid_overwrite": "true",
            }
        }
    )
    upload_response = Mock()
    upload_response.status_code = 200
    upload_response.text = ""

    upload_client = Mock()
    upload_client.get = AsyncMock(return_value=policy_response)
    upload_client.post = AsyncMock(return_value=upload_response)
    upload_client_cm = AsyncMock()
    upload_client_cm.__aenter__.return_value = upload_client
    upload_client_cm.__aexit__.return_value = None

    stream_response = Mock()
    stream_response.status_code = 200
    stream_response.headers = {}
    stream_response.aiter_lines = Mock(return_value=_async_line_iter(["data: [DONE]"]))
    stream_response_cm = AsyncMock()
    stream_response_cm.__aenter__.return_value = stream_response
    stream_response_cm.__aexit__.return_value = None

    stream_client = Mock()
    stream_client.stream.return_value = stream_response_cm
    stream_client_cm = AsyncMock()
    stream_client_cm.__aenter__.return_value = stream_client
    stream_client_cm.__aexit__.return_value = None

    db = Mock(spec=Session)

    with patch(
        "app.services.ai_service.httpx.AsyncClient",
        side_effect=[upload_client_cm, stream_client_cm],
    ):
        result = [chunk async for chunk in ai_service._call_openai_compatible_api(ai_config, "hello upload", analysis, db)]

    assert result == []
    assert upload_client.get.await_args.kwargs["params"] == {"action": "getPolicy", "model": "qwen3.7-plus"}
    assert upload_client.get.await_args.kwargs["headers"]["Authorization"] == "Bearer plain-upload-api-key"
    assert upload_client.post.await_args.kwargs["data"]["key"] == "dashscope-instant/unit-test/qwen-upload.mp4"
    request_headers = stream_client.stream.call_args.kwargs["headers"]
    request_data = stream_client.stream.call_args.kwargs["json"]
    assert request_headers["Authorization"] == "Bearer plain-parse-api-key"
    assert request_headers["X-DashScope-OssResourceResolve"] == "enable"
    assert request_data["messages"][0]["content"][0]["video_url"]["url"] == "oss://dashscope-instant/unit-test/qwen-upload.mp4"


@pytest.mark.asyncio
async def test_ai_service_rejects_upload_for_non_dashscope_config(
    temp_upload_dir: Path,
) -> None:
    video_path = temp_upload_dir / "not-supported.mp4"
    video_path.write_bytes(b"fake-video-content")

    ai_config = AIConfig(
        name="cfg-upload-unsupported",
        provider="custom",
        api_key="plain-test-api-key",
        api_base="https://example.com/qwen-chat-endpoint",
        model="qwen3.7-plus",
        max_tokens=1024,
        temperature=0.7,
        is_active=True,
    )
    analysis = VideoAnalysis(
        user_id="1",
        video_file_id=1,
        prompt_content="分析测试",
        ai_config_id=1,
        status="processing",
        progress=0,
        transmission_method="upload",
        video_file_path=str(video_path),
    )
    analysis.id = 108
    analysis.api_call_time = datetime.now()
    analysis.prompt_tokens = 0

    db = Mock(spec=Session)

    with pytest.raises(ValueError, match="当前 AI 配置暂不支持百炼临时文件上传"):
        [chunk async for chunk in ai_service._call_openai_compatible_api(ai_config, "hello upload", analysis, db)]


@pytest.mark.asyncio
async def test_ai_service_rejects_qwen_upload_without_upload_api_key(
    temp_upload_dir: Path,
) -> None:
    video_path = temp_upload_dir / "missing-upload-key.mp4"
    video_path.write_bytes(b"fake-video-content")

    ai_config = AIConfig(
        name="cfg-qwen-upload-missing-key",
        provider="custom",
        api_key="plain-parse-api-key",
        api_base="https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
        model="qwen3.7-plus",
        max_tokens=1024,
        temperature=0.7,
        is_active=True,
    )
    analysis = VideoAnalysis(
        user_id="1",
        video_file_id=1,
        prompt_content="分析测试",
        ai_config_id=1,
        status="processing",
        progress=0,
        transmission_method="upload",
        video_file_path=str(video_path),
    )
    analysis.id = 109
    analysis.api_call_time = datetime.now()
    analysis.prompt_tokens = 0

    db = Mock(spec=Session)

    with pytest.raises(ValueError, match="上传专用 API Key"):
        [chunk async for chunk in ai_service._call_openai_compatible_api(ai_config, "hello upload", analysis, db)]


@pytest.mark.asyncio
async def test_ai_service_ignores_empty_stream_chunks_for_mimo() -> None:
    ai_config = AIConfig(
        name="cfg-mimo-stream",
        provider="custom",
        api_key="plain-test-api-key",
        api_base="https://example.com/mimo-chat-endpoint",
        model="mimo-v2.5",
        max_tokens=1024,
        temperature=0.7,
        is_active=True,
    )
    analysis = VideoAnalysis(
        user_id="1",
        video_file_id=1,
        prompt_content="分析测试",
        ai_config_id=1,
        status="processing",
        progress=0,
    )
    analysis.id = 102
    analysis.api_call_time = datetime.now()
    analysis.prompt_tokens = 0
    analysis.transmission_method = "url"
    analysis.runtime_video_url = "https://example.com/video.mp4?token=stream"

    response = Mock()
    response.status_code = 200
    response.headers = {}
    response.aiter_lines = Mock(
        return_value=_async_line_iter(
            [
                'data: {"choices":[{"delta":{"content":null,"reasoning_content":"thinking"}}]}',
                'data: {"choices":[{"delta":{"content":"最终答案"}}]}',
                "data: [DONE]",
            ]
        )
    )

    response_cm = AsyncMock()
    response_cm.__aenter__.return_value = response
    response_cm.__aexit__.return_value = None

    client = Mock()
    client.stream.return_value = response_cm

    client_cm = AsyncMock()
    client_cm.__aenter__.return_value = client
    client_cm.__aexit__.return_value = None

    db = Mock(spec=Session)

    with patch("app.services.ai_service.httpx.AsyncClient", return_value=client_cm):
        result = [chunk async for chunk in ai_service._call_openai_compatible_api(ai_config, "hello mimo", analysis, db)]

    assert result == ["最终答案"]
    assert analysis.completion_tokens == len("最终答案") // 4


@pytest.mark.asyncio
async def test_ai_service_formats_mimo_base64_request_with_correct_mime_and_persists_debug_info(
    db_session: Session,
    temp_upload_dir: Path,
) -> None:
    video_path = temp_upload_dir / "mimo-source.mov"
    video_path.write_bytes(b"fake-video-content")

    ai_config = AIConfig(
        name="cfg-mimo-base64",
        provider="custom",
        api_key="plain-test-api-key",
        api_base="https://example.com/mimo-chat-endpoint",
        model="mimo-v2.5",
        max_tokens=1024,
        temperature=0.7,
        is_active=True,
    )
    analysis = VideoAnalysis(
        user_id="1",
        video_file_id=1,
        prompt_content="分析测试",
        ai_config_id=1,
        status="processing",
        progress=0,
        transmission_method="base64",
        video_file_path=str(video_path),
    )
    db_session.add(analysis)
    db_session.commit()
    db_session.refresh(analysis)
    analysis.api_call_time = datetime.now()
    analysis.prompt_tokens = 0
    db_session.commit()

    response = Mock()
    response.status_code = 200
    response.headers = {}
    response.aiter_lines = Mock(return_value=_async_line_iter(["data: [DONE]"]))

    response_cm = AsyncMock()
    response_cm.__aenter__.return_value = response
    response_cm.__aexit__.return_value = None

    client = Mock()
    client.stream.return_value = response_cm

    client_cm = AsyncMock()
    client_cm.__aenter__.return_value = client
    client_cm.__aexit__.return_value = None

    with (
        patch("app.services.ai_service.httpx.AsyncClient", return_value=client_cm),
        patch.object(video_base64_encoder, "is_suitable_for_base64", return_value=(True, "ok")),
        patch.object(video_base64_encoder, "encode_video_to_base64", return_value="ZmFrZV92aWRlbw=="),
    ):
        result = [chunk async for chunk in ai_service._call_openai_compatible_api(ai_config, "hello mimo", analysis, db_session)]

    assert result == []
    request_data = client.stream.call_args.kwargs["json"]
    video_payload = request_data["messages"][0]["content"][0]
    assert video_payload["type"] == "video_url"
    assert video_payload["video_url"]["url"].startswith("data:video/quicktime;base64,")
    assert video_payload["fps"] == 2
    assert video_payload["media_resolution"] == "default"

    db_session.refresh(analysis)
    assert analysis.debug_info is not None
    assert analysis.debug_info["request_data"]["messages"][0]["content"][0]["video_url"]["url"].startswith(
        "data:video/quicktime;base64,"
    )
    assert analysis.debug_info["request_data"]["max_completion_tokens"] == 1024


@pytest.mark.asyncio
async def test_ai_service_raises_when_mimo_base64_video_cannot_be_prepared() -> None:
    ai_config = AIConfig(
        name="cfg-mimo-base64-fail",
        provider="custom",
        api_key="plain-test-api-key",
        api_base="https://example.com/mimo-chat-endpoint",
        model="mimo-v2.5",
        max_tokens=1024,
        temperature=0.7,
        is_active=True,
    )
    analysis = VideoAnalysis(
        user_id="1",
        video_file_id=1,
        prompt_content="分析测试",
        ai_config_id=1,
        status="processing",
        progress=0,
        transmission_method="base64",
        video_file_path="C:/tmp/missing.mov",
    )
    analysis.id = 103
    analysis.api_call_time = datetime.now()
    analysis.prompt_tokens = 0

    db = Mock(spec=Session)

    with patch.object(video_base64_encoder, "is_suitable_for_base64", return_value=(False, "文件过大")):
        with pytest.raises(ValueError, match="未能生成有效的视频内容"):
            [chunk async for chunk in ai_service._call_openai_compatible_api(ai_config, "hello mimo", analysis, db)]


async def _async_line_iter(lines: list[str]):
    for line in lines:
        yield line


def test_ai_config_schema_allows_large_positive_max_tokens() -> None:
    payload = AIConfigCreate(
        name="cfg-large",
        provider="custom",
        api_key="1234567890-valid-key",
        api_base="https://example.com/v1",
        model="gpt-4o",
        max_tokens=999999999,
        temperature=0.7,
        is_active=True,
    )

    assert payload.max_tokens == 999999999


def test_ai_config_schema_rejects_non_positive_or_non_integer_max_tokens() -> None:
    with pytest.raises(ValidationError):
        AIConfigCreate(
            name="cfg-zero",
            provider="custom",
            api_key="1234567890-valid-key",
            api_base="https://example.com/v1",
            model="gpt-4o",
            max_tokens=0,
        )

    with pytest.raises(ValidationError):
        AIConfigUpdate(max_tokens=-1)

    with pytest.raises(ValidationError):
        AIConfigUpdate(max_tokens=1.5)
