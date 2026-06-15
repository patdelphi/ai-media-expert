import pytest

from app.api.v1.endpoints.download import create_download_task, get_download_task, get_download_tasks
from app.schemas.common import PaginationParams
from app.schemas.video import DownloadTaskCreate
from app.tests.factories import create_user


@pytest.mark.asyncio
async def test_download_task_crud(db_session) -> None:
    user = create_user(db_session, email="tester@example.com")

    create_resp = create_download_task(
        DownloadTaskCreate(
            url="https://example.com/video",
            quality="best",
            format_preference="mp4",
            audio_only=False,
            priority=5,
            options=None,
        ),
        current_user=user,
        db=db_session,
    )

    assert create_resp.code == 200
    assert create_resp.data is not None
    task_id = create_resp.data.id

    list_resp = get_download_tasks(
        pagination=PaginationParams(page=1, size=20),
        status_filter=None,
        current_user=user,
        db=db_session,
    )
    assert list_resp.code == 200
    assert list_resp.data is not None
    assert any(item.id == task_id for item in list_resp.data.items)

    get_resp = get_download_task(task_id=task_id, current_user=user, db=db_session)
    assert get_resp.code == 200
    assert get_resp.data is not None
    assert get_resp.data.id == task_id

