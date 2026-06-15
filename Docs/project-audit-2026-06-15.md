# 项目审查报告（2026-06-15）

> 状态说明：本报告反映 2026-06-15 审查时的初始问题清单；其中列出的 P0/P1 问题已在后续执行中大部分修复，当前落地状态以 `"docs/changelog.md"`、`"docs/api-route-inventory.md"` 与 `"docs/optimization-plan-2026-06-15.md"` 为准。

## 审查结论

项目目前可以完成后端测试和前端构建，但存在多处可直接影响数据安全与功能正确性的 P0 问题。建议先收敛旧版无鉴权路由，再处理前端认证刷新和 CI。

## P0：必须优先修复

### 1. 旧版视频 API 无鉴权，可读写和删除全部视频

- 证据：`"app/api/v1/api.py"` 仍挂载 `"app/api/v1/videos.py"`。
- 影响：`GET/PUT/DELETE /api/v1/videos/*` 均未使用 `get_current_user`，删除接口还会删除物理文件。
- 建议：移除旧路由，或统一接入用户鉴权、数据归属过滤和事务回滚。

### 2. 文件管理 API 无鉴权和用户隔离

- 证据：`"app/api/v1/endpoints/file_manager.py"` 的列表、下载、删除、修改时间和统计接口仅依赖数据库会话。
- 影响：未登录用户可枚举、下载或删除所有用户文件。
- 建议：所有接口增加鉴权；查询必须按 `UploadedFile.user_id` 过滤；删除仅允许文件所有者或管理员。

### 3. 旧上传 API 无鉴权、无文件大小限制

- 证据：`"app/api/v1/upload.py"` 被挂载到 `"/api/v1/upload"`，两个上传接口均无鉴权。
- 影响：匿名用户可以持续写入磁盘；该实现还绕过正式上传流程的元数据和用户归属逻辑。
- 建议：移除旧上传路由，保留正式分片上传和简单上传中的一套明确入口。

### 4. 提示词模板 API 全部无鉴权

- 证据：`"app/api/v1/prompt_template.py"` 的新增、修改、删除和使用计数接口均无当前用户依赖。
- 影响：匿名用户可以修改系统提示词；结合前端未净化的 Markdown 预览可形成持久化 XSS。
- 建议：读接口至少要求登录，写接口要求管理员；增加恶意 HTML 测试。

### 5. 前端提示词预览存在持久化 XSS

- 证据：`"frontend/src/pages/SystemConfig.tsx"` 直接将 `marked(...)` 结果传入 `dangerouslySetInnerHTML`。
- 影响：模板内容中的恶意 HTML/事件属性可能在管理员页面执行，并读取 localStorage 中的访问令牌和刷新令牌。
- 建议：使用 DOMPurify 等净化方案，或改用禁用原始 HTML 的 React Markdown 渲染。

### 6. WebSocket 身份认证可伪造

- 证据：前端只把 `userId` 放入 URL；后端 `"/ws/{user_id}"` 仅检查用户是否存在，没有验证令牌。另一条 token 路由仍是 TODO，并固定映射到 `demo_user`。
- 影响：攻击者可订阅其他用户的任务进度和实时消息。
- 建议：连接时验证 JWT，并从 token 提取用户 ID，禁止客户端声明身份。

## P1：重要错误

### 7. 视频静态路由被动态路由遮蔽

- 证据：`"app/api/v1/videos.py"` 先声明 `"/{video_id}"`，后声明 `"/platforms"`、`"/stats"` 和 DELETE `"/batch"`。
- 验证：路由匹配结果显示三个静态地址均命中 `get_video/delete_video`。
- 影响：这些接口实际返回 422，无法使用。
- 建议：若保留该模块，将静态路由放在动态路由之前，并增加路由可达性测试。

### 8. Axios 自动刷新令牌取错响应层级

