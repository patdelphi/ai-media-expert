# AI Media Expert 分阶段优化实施计划

> **执行要求：** 后续实施时使用 `superpowers:subagent-driven-development` 或 `superpowers:executing-plans`，逐任务执行并在每个阶段设置人工验收点。所有 Git 操作、删除操作、依赖安装、数据库迁移和外网调用必须再次获得用户确认。

**目标：** 在不破坏现有视频上传、解析、下载和用户管理功能的前提下，依次消除安全漏洞、接口分叉、正确性缺陷、CI 阻断和主要维护成本。

**总体架构：** 先用安全回归测试固定访问边界，再收敛旧版路由；随后修复前端认证和数据库/文件一致性。质量门禁稳定后才删除冗余代码，最后进行大文件拆分、前端分包和弃用 API 迁移。

**技术栈：** FastAPI、SQLAlchemy、Pydantic 2、Celery、React 19、TypeScript、Axios、Vite 6、ESLint 9、pytest、mypy、flake8。

---

## 当前执行状态（2026-06-15）

- [x] 阶段 0：建立安全基线
- [x] 阶段 1：P0 安全修复
- [x] 阶段 2：接口收敛与旧实现隔离
- [x] 阶段 3：正确性与事务一致性（按本计划当前范围完成）
- [x] 阶段 4：质量门禁与测试体系
- [x] 阶段 5：冗余清理
- [x] 阶段 6：性能、结构和生产配置优化

### 已完成摘要

- 安全边界：文件管理、提示词模板、AI 配置、WebSocket、Markdown 预览安全均已修复并有回归测试。
- 路由收敛：旧 `videos` / `analysis` / `upload` 路由已停挂并最终删除，下载相关重复前缀已收敛。
- 正确性：`get_db()` 已补异常回滚，前端 token 刷新链路已修复，FastAPI lifespan / Pydantic 2 / `utcnow()` 迁移已完成当前范围。
- 质量门禁：前端已接入 Vitest，CI 已统一为后端 `compile/lint/type/test` 与前端 `lint/test/build`。
- 清理：未挂载后端模块、未引用前端组件和一批实验性脚本已删除。
- 性能与配置：前端已完成懒加载与分包，后端已改用受控 CORS / TrustedHost / liveness / readiness，前端生产 sourcemap 默认关闭。

### 已解决的前置确认项

- [x] 允许安装 Vitest、Testing Library、jsdom
- [x] 允许删除未挂载模块、未引用组件和实验性脚本
- [ ] 是否存在仓库外部客户端仍在调用旧 API：未知，已通过文档与路由测试固定当前正式边界

---

## 一、执行规则

### 1. 阶段顺序

1. 阶段 0：建立基线与保护措施。
2. 阶段 1：修复 P0 安全问题。
3. 阶段 2：收敛接口与旧实现。
4. 阶段 3：修复正确性与事务一致性。
5. 阶段 4：恢复并强化质量门禁。
6. 阶段 5：清理冗余代码和文件。
7. 阶段 6：性能、结构和弃用 API 优化。

前一阶段未达到验收标准时，不进入下一阶段。

### 2. 通用验证命令

```powershell
python -m compileall -q "app"
python -m flake8 "app"
python -m mypy "app/core/config.py" "app/services/download_api_client.py" --follow-imports=skip --ignore-missing-imports --disable-error-code=import-untyped
python -m pytest -q
```

```powershell
Set-Location "frontend"
npm run lint
npm run build
```

### 3. Git 与回滚

- 本计划不自动执行 `commit/push/pull/merge`。
- 每个任务完成后先展示 `git diff --check`、测试结果和文件清单。
- 用户确认后才能创建阶段性提交。
- 数据库结构调整前必须备份 `"ai_media_expert.db"`，并验证备份可读取。
- 删除物理文件、脚本或模块前必须再次列出清单并获得确认。

---

# 阶段 0：建立安全基线

## Task 0.1：记录当前路由和测试基线

**文件：**

- 新建：`"app/tests/test_route_security_baseline.py"`
- 更新：`"Docs/changelog.md"`，若不存在则新建

