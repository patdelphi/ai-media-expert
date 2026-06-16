"""文件管理安全测试

覆盖匿名访问拒绝、用户隔离、管理员只读跨用户的策略。
"""

from __future__ import annotations

import pytest

from starlette.responses import FileResponse

from app.api import deps
from app.app import app
from app.api.v1.endpoints.file_manager import (
    create_stream_token,
    delete_file,
    get_stats,
    list_files,
    stream_file,
)
from app.core.security import (
    create_access_token,
    create_media_access_token,
    verify_media_access_token,
)
from app.tests.factories import create_admin, create_uploaded_file, create_user


def _dependant_contains(dependant, target) -> bool:
    if getattr(dependant, "call", None) is target:
        return True
    for child in getattr(dependant, "dependencies", None) or []:
        if _dependant_contains(child, target):
            return True
    return False


def _get_api_route(method: str, path: str):
    from fastapi.routing import APIRoute

    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        if route.path != path:
            continue
        if method.upper() not in route.methods:
            continue
        return route
    raise AssertionError(f"API route not found: {method} {path}")


def test_files_list_requires_auth_dependency() -> None:
    route = _get_api_route("GET", "/api/v1/files/files")
    assert _dependant_contains(route.dependant, deps.get_current_user)


def test_stream_token_requires_auth_dependency() -> None:
    route = _get_api_route("GET", "/api/v1/files/stream-token/{filename}")
    assert _dependant_contains(route.dependant, deps.get_current_user)


@pytest.mark.asyncio
async def test_files_list_isolated_by_user(override_db, temp_upload_dir) -> None:
    user_a = create_user(override_db, email="a@example.com")
    user_b = create_user(override_db, email="b@example.com")

    file_a = temp_upload_dir / "a.mp4"
    file_b = temp_upload_dir / "b.mp4"
    file_a.write_bytes(b"a")
    file_b.write_bytes(b"b")

    create_uploaded_file(
        override_db,
        user=user_a,
        original_filename="a.mp4",
        saved_filename="a.mp4",
        file_path=file_a,
        file_size=1,
    )
    create_uploaded_file(
        override_db,
        user=user_b,
        original_filename="b.mp4",
        saved_filename="b.mp4",
        file_path=file_b,
        file_size=1,
    )
    payload = await list_files(db=override_db, current_user=user_a)
    assert payload.get("success") is True
    files = payload.get("files") or []
    assert len(files) == 1
    assert files[0]["saved_name"] == "a.mp4"


@pytest.mark.asyncio
async def test_files_delete_rejects_cross_user(override_db, temp_upload_dir) -> None:
    user_a = create_user(override_db, email="a2@example.com")
    user_b = create_user(override_db, email="b2@example.com")

    file_b = temp_upload_dir / "b2.mp4"
    file_b.write_bytes(b"b")

    create_uploaded_file(
        override_db,
        user=user_b,
        original_filename="b2.mp4",
        saved_filename="b2.mp4",
        file_path=file_b,
        file_size=1,
    )
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        await delete_file(filename="b2.mp4", db=override_db, current_user=user_a)

    assert exc.value.status_code in {403, 404}
    assert file_b.exists()


@pytest.mark.asyncio
async def test_admin_can_list_cross_user_but_cannot_delete(override_db, temp_upload_dir) -> None:
    admin = create_admin(override_db, email="admin_files@example.com")
    user_b = create_user(override_db, email="b3@example.com")

    file_b = temp_upload_dir / "b3.mp4"
    file_b.write_bytes(b"b")

    create_uploaded_file(
        override_db,
        user=user_b,
        original_filename="b3.mp4",
        saved_filename="b3.mp4",
        file_path=file_b,
        file_size=1,
    )
    from fastapi import HTTPException

    list_payload = await list_files(db=override_db, current_user=admin)
    assert list_payload.get("success") is True
    assert (list_payload.get("total_count") or 0) >= 1

    with pytest.raises(HTTPException) as exc:
        await delete_file(filename="b3.mp4", db=override_db, current_user=admin)

    assert exc.value.status_code == 403
    assert file_b.exists()


@pytest.mark.asyncio
async def test_file_stats_non_admin_returns_403(override_db) -> None:
    user = create_user(override_db, email="stats-user@example.com")
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        await get_stats(current_user=user)

    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_stream_file_requires_token(override_db, temp_upload_dir) -> None:
    user = create_user(override_db, email="stream-missing@example.com")
    file_path = temp_upload_dir / "stream-missing.mp4"
    file_path.write_bytes(b"abcdef")

    create_uploaded_file(
        override_db,
        user=user,
        original_filename="stream-missing.mp4",
        saved_filename="stream-missing.mp4",
        file_path=file_path,
        file_size=6,
    )

    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        await stream_file(filename="stream-missing.mp4", token=None, db=override_db)

    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_stream_token_is_issued_for_owned_file(override_db, temp_upload_dir) -> None:
    user = create_user(override_db, email="stream-token@example.com")
    file_path = temp_upload_dir / "stream-token.mp4"
    file_path.write_bytes(b"abcdef")

    create_uploaded_file(
        override_db,
        user=user,
        original_filename="stream-token.mp4",
        saved_filename="stream-token.mp4",
        file_path=file_path,
        file_size=6,
    )

    payload = await create_stream_token(
        filename="stream-token.mp4",
        db=override_db,
        current_user=user,
    )

    assert payload["success"] is True
    assert payload["saved_name"] == "stream-token.mp4"
    assert payload["stream_path"].endswith("/api/v1/files/stream/stream-token.mp4")
    token_payload = verify_media_access_token(payload["token"])
    assert token_payload is not None
    assert token_payload["sub"] == str(user.id)
    assert token_payload["file"] == "stream-token.mp4"


