import pytest

from app.api.v1.endpoints.simple_upload import simple_upload
from app.tests.factories import create_user


class DummyUploadFile:
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
async def test_simple_upload_success(override_db, temp_upload_dir, tmp_path) -> None:
    user = create_user(override_db, email="test@example.com")
    upload = DummyUploadFile(filename="sample.mp4", content_type="video/mp4", data=b"dummy")

    resp = await simple_upload(
        file=upload,
        title="t",
        description="d",
        db=override_db,
        current_user=user,
    )

    assert getattr(resp, "code", None) == 200
    assert resp.data.get("file_path")
    assert resp.data["file_path"].startswith(str(temp_upload_dir))

