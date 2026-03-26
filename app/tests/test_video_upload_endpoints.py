import httpx
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import patch
from pathlib import Path

from app.api import deps
from app.app import app
from app.core.database import Base
from app.models.user import User
from app.models.video import Video


@pytest.mark.asyncio
async def test_chunked_upload_init_and_chunks(tmp_path) -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    user = User(email="uploader@example.com", hashed_password="x")
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

    from app.api.v1.endpoints import video_upload as video_upload_endpoints

    upload_dir = tmp_path / "uploads" / "videos"
    temp_dir = upload_dir / "temp"
    upload_dir.mkdir(parents=True, exist_ok=True)
    temp_dir.mkdir(parents=True, exist_ok=True)

    video_upload_endpoints.UPLOAD_DIR = upload_dir
    video_upload_endpoints.TEMP_DIR = temp_dir

    payload = b"hello-world"
    chunk_size = 5
    total_chunks = (len(payload) + chunk_size - 1) // chunk_size

    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            init_resp = await client.post(
                "/api/v1/upload/init",
                json={
                    "filename": "sample.mp4",
                    "file_size": len(payload),
                    "chunk_size": chunk_size,
                    "title": "t",
                    "description": "d",
                },
            )
            assert init_resp.status_code == 200
            init_body = init_resp.json()
            assert init_body.get("code") == 200
            session_id = init_body["data"]["upload_session_id"]
            video_id = init_body["data"]["video_id"]

            with patch("app.tasks.video_tasks.process_uploaded_video.delay", return_value=None):
                for i in range(total_chunks):
                    part = payload[i * chunk_size : (i + 1) * chunk_size]
                    resp = await client.post(
                        "/api/v1/upload/chunk",
                        data={
                            "upload_session_id": session_id,
                            "chunk_index": str(i),
                            "total_chunks": str(total_chunks),
                        },
                        files={"chunk_file": ("chunk.bin", part, "application/octet-stream")},
                    )
                    assert resp.status_code == 200
                    body = resp.json()
                    assert body.get("code") == 200

            video = db.query(Video).filter(Video.id == video_id).first()
            assert video is not None
            assert video.upload_status == "completed"
            assert video.upload_progress == 100.0

            merged_path = Path(video.file_path)
            assert merged_path.exists()
            assert merged_path.read_bytes() == payload

    finally:
        app.dependency_overrides.clear()
        db.close()
        Base.metadata.drop_all(bind=engine)

