"""正式路由与废弃路由注册测试

固定阶段 2 的路由收敛结果，避免旧实现重新挂载。
"""

from __future__ import annotations

from fastapi.routing import APIRoute
from starlette.routing import WebSocketRoute

from app.app import app


def _api_paths() -> set[str]:
    return {route.path for route in app.routes if isinstance(route, APIRoute)}


def _websocket_paths() -> set[str]:
    return {route.path for route in app.routes if isinstance(route, WebSocketRoute)}


def test_formal_api_routes_should_remain_registered() -> None:
    api_paths = _api_paths()

    assert "/api/v1/simple-upload/simple" in api_paths
    assert "/api/v1/upload/init" in api_paths
    assert "/api/v1/upload/chunk" in api_paths
    assert "/api/v1/upload/control" in api_paths
    assert "/api/v1/files/files" in api_paths
    assert "/api/v1/video-analysis/videos/{video_id}" in api_paths
    assert "/api/v1/download/platforms" in api_paths
    assert "/api/v1/download/statistics/overview" in api_paths
    assert "/api/v1/download/queue" in api_paths
    assert "/api/v1/ai-config/" in api_paths
    assert "/api/v1/prompt-templates/" in api_paths


def test_deprecated_api_routes_should_not_be_registered() -> None:
    api_paths = _api_paths()

    assert "/api/v1/videos/" not in api_paths
    assert "/api/v1/analysis/start/{video_id}" not in api_paths
    assert "/api/v1/upload/" not in api_paths
    assert "/api/v1/upload/batch" not in api_paths
    assert "/api/v1/upload/status/{video_id}" not in api_paths
    assert "/api/v1/download/platforms/platforms" not in api_paths
    assert "/api/v1/download/queue/queue" not in api_paths


def test_only_token_based_websocket_route_should_remain_registered() -> None:
    websocket_paths = _websocket_paths()

    assert "/api/v1/websocket/ws" in websocket_paths
    assert "/api/v1/websocket/ws/{user_id}" not in websocket_paths