- [ ] 写测试枚举以下高风险路由，断言其当前注册状态：旧视频 API、旧上传 API、文件管理 API、提示词 API、WebSocket、AI 配置启停接口。
- [ ] 运行测试并保存当前失败结果，确认测试能够复现审查报告中的问题。
- [ ] 不在该任务修改实现代码。

建议测试结构：

```python
import pytest
from httpx import ASGITransport, AsyncClient

from app.app import app


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("GET", "/api/v1/files/files"),
        ("GET", "/api/v1/videos/"),
        ("POST", "/api/v1/prompt-templates/"),
        ("POST", "/api/v1/ai-config/1/activate"),
    ],
)
async def test_sensitive_routes_reject_anonymous_users(method: str, path: str):
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.request(method, path)

    assert response.status_code in {401, 403}
```

**验收：** 测试应在现状下失败，且失败原因是接口允许匿名访问，而不是测试环境错误。

## Task 0.2：建立测试辅助工厂

**文件：**

- 新建：`"app/tests/conftest.py"`
- 新建：`"app/tests/factories.py"`

- [ ] 提取测试数据库、普通用户、管理员、认证头和文件记录工厂。
- [ ] 将后续安全测试统一放在临时 SQLite 数据库与临时上传目录中。
- [ ] 确保测试不会读取或修改真实 `"ai_media_expert.db"` 和 `"uploads"`。

核心 fixture：

```python
@pytest.fixture
def auth_headers(user) -> dict[str, str]:
    token = create_access_token(subject=user.id)
    return {"Authorization": f"Bearer {token}"}
```

**验收：** 任一测试运行前后，真实数据库大小和 `"uploads"` 内容保持不变。

---

# 阶段 1：P0 安全修复

## Task 1.1：保护文件管理接口并实施用户隔离

**文件：**

- 修改：`"app/api/v1/endpoints/file_manager.py"`
- 测试：`"app/tests/test_file_manager_security.py"`
- 可能修改：`"frontend/src/services/videoUpload.ts"`

- [ ] 先写匿名访问返回 401 的测试。
- [ ] 写用户 A 无法读取、下载、修改或删除用户 B 文件的测试。
- [ ] 写管理员是否可跨用户管理的明确测试；建议管理员允许查看，删除仍要求显式管理入口。
- [ ] 在所有文件接口增加 `get_current_user`。
- [ ] 查询条件加入 `UploadedFile.user_id == current_user.id`。
- [ ] 删除失败时执行 `db.rollback()`；数据库提交成功后再处理可补偿的文件清理，或使用临时重命名策略。
- [ ] 下载接口改用记录 ID 或保存文件名，避免原文件名重复造成误命中。

建议查询函数：

```python
def get_owned_file(db: Session, current_user: User, filename: str) -> UploadedFile:
    uploaded_file = db.query(UploadedFile).filter(
        UploadedFile.saved_filename == filename,
        UploadedFile.user_id == current_user.id,
    ).first()
    if not uploaded_file:
        raise HTTPException(status_code=404, detail="文件不存在")
    return uploaded_file
```

**验收：** 匿名请求 401；跨用户请求 404/403；本人请求成功；异常路径数据库回滚。

## Task 1.2：保护提示词模板接口

**文件：**

- 修改：`"app/api/v1/prompt_template.py"`
- 测试：`"app/tests/test_prompt_template_permissions.py"`

- [ ] 写匿名读写拒绝测试。
- [ ] 写普通用户可读取启用模板、不可新增/修改/删除的测试。
- [ ] 写管理员可完整 CRUD 的测试。
- [ ] 读取接口增加 `get_current_user`，写接口增加 `require_admin`。
- [ ] 将 `.dict()` 改为 `.model_dump()`。
- [ ] 为写操作补充 `try/except`、`rollback()` 和统一日志。

**验收：** 权限矩阵全部通过，模板管理行为不变。

## Task 1.3：修复提示词预览 XSS

**文件：**

