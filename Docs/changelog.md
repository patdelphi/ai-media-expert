# Changelog

## 2026-06-15

- 新增阶段 0 安全基线：添加路由匿名访问拒绝测试与测试工厂（`"app/tests/test_route_security_baseline.py"`、`"app/tests/conftest.py"`、`"app/tests/factories.py"`）
- 修复提示词模板接口权限矩阵：读接口要求登录，写接口要求管理员，非管理员不可读取停用模板
- 修复 AI 配置启停接口权限：activate/deactivate 改为管理员专用，并补充异常回滚
- 修复 WebSocket 认证：移除 `"/ws/{user_id}"`，统一为 `"/ws?token=..."`，服务端从 JWT `sub` 解析身份
- 修复前端 WebSocket 连接方式：改为从本地 token 建立连接，不再暴露用户 ID
- 修复提示词 Markdown 预览 XSS：统一使用安全 Markdown 渲染函数，阻断原始 HTML 注入
- 停止挂载旧 `videos`、旧 `analysis`、旧 `upload` 路由，并新增 `app/tests/test_registered_routes.py` 固定正式/废弃路由边界
- 收敛下载相关重复前缀：`"/download/platforms"`、`"/download/statistics/*"`、`"/download/queue"` 不再出现二次拼接
- 新增安全测试：`"app/tests/test_prompt_template_security.py"`、`"app/tests/test_ai_config_security.py"`、`"app/tests/test_websocket_auth.py"`
- 收紧生产配置：CORS 改为读取 `"settings.cors_origins"`，增加 `TrustedHostMiddleware`，新增 `"/health/liveness"` 与 `"/health/readiness"` 健康检查
- 收紧前端生产构建：新增 `"frontend/.env.example"`，生产环境默认关闭 sourcemap，仍可通过 `VITE_SOURCEMAP` 显式覆盖
- 对齐工程门禁：更新 `".github/workflows/ci.yml"` 与 `".github/pull_request_template.md"`，补充 compile/type-check/security checks 与权限/数据库/API 影响检查项
- 拆分前端超大页面基础结构：提取 `"frontend/src/utils/markdown.ts"`、`"frontend/src/pages/video-analysis/types.ts"`、`"frontend/src/pages/video-upload/types.ts"`
- 引入前端单元测试：安装 Vitest / Testing Library / jsdom，新增 `"frontend/src/services/api.test.ts"` 与 `"frontend/src/utils/markdown.test.ts"`，并将 `npm run test` 纳入 CI
- 清理冗余代码：删除未挂载旧路由模块、未引用的 `"frontend/src/components/DebugInfoPanel.tsx"`，以及一批根目录/`"scripts"` 下的实验性脚本
