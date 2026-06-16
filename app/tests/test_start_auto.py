"""启动监督脚本测试

验证自动端口选择与前端代理目标注入，确保 bat 启动时
不会再把后端端口固定死在 8000。
"""

from __future__ import annotations

from pathlib import Path

import start_auto


def test_select_backend_port_falls_back_to_next_available_port() -> None:
    manager = start_auto.AutoServiceManager()

    def fake_is_tcp_port_open(_host: str, port: int, timeout: float = 1.0) -> bool:
        return port == 8000

    manager.is_tcp_port_open = fake_is_tcp_port_open

    assert manager.select_backend_port() == 8001


def test_start_frontend_injects_dynamic_proxy_target(
    tmp_path: Path,
    monkeypatch,
) -> None:
    frontend_dir = tmp_path / "frontend"
    logs_dir = tmp_path / "logs"
    frontend_dir.mkdir()
    logs_dir.mkdir()

    monkeypatch.setattr(start_auto, "FRONTEND_DIR", frontend_dir)
    monkeypatch.setattr(start_auto, "LOGS_DIR", logs_dir)

    manager = start_auto.AutoServiceManager()
    manager.backend_port = 8002
    manager.frontend_port = 5173

    popen_calls: list[dict[str, object]] = []

    class DummyProcess:
        pid = 12345

    def fake_popen(*args, **kwargs):
        popen_calls.append({"args": args, "kwargs": kwargs})
        return DummyProcess()

    monkeypatch.setattr(start_auto.platform, "system", lambda: "Windows")
    monkeypatch.setattr(start_auto.subprocess, "Popen", fake_popen)

    assert manager.start_frontend() is True
    assert len(popen_calls) == 1

    kwargs = popen_calls[0]["kwargs"]
    env = kwargs["env"]

    assert env["VITE_DEV_PROXY_TARGET"] == "http://127.0.0.1:8002"
    assert kwargs["cwd"] == frontend_dir
    assert kwargs["shell"] is False
