import inspect

import httpx
import pytest

from app.app import app, lifespan


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
async def test_liveness_check() -> None:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        resp = await client.get("/health/liveness")

    assert resp.status_code == 200
    assert resp.json().get("status") == "alive"


@pytest.mark.asyncio
async def test_readiness_check() -> None:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        resp = await client.get("/health/readiness")

    assert resp.status_code == 200
    assert resp.json().get("status") == "ready"


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
    assert data.get("health") == "/health/liveness"
    assert data.get("readiness") == "/health/readiness"


def test_lifespan_and_uploads_route_hardened() -> None:
    wrapped_lifespan = getattr(lifespan, "__wrapped__", None)
    assert wrapped_lifespan is not None
    assert inspect.isasyncgenfunction(wrapped_lifespan)
    assert all(getattr(route, "path", None) != "/uploads/{path:path}" for route in app.routes)

