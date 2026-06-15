# Docs（项目文档入口）

> 说明：仓库目前已有 `"docs/"`（历史文档），本目录 `"Docs/"` 作为统一的“入口与导航”。后续建议逐步将关键文档迁移到本目录下，减少重复与口径不一致。

## 快速导航

- 历史文档目录：`"docs/"`
- 审查报告：["project-audit-2026-06-15.md"](file:///c:/Users/patde/Documents/GitHub/ai-media-expert/docs/project-audit-2026-06-15.md)
- 优化计划：["optimization-plan-2026-06-15.md"](file:///c:/Users/patde/Documents/GitHub/ai-media-expert/docs/optimization-plan-2026-06-15.md)
- 路由清单：["api-route-inventory.md"](file:///c:/Users/patde/Documents/GitHub/ai-media-expert/docs/api-route-inventory.md)
- 变更记录：["changelog.md"](file:///c:/Users/patde/Documents/GitHub/ai-media-expert/docs/changelog.md)
- 服务启动指南：["README_SERVICES.md"](file:///c:/Users/patde/Documents/GitHub/ai-media-expert/README_SERVICES.md)
- 手工脚本清单：["manual_tools.md"](file:///c:/Users/patde/Documents/GitHub/ai-media-expert/scripts/manual_tools.md)

## 当前口径（以代码为准）

- 后端：FastAPI，默认端口 `8000`（`/docs`、`/health`、`/health/liveness`、`/health/readiness`）
- 前端：Vite dev server，默认端口 `5173`（以启动输出为准）
- 上传接口：统一为 `"/api/v1/simple-upload/simple"`（已移除 `"/minimal"` 与 `"/test-upload"` 路由）
- WebSocket：统一入口 `"/api/v1/websocket/ws?token=..."`，不再使用 URL 中的用户 ID 声明身份
- 质量门禁：后端执行 `compileall + flake8 + mypy + pytest`，前端执行 `lint + test + build`
- 依赖安装：默认依赖为“轻量可运行集”，重型能力通过 extras 安装（如 `.[ai]`、`.[ui]`）

## 默认管理员账号（开发环境）

首次启动后端服务时，会自动初始化数据库并创建默认管理员账号：
- 账号：`admin@example.com`
- 密码：`admin123`

