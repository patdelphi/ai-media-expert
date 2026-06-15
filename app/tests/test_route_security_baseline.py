"""路由安全基线测试

该文件用于固定“敏感路由必须拒绝匿名访问”的访问边界，后续阶段会逐步让这些断言全部通过。
"""

from __future__ import annotations

import pytest
from fastapi.routing import APIRoute
from starlette.routing import WebSocketRoute

from app.api import deps
from app.app import app


def _dependant_contains(dependant, target) -> bool:
    if getattr(dependant, "call", None) is target:
        return True
    for child in getattr(dependant, "dependencies", []) or []:
        if _dependant_contains(child, target):
            return True
    return False


def _get_api_route(method: str, path: str) -> APIRoute:
    method_upper = method.upper()
    for route in app.routes:
        if isinstance(route, APIRoute) and route.path == path and method_upper in (route.methods or set()):
            return route
    raise AssertionError(f"route not found: {method} {path}")


def _get_websocket_routes() -> list[WebSocketRoute]:
    return [r for r in app.routes if isinstance(r, WebSocketRoute)]


@pytest.mark.parametrize(
    ("method", "path", "required_dependency", "xfail"),
    [
        ("GET", "/api/v1/files/files", deps.get_current_user, False),
        ("POST", "/api/v1/prompt-templates/", deps.require_admin, False),
        ("POST", "/api/v1/ai-config/{config_id}/activate", deps.require_admin, False),
    ],
)
def test_sensitive_routes_must_require_auth_dependency(method: str, path: str, required_dependency, xfail: bool) -> None:
    if xfail:
        pytest.xfail("待阶段1修复：鉴权/权限未落地")
    route = _get_api_route(method, path)
    assert _dependant_contains(route.dependant, required_dependency)


def test_websocket_route_must_not_accept_user_id_path_param() -> None:
    paths = {r.path for r in _get_websocket_routes()}
    assert "/api/v1/websocket/ws/{user_id}" not in paths
