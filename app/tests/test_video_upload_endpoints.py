import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import patch
from pathlib import Path

from app.core.database import Base
from app.models.user import User
from app.models.video import Video
from app.api.v1.endpoints.video_upload import init_upload, upload_chunk
from app.schemas.video_upload import InitUploadRequest


class DummyChunkUploadFile:
    """测试用分片上传文件对象。"""

    def __init__(self, *, filename: str, content_type: str, data: bytes) -> None:
        self.filename = filename
        self.content_type = content_type
        self.size = len(data)
        self._data = data
        self._offset = 0

    async def read(self, size: int = -1) -> bytes:
        if self._offset >= len(self._data):
            return b""
        if size is None or size < 0:
            chunk = self._data[self._offset :]
            self._offset = len(self._data)
            return chunk
        chunk = self._data[self._offset : self._offset + size]
        self._offset += len(chunk)
        return chunk


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
        init_body = init_upload(
            request=InitUploadRequest(
                filename="sample.mp4",
                file_size=len(payload),
                chunk_size=chunk_size,
                title="t",
                description="d",
            ),
            current_user=user,
            db=db,
        )
        assert init_body.code == 200
        session_id = init_body.data.upload_session_id
        video_id = init_body.data.video_id

        with patch("app.tasks.video_tasks.process_uploaded_video.delay", return_value=None):
            for i in range(total_chunks):
                part = payload[i * chunk_size : (i + 1) * chunk_size]
                resp = await upload_chunk(
                    upload_session_id=session_id,
                    chunk_index=i,
                    total_chunks=total_chunks,
                    chunk_file=DummyChunkUploadFile(
                        filename="chunk.bin",
                        content_type="application/octet-stream",
                        data=part,
                    ),
                    current_user=user,
                    db=db,
                )
                assert resp.code == 200

        video = db.query(Video).filter(Video.id == video_id).first()
        assert video is not None
        assert video.upload_status == "completed"
        assert video.upload_progress == 100.0

        merged_path = Path(video.file_path)
        assert merged_path.exists()
        assert merged_path.read_bytes() == payload
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()