- 修改：`"frontend/src/pages/SystemConfig.tsx"`
- 新建：`"frontend/src/utils/markdown.ts"`
- 测试：`"frontend/src/utils/markdown.test.ts"`，前提是阶段 4 引入前端测试框架；阶段 1 可先使用纯函数和构建校验
- 修改：`"frontend/package.json"`，安装净化依赖前必须获得确认

- [ ] 优先方案：使用 `DOMPurify.sanitize(marked.parse(content))` 封装 `renderSafeMarkdown()`。
- [ ] 若不允许新增依赖，改用 `react-markdown` 且不启用原始 HTML。
- [ ] 三处 `dangerouslySetInnerHTML` 统一调用安全函数，不允许页面自行拼接 HTML。
- [ ] 验证 `<script>`、`onerror`、`javascript:` 链接被移除。

```typescript
export function renderSafeMarkdown(content: string): string {
  return DOMPurify.sanitize(marked.parse(content) as string);
}
```

**验收：** 恶意模板无法执行脚本；正常 Markdown 标题、列表、代码块仍可显示。

## Task 1.4：修复 WebSocket 身份认证

**文件：**

- 修改：`"app/api/v1/endpoints/websocket.py"`
- 修改：`"app/core/security.py"`
- 修改：`"frontend/src/services/websocketService.ts"`
- 测试：`"app/tests/test_websocket_auth.py"`

- [ ] 删除以 URL 用户 ID 作为可信身份的逻辑。
- [ ] WebSocket 只保留一个正式入口：`"/ws?token=..."`。
- [ ] 服务端验证 JWT 类型、有效期和用户状态，并从 token 的 `sub` 获取用户 ID。
- [ ] 前端从认证服务取 access token，连接 URL 不再传 user ID。
- [ ] 删除 `demo_user/test_user` 绕过逻辑。
- [ ] 写无 token、无效 token、停用用户、有效用户四组测试。

```python
payload = verify_token(token)
if not payload or payload.get("type") != "access":
    await websocket.close(code=4001, reason="认证失败")
    return
user_id = int(payload["sub"])
```

**验收：** 用户只能接收自己的消息；伪造用户 ID 不再可用。

## Task 1.5：补齐 AI 配置启停权限

**文件：**

- 修改：`"app/api/v1/ai_config.py"`
- 测试：`"app/tests/test_ai_config_permissions.py"`

- [ ] 写匿名和普通用户启停配置被拒绝的测试。
- [ ] 为 activate/deactivate 增加 `require_admin`。
- [ ] 写管理员启停成功测试。
- [ ] 补异常回滚。

**阶段 1 验收门槛：**

- 所有 P0 安全测试通过。
- `pytest`、`flake8`、`compileall` 通过。
- 前端 build 通过。
- OpenAPI 中不存在匿名写入文件、视频、模板和 AI 配置的入口。

---

# 阶段 2：接口收敛与旧实现隔离

## Task 2.1：建立正式 API 使用清单

**文件：**

- 新建：`"Docs/api-route-inventory.md"`
- 修改：`"app/tests/test_registered_routes.py"`

- [ ] 列出前端实际使用的上传、视频、解析、下载、配置接口。
- [ ] 标记正式、兼容、废弃、未使用四类。
- [ ] 为正式路由写注册断言，为废弃路由写“不应注册”断言。

## Task 2.2：停止挂载旧视频与旧上传 API

**文件：**

- 修改：`"app/api/v1/api.py"`
- 候选删除：`"app/api/v1/videos.py"`、`"app/api/v1/upload.py"`
- 测试：`"app/tests/test_registered_routes.py"`
- 修改：相关文档

- [ ] 先确认前端无调用旧 API。
- [ ] 从路由汇总移除 `upload_router` 和 `videos_router`。
- [ ] 保留文件一个阶段但不挂载，观察测试与本地使用情况。
- [ ] 删除文件属于危险操作，必须单独确认。

**验收：** 旧无鉴权 API 返回 404，正式上传和视频列表仍可用。

## Task 2.3：处理两套分析 API

**文件：**

- 审查：`"app/api/v1/analysis.py"`
- 审查：`"app/api/v1/endpoints/analysis.py"`
- 主实现：`"app/api/v1/endpoints/video_analysis.py"`
- 修改：`"app/api/v1/api.py"`