- 证据：`"frontend/src/services/api.ts"` 从 `response.data` 解构 token，但后端返回结构是 `response.data.data`。
- 影响：访问令牌过期后会把 `undefined` 写入 localStorage，原请求无法正常重试。
- 建议：修正响应层级，并增加 401 -> refresh -> retry 单元测试。

### 9. AI 配置启用/停用接口缺少管理员鉴权

- 证据：`"app/api/v1/ai_config.py"` 的 activate/deactivate 没有 `require_admin`，而同文件其他写接口有。
- 影响：匿名用户可以切换当前 AI 配置状态。
- 建议：补齐管理员依赖和权限测试。

### 10. CORS 配置忽略 Settings，并开放全部来源

- 证据：`"app/app.py"` 固定 `allow_origins=["*"]` 且允许 credentials；`settings.cors_origins` 未使用。
- 影响：配置文件中的来源白名单无效，生产环境边界不清晰。
- 建议：读取 `settings.cors_origins`；生产环境禁止通配来源。

### 11. 数据库操作缺少统一事务策略

- 证据：API 目录有 68 处 `commit()`，端点目录仅少数显式 `rollback()`。
- 典型风险：文件删除先于数据库提交；提交失败时文件已丢失但记录仍在。
- 建议：统一使用事务上下文；文件系统操作设计补偿机制，避免数据库和磁盘状态分裂。

### 12. 测试未覆盖上述高风险路由

- 证据：当前 29 个测试集中于下载、上传和密码；文件管理、旧视频 API、提示词、WebSocket、token 自动刷新均无测试。
- 建议：优先增加未登录返回 401/403、跨用户访问拒绝、静态路由可达和 token 刷新测试。

## P2：冗余与可优化项

- `"app/api/v1/endpoints/videos.py"` 与 `"app/api/v1/endpoints/analysis.py"` 未被路由汇总挂载，属于疑似死代码。
- 根目录仍有 14 个 `"test_douyin_*.py"` 手工脚本，以及多组旧上传/分析实现；删除前应逐项确认用途。
- `"frontend/src/components/DebugInfoPanel.tsx"` 未发现引用，可列为删除候选。
- `"SystemConfig.tsx"` 3033 行、`"VideoAnalysis.tsx"` 2526 行，建议按业务区块拆分组件与 hooks，降低修改回归风险。
- 前端生产构建主 JS 为 1.71 MB（gzip 536.62 KB），应对页面做动态导入和代码分包。
- 生产构建启用 sourcemap，生成约 8.9 MB map；如不需要线上调试，建议仅在受控环境发布 source map。
- 代码仍有约 48 处 Pydantic V1 `dict/from_orm` 用法、50 处 `datetime.utcnow()`，后续升级 Pydantic 3/Python 新版本前应迁移。
- FastAPI `on_event("startup")` 已弃用，应迁移到 lifespan。
- mypy 目前仅检查两个文件，无法代表后端整体类型质量，建议逐目录扩大范围。
- `pyproject.toml` 要求 Python >=3.9，但 classifiers 仍声明 Python 3.8；Black target 也仍为 py38，版本口径不一致。

## 验证结果

- `python -m compileall -q "app"`：通过。
- `python -m flake8 "app"`：通过。
- 现有 mypy 两文件范围：通过。
- `python -m pytest -q`：29 passed，但有 FastAPI、Pydantic 和 `datetime.utcnow()` 弃用告警。
- `npm run build`：通过，有大 chunk 告警。
- `npm run lint`：失败；ESLint 9 找不到 `eslint.config.js/mjs/cjs`，当前 CI 前端 job 会失败。

## 建议执行顺序

1. 移除或封禁旧版无鉴权路由，补安全回归测试。
2. 修复文件管理、提示词、AI 配置和 WebSocket 权限。
3. 修复前端 token 刷新、XSS 和 ESLint 配置。
4. 统一事务与文件补偿策略。
5. 清理死代码和手工脚本，再进行前端拆分与依赖迁移。
