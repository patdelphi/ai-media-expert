# 代码审查与清理报告

> 日期：2026-04-02
> 执行者：Claude Opus 4.6

---

## 一、背景

项目在快速迭代过程中积累了大量重复代码：同一功能存在 2~3 套实现，路由冲突，前端类型定义矛盾，死代码散落各处。本次清理的目标是在不影响现有功能的前提下，删除冗余代码，修复冲突，让代码库回到简洁可维护的状态。

## 二、发现的问题

### 2.1 后端端点重复（最严重）

| 功能 | 冲突文件 | 保留文件 |
|------|---------|---------|
| 上传 | `api/v1/upload.py` + `endpoints/video_upload.py` + `endpoints/simple_upload.py` | `simple_upload.py` + `video_upload.py` |
| 分析 | `api/v1/analysis.py` + `endpoints/analysis.py` + `endpoints/video_analysis.py` | `video_analysis.py` |
| 视频列表 | `api/v1/videos.py` + `endpoints/videos.py` | `endpoints/videos.py` |
| 下载 | `endpoints/download.py` + `endpoints/video_download.py` | `video_download.py` |

`api.py` 中 `/upload` 前缀被注册了两次，造成路由冲突。

### 2.2 安全问题
- CORS 配置为 `allow_origins=["*"]`，允许任意来源
- API 密钥明文存储
- docker-compose 硬编码开发密钥

### 2.3 前端问题
- `User` 类型在 `types/index.ts`（id: string）和 `auth.ts`（id: number）中定义冲突
- `DownloadTask` 类型在两处定义，字段不一致
- `DebugInfoPanel` 组件 300+ 行从未被引用
- `App.tsx` 大量注释代码
- `VideoPlayer.tsx` 6 处 debug console.log

### 2.4 依赖问题
- `requires-python >= 3.9` 但 fastapi 要求 >= 3.10
- `aiohttp`、`qrcode`、`gmssl`、`tenacity` 被代码引用但未声明在依赖中

## 三、执行的清理

### Phase 1 — 清理后端重复端点 + 修复依赖

**删除文件（5 个，共 ~1300 行）：**
- `app/api/v1/upload.py` (154 行)
- `app/api/v1/videos.py` (172 行)
- `app/api/v1/analysis.py` (292 行)
- `app/api/v1/endpoints/analysis.py` (359 行)
- `app/api/v1/endpoints/download.py` (318 行)

**修改文件：**
- `app/api/v1/api.py` — 删除旧模块 import 和路由注册，消除 `/upload` 前缀冲突
- `pyproject.toml` — `requires-python` 改为 `>=3.10`，补齐 4 个缺失依赖

### Phase 2 — 修复 CORS

- `app/app.py` — `allow_origins=["*"]` 改为 `allow_origins=settings.cors_origins`
- 开发环境默认允许 `localhost:3000`、`localhost:3001`、`localhost:8080`

### Phase 3 — 前端清理死代码

- 删除 `frontend/src/components/DebugInfoPanel.tsx`（303 行，无任何引用）
- 清理 `App.tsx` 中 ~40 行注释代码
- 清理 `VideoPlayer.tsx` 中 6 处 console.log

### Phase 4 — 前端类型冲突修复

- 删除 `types/index.ts` 中重复的 `User` 接口（与 `auth.ts` 冲突）
- 删除 `types/index.ts` 中重复的 `DownloadTask` 接口（与 `videoDownloadApi.ts` 冲突）
- `VideoDownload.tsx` 改为从 `videoDownloadApi.ts` 导入 `DownloadTask`
- 补齐 `DownloadTask` 缺失字段（`download_speed`、`eta`）

### 测试清理

- 删除 `app/tests/test_download_endpoints.py`（针对已删除端点的过时测试）
- 删除根目录 19 个遗留的手工测试脚本（`test_douyin_*` 等）

## 四、验证结果

| 检查项 | 结果 |
|--------|------|
| 后端 pytest | 28 passed, 0 failed |
| 前端 tsc --noEmit | 0 errors |
| 应用启动 smoke test | 2 passed |

## 五、清理统计

| 指标 | 数值 |
|------|------|
| 删除文件 | 25 个 |
| 删除代码行 | ~5000 行 |
| 修改文件 | 8 个 |
| Commits | 5 个 |

## 六、下一步计划

以下问题已记录在 `Docs/todo.md` 中，按优先级排列：

### 高优先级

1. **数据库迁移工具**
   - 初始化 Alembic，建立迁移工作流
   - 当前模型变更无法追踪，风险较大

2. **API 密钥加密存储**
   - `app/models/video.py` 中 AIConfig 的 `api_key` 字段明文存储
   - 复用 `system_config.py` 已有的加密机制

3. **分析服务占位代码清理**
   - `analysis_service.py` 有 ~15 个返回硬编码值的占位函数
   - 实际工作的分析走 `ai_service.py`，占位代码应标记或移除

4. **前端通知机制统一**
   - 当前 3 种方式：自定义函数、state、react-hot-toast
   - 统一为 `react-hot-toast`

### 中优先级

5. **simple_upload threading 改 Celery**
   - 当前用 `threading.Thread` 做后处理，无重试、无进度、崩溃丢数据

6. **Celery 任务 async/sync 混用**
   - `download_tasks.py` 在 Celery 任务内用 `asyncio.run()`
   - `analysis_tasks.py` 用 `.delay().get()` 阻塞等待
   - 应统一为纯同步或纯异步

7. **Video 模型字段冗余**
   - `status` / `upload_status` 语义重叠
   - `codec` / `video_codec` / `audio_codec` 命名不一致
   - 需要数据库迁移配合

8. **前端内存泄漏修复**
   - `VideoDownload.tsx` 中 setInterval 和 WebSocket 监听器未在组件卸载时清理

### 低优先级

9. **Docker 部署加固** — 资源限制、健康检查、日志轮转
10. **CI 增强** — mypy 全量检查、安全扫描、覆盖率门槛
11. **依赖版本上界** — 防止破坏性更新
12. **可访问性** — aria-label 补全