- [ ] 对照前端调用和数据库模型，确认唯一正式分析流程。
- [ ] 将仍有价值的行为迁移到正式端点并先补测试。
- [ ] 停止挂载旧 `"/analysis"` 路由。
- [ ] 未挂载的 `endpoints/analysis.py` 列入阶段 5 删除候选。

## Task 2.4：规范重复路径前缀

**文件：**

- 修改：下载平台、统计、队列路由文件或 `"app/api/v1/api.py"`
- 测试：`"app/tests/test_registered_routes.py"`

- [ ] 将 `"/download/platforms/platforms"` 收敛为 `"/download/platforms"`。
- [ ] 将 `"/download/statistics/statistics/*"` 收敛为 `"/download/statistics/*"`。
- [ ] 将 `"/download/queue/queue"` 收敛为 `"/download/queue"`。
- [ ] 若前端已使用旧路径，提供一个版本周期的兼容别名并标记弃用。

**阶段 2 验收门槛：** 路由清单无分叉；所有正式路由有鉴权策略；旧路由不再注册。

---

# 阶段 3：正确性与一致性

## Task 3.1：修复 Axios 自动刷新令牌

**文件：**

- 修改：`"frontend/src/services/api.ts"`
- 修改：`"frontend/src/services/auth.ts"`
- 测试：`"frontend/src/services/api.test.ts"`

- [ ] 抽出不经过响应拦截器的 refresh client，避免刷新请求自身 401 时递归。
- [ ] 从 `response.data.data` 读取 token。
- [ ] 多个并发 401 只发起一次刷新请求，其他请求等待同一 Promise。
- [ ] 刷新失败统一清理认证状态并跳转登录页。
- [ ] 禁止通过 `apiService['api']` 访问 private 字段；公开 `baseUrl` 或提供登录方法。

```typescript
const payload = response.data.data;
const { access_token: accessToken, refresh_token: nextRefreshToken } = payload;
```

**验收：** 单请求刷新、并发刷新、刷新失败三组测试通过。

## Task 3.2：修复静态路由遮蔽

**文件：**

- 若旧视频模块仍保留：修改 `"app/api/v1/videos.py"`
- 测试：`"app/tests/test_registered_routes.py"`

- [ ] 将静态路由放在 `"/{video_id}"` 前。
- [ ] 更推荐在阶段 2 移除该模块；若已移除，本任务标记为“不适用”。
- [ ] 路由匹配测试必须直接断言 endpoint 名称。

## Task 3.3：统一 API 数据库事务边界

**文件：**

- 修改：`"app/core/database.py"`
- 分批修改：文件、上传、用户、配置、标签、下载相关写端点
- 测试：各端点测试文件

- [ ] 为 `get_db()` 增加异常回滚保护，但端点仍需明确事务边界。
- [ ] 写操作按“校验 -> 修改 ORM -> commit -> 外部副作用”排序。
- [ ] 所有捕获数据库异常的端点必须 rollback 后再转换异常。
- [ ] 不一次性改 68 处 commit；按模块分批，每批独立测试。

```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
```

## Task 3.4：实现数据库与文件系统补偿策略

**文件：**

- 新建：`"app/services/file_storage.py"`
- 修改：`"file_manager.py"`、`"simple_upload.py"`、`"video_upload.py"`
- 测试：`"app/tests/test_file_storage.py"`

- [ ] 封装安全保存、临时文件、原子替换、隔离删除和恢复。
- [ ] 上传先写临时文件，数据库提交成功后原子移动到正式路径。
- [ ] 删除先移动到回收临时路径；数据库提交成功后永久删除，提交失败则恢复。
- [ ] 所有路径必须解析并验证位于配置的上传根目录内。

**阶段 3 验收门槛：** token 刷新可用；异常注入测试证明数据库和磁盘不会出现单边成功。

---

# 阶段 4：质量门禁与测试体系

## Task 4.1：修复 ESLint 9 配置

**文件：**

