from datetime import datetime, UTC
from unittest.mock import Mock

import pytest
from sqlalchemy.orm import Session

from fastapi import HTTPException

from app.models.user import User
from app.api.v1.endpoints.users import change_password, update_user
from app.schemas.auth import PasswordChange
from app.schemas.user import AdminUserUpdate


def _fake_hash(password: str) -> str:
    return f"hashed:{password}"


def _fake_verify(plain_password: str, hashed_password: str) -> bool:
    return hashed_password == _fake_hash(plain_password)


def _utcnow() -> datetime:
    """统一生成 UTC 时间，避免废弃 API 警告。"""
    return datetime.now(UTC).replace(tzinfo=None)


def test_change_password_success(monkeypatch: pytest.MonkeyPatch) -> None:
    old_password = "Oldpass123"
    new_password = "Newpass123"

    from app.api.v1.endpoints import users as users_endpoints

    monkeypatch.setattr(users_endpoints, "get_password_hash", _fake_hash)
    monkeypatch.setattr(users_endpoints, "verify_password", _fake_verify)

    user = User(email="test@example.com", hashed_password=_fake_hash(old_password))
    user.id = 1
    user.is_active = True
    user.is_verified = True
    user.role = "user"
    user.created_at = _utcnow()
    user.updated_at = _utcnow()

    db = Mock(spec=Session)

    resp = change_password(
        password_data=PasswordChange(current_password=old_password, new_password=new_password),
        current_user=user,
        db=db,
    )
    assert resp.code == 200
    assert _fake_verify(new_password, user.hashed_password) is True
    assert db.commit.called is True


def test_change_password_rejects_wrong_current_password(monkeypatch: pytest.MonkeyPatch) -> None:
    old_password = "Oldpass123"

    from app.api.v1.endpoints import users as users_endpoints

    monkeypatch.setattr(users_endpoints, "get_password_hash", _fake_hash)
    monkeypatch.setattr(users_endpoints, "verify_password", _fake_verify)

    user = User(email="test@example.com", hashed_password=_fake_hash(old_password))
    user.id = 1
    user.is_active = True
    user.is_verified = True
    user.role = "user"
    user.created_at = _utcnow()
    user.updated_at = _utcnow()

    db = Mock(spec=Session)

    with pytest.raises(HTTPException) as exc:
        change_password(
            password_data=PasswordChange(
                current_password="Wrongpass123",
                new_password="Newpass123",
            ),
            current_user=user,
            db=db,
        )

    assert exc.value.status_code == 400
    assert _fake_verify(old_password, user.hashed_password) is True
    assert db.commit.called is False


def test_admin_update_user_can_set_password(monkeypatch: pytest.MonkeyPatch) -> None:
    old_password = "Oldpass123"
    new_password = "Newpass123"

    from app.api.v1.endpoints import users as users_endpoints

    monkeypatch.setattr(users_endpoints, "get_password_hash", _fake_hash)
    monkeypatch.setattr(users_endpoints, "verify_password", _fake_verify)

    target_user = User(email="target@example.com", hashed_password=_fake_hash(old_password))
    target_user.id = 2
    target_user.username = "target"
    target_user.is_active = True
    target_user.is_verified = True
    target_user.role = "user"
    target_user.created_at = _utcnow()
    target_user.updated_at = _utcnow()

    admin_user = User(email="admin@example.com", hashed_password="x")
    admin_user.id = 99
    admin_user.is_active = True
    admin_user.is_verified = True
    admin_user.role = "admin"
    admin_user.created_at = _utcnow()
    admin_user.updated_at = _utcnow()

    db = Mock(spec=Session)
    db.query.return_value.filter.return_value.first.return_value = target_user

    resp = update_user(
        user_id=2,
        user_update=AdminUserUpdate(password=new_password),
        current_user=admin_user,
        db=db,
    )
    assert resp.code == 200
    assert _fake_verify(new_password, target_user.hashed_password) is True
    assert db.commit.called is True
    assert db.refresh.called is True

