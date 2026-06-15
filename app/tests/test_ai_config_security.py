"""AI 配置安全与事务测试

覆盖管理员启停权限，以及异常时的事务回滚。
"""

from __future__ import annotations

from unittest.mock import Mock

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.api.v1.ai_config import activate_ai_config, deactivate_ai_config
from app.models.video import AIConfig
from app.models.user import User
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