- 新建：`"frontend/eslint.config.js"`
- 删除候选：旧 `.eslintrc*`，若存在
- 修改：`"frontend/package.json"`

- [ ] 使用 ESLint flat config 配置 TypeScript、React Hooks 和 React Refresh。
- [ ] 忽略 `dist`、`node_modules` 和生成文件。
- [ ] 运行 lint，逐个修复真实错误；不通过全局关闭规则掩盖问题。

```javascript
export default [
  { ignores: ['dist/**', 'node_modules/**'] },
  {
    files: ['**/*.{ts,tsx}'],
    languageOptions: { parser: tsParser },
    plugins: { '@typescript-eslint': tseslint, 'react-hooks': reactHooks },
    rules: { ...reactHooks.configs.recommended.rules },
  },
];
```

## Task 4.2：引入前端单元测试

**文件：**

- 修改：`"frontend/package.json"`
- 新建：`"frontend/vitest.config.ts"`
- 新建：`"frontend/src/test/setup.ts"`
- 修改：CI

- [ ] 安装 Vitest、Testing Library 和 jsdom 前先获得依赖安装确认。
- [ ] 优先覆盖 token 刷新、Markdown 净化和关键 service。
- [ ] 增加 `npm run test` 和 CI job。

## Task 4.3：扩大后端 mypy 范围

**文件：**

- 修改：`"pyproject.toml"`
- 修改：`".github/workflows/ci.yml"`

- [ ] 第一批纳入 `app/core`、`app/schemas`、`app/services/download_api_client.py`。
- [ ] 第二批纳入 `app/api/deps.py` 和安全敏感端点。
- [ ] 每批清零后才扩大，不使用大范围 ignore。

## Task 4.4：CI 与 PR 模板对齐

**文件：**

- 修改：`".github/workflows/ci.yml"`
- 修改：`".github/pull_request_template.md"`

- [ ] CI 强制后端 compile/lint/type/test 和前端 lint/test/build。
- [ ] 增加安全测试单独标识。
- [ ] PR 模板要求说明数据库、文件、权限和 API 兼容性影响。
- [ ] GitHub 分支保护设置属于外部操作，执行前确认。

**阶段 4 验收门槛：** 所有本地 checks 通过，CI 配置与 PR checklist 完全一致。

---

# 阶段 5：冗余清理

## Task 5.1：删除未挂载后端模块

**候选：**

- `"app/api/v1/endpoints/videos.py"`
- `"app/api/v1/endpoints/analysis.py"`
- 阶段 2 停挂的旧 `"app/api/v1/videos.py"`、`"upload.py"`、`"analysis.py"`

- [ ] 使用 `rg` 确认无导入、无路由注册、无文档依赖。
- [ ] 先删除一个模块并运行完整 checks。
- [ ] 删除操作前向用户展示最终清单。

## Task 5.2：清理根目录手工测试脚本

**候选：** 14 个 `"test_douyin_*.py"`、根目录其他 `"test_*.py"`、`"scripts/test_*.py"`。

- [ ] 分类为“仍需保留的手工诊断”“转为自动测试”“删除”。
- [ ] 保留脚本统一移动到 `"scripts/manual"`，移动操作前确认。
- [ ] 更新 `"scripts/manual_tools.md"` 和 `"TEST_REPORT.md"`。

## Task 5.3：清理未引用前端代码

**候选：**

- `"frontend/src/components/DebugInfoPanel.tsx"`
- 未使用 hooks、types 和 service 方法

- [ ] 使用 TypeScript、ESLint 和 `rg` 三种证据确认无引用。
- [ ] 删除后运行 lint、test、build。

**阶段 5 验收门槛：** 删除清单全部有证据；功能测试无回归；文档同步更新。

---

# 阶段 6：性能与长期维护

## Task 6.1：前端路由级代码分包

**文件：**

- 修改：`"frontend/src/App.tsx"`
- 修改：`"frontend/vite.config.ts"`

