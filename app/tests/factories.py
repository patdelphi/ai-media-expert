"""测试数据工厂

集中生成常用测试数据，避免在用例中重复拼装对象。
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from app.core.security import create_access_token, get_password_hash
from app.models.uploaded_file import UploadedFile
from app.models.user import User


def create_user(
    db: Session,
    *,
    email: str = "user@example.com",
    password: Optional[str] = None,
    role: str = "user",
    is_active: bool = True,
    is_verified: bool = True,
) -> User:
    hashed_password = "x"
    if password is not None:
        hashed_password = get_password_hash(password)

    user = User(
        email=email,
        hashed_password=hashed_password,
        role=role,
        is_active=is_active,
        is_verified=is_verified,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_admin(
    db: Session,
    *,
    email: str = "admin@example.com",
    password: Optional[str] = None,
) -> User:
    return create_user(db, email=email, password=password, role="admin", is_verified=True)


def create_auth_headers(user: User) -> dict[str, str]:
    token = create_access_token(subject=user.id)
    return {"Authorization": f"Bearer {token}"}


def create_uploaded_file(
    db: Session,
    *,
    user: User,
    original_filename: str,
    saved_filename: str,
    file_path: Path,
    content_type: str = "video/mp4",
    file_size: int = 1,
    title: Optional[str] = None,
    description: Optional[str] = None,
) -> UploadedFile:
    record = UploadedFile(
        user_id=str(user.id),
        original_filename=original_filename,
        saved_filename=saved_filename,
        file_size=file_size,
        content_type=content_type,
        title=title or Path(original_filename).stem,
        description=description,
        file_path=str(file_path),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record
