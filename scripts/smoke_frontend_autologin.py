"""前端自动登录冒烟测试

用途：
  - 启动前后端后，访问前端首页，验证是否能自动登录并进入功能页。

输出：
  - 仅输出布尔结果与当前路径，不打印 token 等敏感信息。
"""

from __future__ import annotations

import argparse
from pathlib import Path

from playwright.sync_api import sync_playwright


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Frontend autologin smoke test.")
    parser.add_argument(
        "--url",
        default="http://localhost:5173",
        help="Frontend base URL (default: http://localhost:5173).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    screenshot_path = Path("logs") / "smoke_frontend_autologin.png"
    screenshot_path.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(args.url, wait_until="networkidle")
        page.wait_for_timeout(1500)

        current_path = page.evaluate("window.location.pathname")
        has_access_token = page.evaluate("Boolean(window.localStorage.getItem('access_token'))")
        has_user = page.evaluate("Boolean(window.localStorage.getItem('user'))")

        page.screenshot(path=str(screenshot_path), full_page=True)
        browser.close()

    print(f"path={current_path}")
    print(f"has_access_token={has_access_token}")
    print(f"has_user={has_user}")


if __name__ == "__main__":
    main()
