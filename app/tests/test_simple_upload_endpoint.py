import os

import httpx
import pytest
from sqlalchemy.orm import Session
from unittest.mock import Mock

from app.api import deps
from app.app import app
from app.models.user import User


@pytest.mark.asyncio
async def test_simple_upload_success(tmp_path) -> None:
    def override_get_current_user() -> User:
        user = User(email="test@example.com", hashed_password="x")
        user.id = 1
        user.is_active = True
        return user

    def override_get_db() -> Session:
        return Mock(spec=Session)

    app.dependency_overrides[deps.get_current_user] = override_get_current_user
    app.dependency_overrides[deps.get_db] = override_get_db

    file_path = tmp_path / "sample.mp4"
    file_path.write_bytes(b"dummy")

    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            resp = await client.post(
                "/api/v1/simple-upload/simple",
                files={"file": ("sample.mp4", file_path.read_bytes(), "video/mp4")},
                data={"title": "t", "description": "d"},
            )

        assert resp.status_code == 200
        body = resp.json()
        assert body.get("code") == 200
        assert body.get("data", {}).get("file_path")

        saved_path = body["data"]["file_path"]
        assert os.path.exists(saved_path)

    finally:
        app.dependency_overrides.clear()
        try:
            if "saved_path" in locals() and os.path.exists(saved_path):
                os.remove(saved_path)
        except Exception:
            pass

