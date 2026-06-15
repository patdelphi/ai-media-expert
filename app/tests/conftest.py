"""测试公共夹具

提供隔离的测试数据库、临时上传目录，以及常用依赖覆盖工具。
"""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api import deps
from app.app import app
from app.core.database import Base


@pytest.fixture(autouse=True)
def force_test_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.core.config import settings

    monkeypatch.setattr(settings, "environment", "test", raising=False)


@pytest.fixture
def testing_session_local() -> Generator[sessionmaker, None, None]:
    import app.models  # noqa: F401

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    try:
        yield sessionmaker(autocommit=False, autoflush=False, bind=engine)
    finally:
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture
def db_session(testing_session_local: sessionmaker) -> Generator[Session, None, None]:
    db = testing_session_local()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def override_db(testing_session_local: sessionmaker) -> Generator[Session, None, None]:
    seed_db = testing_session_local()

    def _override_get_db() -> Generator[Session, None, None]:
        db = testing_session_local()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[deps.get_db] = _override_get_db
    try:
        yield seed_db
    finally:
        seed_db.close()
        app.dependency_overrides.pop(deps.get_db, None)


@pytest.fixture
def temp_upload_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Generator[Path, None, None]:
    from app.api.v1.endpoints import file_manager as file_manager_endpoints
    from app.api.v1.endpoints import simple_upload as simple_upload_endpoints

    videos_dir = tmp_path / "uploads" / "videos"
    videos_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(simple_upload_endpoints, "UPLOAD_DIR", videos_dir)
    monkeypatch.setattr(file_manager_endpoints, "UPLOAD_DIR", videos_dir)

    yield videos_dir


@pytest.fixture(autouse=True)
def disable_simple_upload_postprocess(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.api.v1.endpoints import simple_upload as simple_upload_endpoints

    def _noop(*_args: Any, **_kwargs: Any) -> None:
        return None

    class _DummyThread:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        def start(self) -> None:
            return None

    monkeypatch.setattr(simple_upload_endpoints, "_postprocess_upload", _noop)
    monkeypatch.setattr(simple_upload_endpoints.threading, "Thread", _DummyThread)
