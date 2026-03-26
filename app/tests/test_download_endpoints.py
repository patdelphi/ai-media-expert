import httpx
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api import deps
from app.app import app
from app.core.database import Base
from app.models.user import User


@pytest.mark.asyncio
async def test_download_task_crud() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    user = User(email="tester@example.com", hashed_password="x")
    db.add(user)
    db.commit()
    db.refresh(user)

    def override_get_current_user() -> User:
        return user

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[deps.get_current_user] = override_get_current_user
    app.dependency_overrides[deps.get_db] = override_get_db

    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            create_resp = await client.post(
                "/api/v1/download/tasks",
                json={
                    "url": "https://example.com/video",
                    "quality": "best",
                    "format_preference": "mp4",
                    "audio_only": False,
                    "priority": 5,
                },
            )

            assert create_resp.status_code == 200
            body = create_resp.json()
            assert body.get("code") == 200
            task_id = body["data"]["id"]

            list_resp = await client.get("/api/v1/download/tasks")
            assert list_resp.status_code == 200
            list_body = list_resp.json()
            assert list_body.get("code") == 200
            items = list_body["data"]["items"]
            assert any(item["id"] == task_id for item in items)

            get_resp = await client.get(f"/api/v1/download/tasks/{task_id}")
            assert get_resp.status_code == 200
            get_body = get_resp.json()
            assert get_body.get("code") == 200
            assert get_body["data"]["id"] == task_id

    finally:
        app.dependency_overrides.clear()
        db.close()
        Base.metadata.drop_all(bind=engine)