@pytest.mark.asyncio
async def test_stream_token_rejects_cross_user_file(override_db, temp_upload_dir) -> None:
    user_a = create_user(override_db, email="stream-token-a@example.com")
    user_b = create_user(override_db, email="stream-token-b@example.com")
    file_path = temp_upload_dir / "stream-token-cross.mp4"
    file_path.write_bytes(b"abcdef")

    create_uploaded_file(
        override_db,
        user=user_b,
        original_filename="stream-token-cross.mp4",
        saved_filename="stream-token-cross.mp4",
        file_path=file_path,
        file_size=6,
    )

    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        await create_stream_token(
            filename="stream-token-cross.mp4",
            db=override_db,
            current_user=user_a,
        )

    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_stream_file_rejects_normal_access_token(override_db, temp_upload_dir) -> None:
    user = create_user(override_db, email="stream-access@example.com")
    file_path = temp_upload_dir / "stream-access.mp4"
    file_path.write_bytes(b"abcdef")

    create_uploaded_file(
        override_db,
        user=user,
        original_filename="stream-access.mp4",
        saved_filename="stream-access.mp4",
        file_path=file_path,
        file_size=6,
    )
    access_token = create_access_token(subject=user.id)

    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        await stream_file(filename="stream-access.mp4", token=access_token, db=override_db)

    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_stream_file_rejects_token_for_other_filename(override_db, temp_upload_dir) -> None:
    user = create_user(override_db, email="stream-mismatch@example.com")
    file_path = temp_upload_dir / "stream-mismatch.mp4"
    file_path.write_bytes(b"abcdef")

    create_uploaded_file(
        override_db,
        user=user,
        original_filename="stream-mismatch.mp4",
        saved_filename="stream-mismatch.mp4",
        file_path=file_path,
        file_size=6,
    )
    media_token = create_media_access_token(
        subject=user.id,
        saved_filename="other-file.mp4",
    )

    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        await stream_file(filename="stream-mismatch.mp4", token=media_token, db=override_db)

    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_stream_file_rejects_cross_user_access(override_db, temp_upload_dir) -> None:
    user_a = create_user(override_db, email="stream-owner-a@example.com")
    user_b = create_user(override_db, email="stream-owner-b@example.com")
    file_path = temp_upload_dir / "stream-cross-user.mp4"
    file_path.write_bytes(b"abcdef")

    create_uploaded_file(
        override_db,
        user=user_b,
        original_filename="stream-cross-user.mp4",
        saved_filename="stream-cross-user.mp4",
        file_path=file_path,
        file_size=6,
    )
    media_token = create_media_access_token(
        subject=user_a.id,
        saved_filename="stream-cross-user.mp4",
    )

    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        await stream_file(filename="stream-cross-user.mp4", token=media_token, db=override_db)

    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_stream_file_returns_inline_content(override_db, temp_upload_dir) -> None:
    user = create_user(override_db, email="stream-inline@example.com")
    file_path = temp_upload_dir / "stream-inline.mp4"
    file_path.write_bytes(b"abcdef")

    create_uploaded_file(
        override_db,
        user=user,
        original_filename="stream-inline.mp4",
        saved_filename="stream-inline.mp4",
        file_path=file_path,
        file_size=6,
    )
    media_token = create_media_access_token(
        subject=user.id,
        saved_filename="stream-inline.mp4",
    )

    response = await stream_file(filename="stream-inline.mp4", token=media_token, db=override_db)

    assert isinstance(response, FileResponse)
    assert response.status_code == 200
    assert response.path == str(file_path)
    assert response.headers.get("content-disposition", "").startswith("inline;")
    assert response.headers.get("accept-ranges") == "bytes"


@pytest.mark.asyncio
async def test_stream_file_supports_range_requests(override_db, temp_upload_dir) -> None:
    user = create_user(override_db, email="stream-range@example.com")
    file_path = temp_upload_dir / "stream-range.mp4"
    file_path.write_bytes(b"abcdef")

    create_uploaded_file(
        override_db,
        user=user,
        original_filename="stream-range.mp4",
        saved_filename="stream-range.mp4",
        file_path=file_path,
        file_size=6,
    )
    media_token = create_media_access_token(
        subject=user.id,
        saved_filename="stream-range.mp4",
    )

    response = await stream_file(filename="stream-range.mp4", token=media_token, db=override_db)

    assert isinstance(response, FileResponse)
    assert response.headers.get("accept-ranges") == "bytes"
    assert FileResponse._parse_range_header("bytes=0-2", 6) == [(0, 3)]
