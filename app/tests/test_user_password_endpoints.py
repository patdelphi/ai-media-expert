from datetime import datetime
from unittest.mock import Mock

import httpx
import pytest
from sqlalchemy.orm import Session

from app.api import deps
from app.app import app
from app.core.security import get_password_hash, verify_password
from app.models.user import User


@pytest.mark.asyncio
async def test_change_password_success() -> None:
    old_password = "Oldpass123"
    new_password = "Newpass123"

    user = User(email="test@example.com", hashed_password=get_password_hash(old_password))
    user.id = 1
    user.is_active = True
    user.is_verified = True
    user.role = "user"
    user.created_at = datetime.utcnow()
    user.updated_at = datetime.utcnow()

    db = Mock(spec=Session)

    def override_get_current_user() -> User:
        return user

    def override_get_db() -> Session:
        return db

    app.dependency_overrides[deps.get_current_user] = override_get_current_user
    app.dependency_overrides[deps.get_db] = override_get_db

    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            resp = await client.post(
                "/api/v1/users/change-password",
                json={"current_password": old_password, "new_password": new_password},
            )

        assert resp.status_code == 200
        body = resp.json()
        assert body.get("code") == 200
        assert verify_password(new_password, user.hashed_password) is True
        assert db.commit.called is True
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_change_password_rejects_wrong_current_password() -> None:
    old_password = "Oldpass123"
    user = User(email="test@example.com", hashed_password=get_password_hash(old_password))
    user.id = 1
    user.is_active = True
    user.is_verified = True
    user.role = "user"
    user.created_at = datetime.utcnow()
    user.updated_at = datetime.utcnow()

    db = Mock(spec=Session)

    def override_get_current_user() -> User:
        return user

    def override_get_db() -> Session:
        return db

    app.dependency_overrides[deps.get_current_user] = override_get_current_user
    app.dependency_overrides[deps.get_db] = override_get_db

    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            resp = await client.post(
                "/api/v1/users/change-password",
                json={"current_password": "Wrongpass123", "new_password": "Newpass123"},
            )

        assert resp.status_code == 400
        assert verify_password(old_password, user.hashed_password) is True
        assert db.commit.called is False
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_admin_update_user_can_set_password() -> None:
    old_password = "Oldpass123"
    new_password = "Newpass123"

    target_user = User(email="target@example.com", hashed_password=get_password_hash(old_password))
    target_user.id = 2
    target_user.username = "target"
    target_user.is_active = True
    target_user.is_verified = True
    target_user.role = "user"
    target_user.created_at = datetime.utcnow()
    target_user.updated_at = datetime.utcnow()

    admin_user = User(email="admin@example.com", hashed_password="x")
    admin_user.id = 99
    admin_user.is_active = True
    admin_user.is_verified = True
    admin_user.role = "admin"
    admin_user.created_at = datetime.utcnow()
    admin_user.updated_at = datetime.utcnow()

    db = Mock(spec=Session)
    db.query.return_value.filter.return_value.first.return_value = target_user

    def override_require_admin() -> User:
        return admin_user

    def override_get_db() -> Session:
        return db

    app.dependency_overrides[deps.require_admin] = override_require_admin
    app.dependency_overrides[deps.get_db] = override_get_db

    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            resp = await client.put(
                "/api/v1/users/2",
                json={"password": new_password},
            )

        assert resp.status_code == 200
        body = resp.json()
        assert body.get("code") == 200
        assert verify_password(new_password, target_user.hashed_password) is True
        assert db.commit.called is True
        assert db.refresh.called is True
    finally:
        app.dependency_overrides.clear()

