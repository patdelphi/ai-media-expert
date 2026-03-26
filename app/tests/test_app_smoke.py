import httpx
import pytest

from app.app import app


@pytest.mark.asyncio
async def test_health_check() -> None:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        resp = await client.get("/health")

    assert resp.status_code == 200
    assert resp.json().get("status") == "healthy"


@pytest.mark.asyncio
async def test_root() -> None:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        resp = await client.get("/")

    assert resp.status_code == 200
    data = resp.json()
    assert data.get("message")
    assert data.get("docs") == "/docs"
    assert data.get("health") == "/health"