- [ ] 使用 `React.lazy()` 动态加载 Dashboard、VideoAnalysis、SystemConfig 等页面。
- [ ] 添加统一 Suspense loading 状态。
- [ ] 根据构建报告决定是否拆分 echarts、swiper、markdown vendor chunk。
- [ ] 目标：入口 JS gzip 明显低于当前 536 KB；单 chunk 不再超过 500 KB，或有明确例外说明。

## Task 6.2：拆分超大页面

**文件：**

- 拆分：`"SystemConfig.tsx"`、`"VideoAnalysis.tsx"`、`"VideoUpload.tsx"`
- 新建目录：对应页面 `components/`、`hooks/`、`types.ts`

- [ ] 先为现有关键交互补测试。
- [ ] 每次只提取一个职责：API 配置、提示词模板、用户管理、分析历史、实时状态。
- [ ] 页面组件保留状态编排，子组件只接收明确 props。
- [ ] 每次提取后运行前端完整 checks。

## Task 6.3：迁移弃用 API

**文件：**

- 修改：`"app/app.py"`，迁移 FastAPI lifespan。
- 修改：全局 `.dict()`/`from_orm()` 为 `model_dump()`/`model_validate()`。
- 修改：`datetime.utcnow()` 为项目统一 `utcnow()`。

- [ ] 每类迁移单独执行，不混在同一变更中。
- [ ] 开启 warnings-as-errors 的专项测试，先限定项目自身弃用告警。
- [ ] 修正 `pyproject.toml` 的 Python 版本 classifier 和 Black target。

## Task 6.4：生产配置收紧

**文件：**

- 修改：`"app/app.py"`、`"app/core/config.py"`、`".env.example"`
- 修改：`"frontend/vite.config.ts"`

- [x] CORS 使用 `settings.cors_origins`，生产环境禁止 `*`。
- [x] 配置 TrustedHostMiddleware。
- [x] 生产 build 默认不发布 source map；需要时上传到受控错误平台。
- [x] 健康检查区分 liveness 和 readiness，不泄露敏感详情。

**阶段 6 验收门槛：** 项目自身无弃用告警；生产配置有明确边界；构建体积达到目标。

---

# 二、总体验收标准

- 匿名用户无法访问任何私有数据或写接口。
- 普通用户无法读取、修改或删除其他用户的数据和文件。
- 管理员权限有自动化测试，且没有散落的特例绕过。
- WebSocket 身份完全来自已验证 JWT。
- Markdown 内容不能执行任意 HTML/JavaScript。
- 仅保留一套正式上传、视频管理和分析流程。
- 数据库失败和文件系统失败均有补偿测试。
- 后端 test/lint/type-check/compile 全绿。
- 前端 lint/test/build 全绿。
- CI 与 PR 模板 checks 一致。
- 删除候选经过引用检查、用户确认和完整回归测试。
- 文档、API 清单和 changelog 与实现同步。

# 三、建议里程碑

| 里程碑 | 范围 | 预计工作量 | 风险 |
|---|---|---:|---|
| M0 | 基线测试 | 0.5-1 天 | 低 |
| M1 | P0 安全修复 | 2-4 天 | 高 |
| M2 | API 收敛 | 1-3 天 | 中高 |
| M3 | 正确性与事务 | 2-4 天 | 高 |
| M4 | CI 和测试体系 | 1-3 天 | 中 |
| M5 | 冗余清理 | 1-2 天 | 中 |
| M6 | 性能与维护 | 3-6 天 | 中 |

总计约 10.5-23 个工程日，实际取决于旧接口是否仍被外部客户端使用，以及是否允许安装前端安全和测试依赖。

# 四、实施前必须再次确认的事项

1. 是否允许安装 DOMPurify、Vitest、Testing Library 等前端依赖。`Vitest / Testing Library / jsdom` 已确认允许并已执行。
2. 是否存在仓库外部客户端仍在调用旧 API。
3. 管理员是否允许跨用户查看或删除文件。
4. 是否允许删除或移动根目录手工脚本。已确认允许并已执行当前清理范围。
5. 是否执行数据库备份、迁移或生产配置调整。生产配置调整已在当前代码范围内完成，数据库备份/迁移未执行。
6. 每个阶段是否创建 Git 提交；提交信息和范围需单独确认。
