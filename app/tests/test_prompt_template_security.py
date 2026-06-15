"""提示词模板安全与事务测试

覆盖权限矩阵、非管理员访问边界，以及异常时的事务回滚。
"""

from __future__ import annotations

from unittest.mock import Mock

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.api.v1.prompt_template import (
    create_prompt_template,
    get_prompt_templates,
    update_prompt_template,
    use_prompt_template,
)
from app.models.prompt_template import PromptTemplate
from app.models.user import User
from app.schemas.prompt_template import PromptTemplateCreate, PromptTemplateUpdate
from app.tests.factories import create_admin, create_user


def _create_prompt_template_record(
    db: Session,
    *,
    title: str,
    content: str,
    is_active: bool = True,
) -> PromptTemplate:
    record = PromptTemplate(title=title, content=content, is_active=is_active, usage_count=0)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@pytest.mark.asyncio
async def test_prompt_templates_include_inactive_requires_admin(override_db) -> None:
    user = create_user(override_db, email="prompt-user@example.com")
    _create_prompt_template_record(
        override_db,
        title="inactive-template",
        content="secret",
        is_active=False,
    )

    with pytest.raises(HTTPException) as exc:
        await get_prompt_templates(include_inactive=True, current_user=user, db=override_db)

    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_prompt_template_use_hides_inactive_from_non_admin(override_db) -> None:
    user = create_user(override_db, email="prompt-user2@example.com")
    template = _create_prompt_template_record(
        override_db,
        title="inactive-use",
        content="hidden",
        is_active=False,
    )

    with pytest.raises(HTTPException) as exc:
        await use_prompt_template(template_id=template.id, current_user=user, db=override_db)

    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_prompt_template_admin_can_create_and_list_inactive(override_db) -> None:
    admin = create_admin(override_db, email="prompt-admin@example.com")

    resp = await create_prompt_template(
        template=PromptTemplateCreate(title="admin-template", content="hello", is_active=False),
        current_user=admin,
        db=override_db,
    )
    assert resp.code == 200

    list_resp = await get_prompt_templates(
        include_inactive=True,
        current_user=admin,
        db=override_db,
    )
    assert any(item.title == "admin-template" for item in list_resp.data)


@pytest.mark.asyncio
async def test_create_prompt_template_rolls_back_on_commit_error() -> None:
    admin = User(email="admin@example.com", hashed_password="x", role="admin", is_active=True)
    db = Mock(spec=Session)
    db.query.return_value.filter.return_value.first.return_value = None
    db.commit.side_effect = RuntimeError("db down")

    with pytest.raises(HTTPException) as exc:
        await create_prompt_template(
            template=PromptTemplateCreate(title="rollback-create", content="body", is_active=True),
            current_user=admin,
            db=db,
        )

    assert exc.value.status_code == 500
    assert db.rollback.called is True


@pytest.mark.asyncio
async def test_update_prompt_template_rolls_back_on_commit_error() -> None:
    admin = User(email="admin2@example.com", hashed_password="x", role="admin", is_active=True)
    template = PromptTemplate(title="before", content="content", is_active=True, usage_count=0)
    template.id = 7

    db = Mock(spec=Session)
    db.query.return_value.filter.return_value.first.side_effect = [template, None]
    db.commit.side_effect = RuntimeError("db down")

    with pytest.raises(HTTPException) as exc:
        await update_prompt_template(
            template_id=template.id,
            template_update=PromptTemplateUpdate(title="after"),
            current_user=admin,
            db=db,
        )

    assert exc.value.status_code == 500
    assert db.rollback.called is True
