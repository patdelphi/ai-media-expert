"""文件管理安全测试

覆盖匿名访问拒绝、用户隔离、管理员只读跨用户的策略。
"""

from __future__ import annotations

import pytest

from app.api import deps
from app.app import app
from app.api.v1.endpoints.file_manager import delete_file, list_files
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
