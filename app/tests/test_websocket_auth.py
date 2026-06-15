"""WebSocket 认证测试

覆盖 token 认证助手和路径收敛后的访问边界。
"""

from __future__ import annotations

import pytest

from fastapi import HTTPException

from app.api.v1.endpoints.websocket import _authenticate_websocket_token
from app.core.security import create_access_token
from app.tests.factories import create_user


def test_authenticate_websocket_token_rejects_missing_token(db_session) -> None:
    with pytest.raises(HTTPException) as exc:
        _authenticate_websocket_token(None, db_session)

    assert exc.value.status_code == 401


def test_authenticate_websocket_token_accepts_valid_token(db_session) -> None:
    user = create_user(db_session, email="ws-user@example.com")
    token = create_access_token(subject=user.id)

    authenticated_user = _authenticate_websocket_token(token, db_session)

    assert authenticated_user.id == user.id
