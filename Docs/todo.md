# Code Review TODO

> 项目审查时间：2026-04-02
> 说明：开发中功能（首页、视频下载、视频列表）的已知未完成项不在此列，仅记录已有代码中的问题和优化点。

---

## 一、安全问题

### [HIGH] CORS 配置过于宽松
- **文件**: `app/app.py:26-32`
- **问题**: `allow_origins=["*"]` 允许所有来源，且 `allow_credentials=True`，存在 CSRF 风险
- **建议**: 改用 `config.py` 中已定义的 `cors_origins` 列表

### [HIGH] API 密钥明文存储
- **文件**: `app/models/video.py:360`
- **问题**: AIConfig 模型中 `api_key` 字段未加密存储
- **建议**: 复用 `system_config.py` 中已有的加密机制

### [HIGH] docker-compose 硬编码开发密钥
- **文件**: `docker-compose.yml:16-17`
- **问题**: `SECRET_KEY` 和 `JWT_SECRET_KEY` 硬编码在文件中
- **建议**: 移到 `.env` 文件，docker-compose 只引用变量

### [HIGH] file:// 协议打开文件
- **文件**: `frontend/src/pages/VideoDownload.tsx:869`
- **问题**: `window.open(file://...)` 存在安全风险，且浏览器通常会阻止
- **建议**: 通过后端接口提供文件下载

### [MEDIUM] JWT 客户端解析无校验
- **文件**: `frontend/src/services/auth.ts:186`
- **问题**: `shouldRefreshToken()` 直接 base64 解码 JWT，未验证签名
- **建议**: 使用 `jwt-decode` 库，或仅依赖后端返回的过期时间

### [MEDIUM] 公开配置接口信息泄露
- **文件**: `app/api/v1/endpoints/system_config.py:81-104`
- **问题**: `/public` 端点无认证，可能暴露敏感配置
- **建议**: 审查哪些配置真正需要公开，加白名单过滤

### [MEDIUM] datetime.utcnow() 已废弃
- **文件**: `app/core/security.py:34,124`
- **问题**: Python 3.12+ 中 `datetime.utcnow()` 已废弃
- **建议**: 改用 `datetime.now(timezone.utc)`

---

## 二、Bug / 运行时错误

### [HIGH] showNotification 参数顺序错误
- **文件**: `frontend/src/pages/VideoUpload.tsx:488,492`
- **问题**: 参数写反了，`showNotification('文件创建时间已更新' as any, 'success' as any)`
- **建议**: 改为 `showNotification('success', '文件创建时间已更新')`

### [HIGH] login 绕过 apiService 拦截器
- **文件**: `frontend/src/services/auth.ts:67`
- **问题**: 登录用原生 `fetch` 而非 `apiService`，错过统一错误处理
- **建议**: 统一使用 `apiService.post()`

---

## 三、内存泄漏 / 资源管理

### [HIGH] setInterval 未清理
- **文件**: `frontend/src/pages/VideoDownload.tsx:337-376`
- **问题**: `monitorDownloadProgress()` 创建的 interval 在组件卸载时未清除
- **建议**: 将 interval ID 存入 ref，在 useEffect cleanup 中 clearInterval

### [HIGH] WebSocket 监听器未移除
- **文件**: `frontend/src/pages/VideoDownload.tsx:95-103`
- **问题**: `setupWebSocketListeners()` 添加的监听器在 cleanup 中未 off
- **建议**: useEffect return 中调用 `websocketService.off()` 移除所有监听

### [MEDIUM] 上传分片合并无文件锁
- **文件**: `app/api/v1/endpoints/video_upload.py:231-246`
- **问题**: 并发请求可能同时合并同一文件的分片，导致文件损坏
- **建议**: 使用文件锁或数据库状态锁

### [MEDIUM] 下载失败未清理临时文件
- **文件**: `app/tasks/download_tasks.py:152-166`
- **问题**: 下载失败时未删除已下载的部分文件
- **建议**: 在 except 块中添加临时文件清理逻辑

---

## 四、后端代码质量

### [HIGH] 缺少数据库迁移工具
- **问题**: 项目无 Alembic 配置，模型变更无法追踪
- **建议**: 初始化 Alembic，建立迁移工作流

### [MEDIUM] N+1 查询
- **文件**: `app/api/v1/endpoints/videos.py:35-40`
- **问题**: join 查询未使用 eager loading
- **建议**: 使用 `joinedload()` 或 `selectinload()`

### [MEDIUM] 用户更新缺少事务回滚
- **文件**: `app/api/v1/endpoints/users.py:79-80`
- **问题**: `db.commit()` 无 try-except，部分更新时可能数据不一致
- **建议**: 包裹 try-except，异常时 `db.rollback()`

### [MEDIUM] 下载任务缺少唯一约束
- **文件**: `app/models/video.py:138-190`
- **问题**: DownloadTask 无 `(user_id, url)` 唯一约束，可能产生重复任务
- **建议**: 添加唯一约束或插入前检查

### [MEDIUM] 缺少数据库索引
- **文件**: `app/models/video.py`
- **问题**: DownloadTask 的 `user_id`、`status`、`created_at` 缺少索引
- **建议**: 添加 `index=True`

### [MEDIUM] 外部 HTTP 请求无重试
- **文件**: `app/services/download_service.py:305-315`
- **问题**: 外部 API 调用无重试和指数退避
- **建议**: 使用 `tenacity` 或手动实现重试逻辑

### [MEDIUM] 响应格式不统一
- **文件**: `app/api/v1/endpoints/file_manager.py:66-72`
- **问题**: 部分接口返回 `{"success": True, "files": ...}`，与其他接口格式不一致
- **建议**: 统一使用 ResponseModel 格式

### [LOW] 服务层全局单例
- **文件**: `app/services/download_service.py:662-663`
- **问题**: `download_service = DownloadService()` 全局实例，不利于测试
- **建议**: 改用 FastAPI 依赖注入

---

## 五、前端代码质量

### [MEDIUM] 大量 `as any` 类型断言
- **文件**: `frontend/src/pages/VideoDownload.tsx:157,164,168,802,814,831`
- **问题**: 绕过 TypeScript 类型检查
- **建议**: 补全类型定义，如在 `types/index.ts` 中给 DownloadTask status 加上 `'cancelled'`

### [MEDIUM] 未使用的 mock 下载代码
- **文件**: `frontend/src/pages/VideoDownload.tsx:379-425`
- **问题**: `processDownloadQueue()` 已定义但从未调用
- **建议**: 清理或正式集成

### [MEDIUM] 上传取消逻辑不完整
- **文件**: `frontend/src/pages/VideoUpload.tsx:406-414`
- **问题**: `removeFile()` 中取消上传的逻辑被注释掉了
- **建议**: 实现完整的 XHR abort

### [MEDIUM] 缺少 Error Boundary
- **问题**: 前端无 React Error Boundary 组件
- **建议**: 添加全局 Error Boundary 捕获渲染错误

### [MEDIUM] WebSocket 重连无指数退避
- **文件**: `frontend/src/services/websocketService.ts:74-82`
- **问题**: 连接超时 3 秒直接 reject，无重试
- **建议**: 实现指数退避重连

---

## 六、部署 / DevOps

### [MEDIUM] Docker 服务缺少资源限制
- **文件**: `docker-compose.yml`
- **问题**: 所有服务未设置 CPU/内存限制
- **建议**: 添加 `deploy.resources.limits`

### [MEDIUM] Redis/Celery 缺少健康检查
- **文件**: `docker-compose.yml`
- **问题**: 仅 app 服务有 healthcheck
- **建议**: 给 Redis 加 `redis-cli ping`，Celery 加 `celery inspect ping`

### [MEDIUM] 容器无日志轮转配置
- **文件**: `docker-compose.yml`
- **问题**: 未配置 logging driver，日志可能无限增长
- **建议**: 添加 `json-file` driver 并设置 `max-size`/`max-file`

### [LOW] 依赖版本未锁定上界
- **文件**: `pyproject.toml:22-52`
- **问题**: 大部分依赖用 `>=` 无上界，可能引入破坏性更新
- **建议**: 改为 `>=x.y,<(x+1)` 或使用 `~=`

---

## 七、CI / 测试

### [MEDIUM] mypy 只检查 2 个文件
- **文件**: `.github/workflows/ci.yml:24-26`
- **问题**: 类型检查覆盖面极小
- **建议**: 逐步扩展到整个 `app/` 目录

### [MEDIUM] CI 缺少安全扫描
- **问题**: 无 `pip-audit`、`bandit` 等安全检查
- **建议**: 在 CI 中添加依赖漏洞扫描和 SAST

### [MEDIUM] 测试覆盖不足
- **问题**: 仅 7 个测试文件，缺少 models、services、核心逻辑的测试
- **建议**: 添加覆盖率报告，设定最低阈值（如 70%）

### [MEDIUM] 集成测试仅手动触发
- **文件**: `.github/workflows/ci.yml:35`
- **问题**: 集成测试只在 `workflow_dispatch` 时运行
- **建议**: 至少在 main 分支 push 时自动运行

---

## 八、后端端点重复/冲突（最严重）

> 这是当前代码最大的问题：同一功能有 2~3 套实现，路由冲突，逻辑不一致。必须先清理再继续开发。

### [CRITICAL] 上传接口：3 套实现，路由冲突
- `app/api/v1/endpoints/video_upload.py` — 分片上传（session + chunk + merge）
- `app/api/v1/upload.py` — 简单上传 + 批量上传（用了废弃的 `from_orm()`）
- `app/api/v1/endpoints/simple_upload.py` — 简单上传 + 元数据提取
- **路由冲突**: `api.py:38` 和 `api.py:49` 都注册了 `/upload` 前缀
- **建议**: 保留 `simple_upload.py`（最完整），删除 `upload.py`。分片上传如需保留则改前缀为 `/chunked-upload`

### [CRITICAL] 视频分析接口：3 套实现
- `app/api/v1/endpoints/analysis.py` — AnalysisTask CRUD，但 TODO 注释"应该加入 Celery 队列"未实现
- `app/api/v1/analysis.py` — 另一套分析接口，用 AnalysisService 但未接 AI API
- `app/api/v1/endpoints/video_analysis.py` — 真正的 AI 分析 + 流式响应
- **建议**: 保留 `video_analysis.py`（唯一真正能用的），删除另外两个

### [CRITICAL] 视频列表接口：2 套实现，逻辑冲突
- `app/api/v1/endpoints/videos.py` — 按用户过滤，软删除
- `app/api/v1/videos.py` — 返回所有视频，无用户过滤，硬删除
- **建议**: 保留 `endpoints/videos.py`（有权限控制），删除 `api/v1/videos.py`

### [CRITICAL] 下载接口：2 套实现
- `app/api/v1/endpoints/download.py` — 仅 Task CRUD，TODO"应该加入 Celery 队列"未实现
- `app/api/v1/endpoints/video_download.py` — 解析 + 下载 + 任务管理，功能完整
- **建议**: 保留 `video_download.py`，删除 `download.py`

### 清理后应删除的文件
```
app/api/v1/upload.py              # 被 simple_upload.py 替代
app/api/v1/videos.py              # 被 endpoints/videos.py 替代
app/api/v1/analysis.py            # 被 endpoints/video_analysis.py 替代
app/api/v1/endpoints/analysis.py  # 被 endpoints/video_analysis.py 替代
app/api/v1/endpoints/download.py  # 被 endpoints/video_download.py 替代
```

### 清理后需修改 `api.py` 路由注册
- 删除重复的 `/upload` 注册（line 49）
- 删除对已移除模块的 include_router 调用

---

## 九、后端服务层冗余

### [HIGH] 分析服务重复
- `app/services/analysis_service.py` — `_analyze_audio()` 和 `_analyze_content()` 90% 是占位符
- `app/services/video_processing.py` — `analyze_video()` 与上面功能重叠
- **建议**: 合并为一个 `VideoAnalysisService`，删除占位代码

### [HIGH] simple_upload 用 threading 代替 Celery
- **文件**: `app/api/v1/endpoints/simple_upload.py:308-312`
- **问题**: 用 `threading.Thread` 做后处理，绕过任务队列，无重试、无进度、崩溃丢数据
- **建议**: 改用 Celery task

### [MEDIUM] Celery 任务 async/sync 混用
- `app/tasks/download_tasks.py:62` — Celery 任务内用 `asyncio.run()`
- `app/tasks/analysis_tasks.py:157` — 用 `.delay().get()` 阻塞等待（失去异步意义）
- **建议**: 统一为纯同步或纯异步模式

### [MEDIUM] 大量 TODO 占位代码
- `endpoints/analysis.py:82` — "这里应该将任务加入Celery队列"
- `endpoints/download.py:69` — "这里应该将任务加入Celery队列"
- `analysis_service.py:256,311` — 多处占位函数
- `analysis_tasks.py:243` — "TODO: 实现PDF报告生成"
- **建议**: 未实现的功能要么实现，要么删除，不要留空壳

---

## 十、后端模型冗余

### [MEDIUM] Video 模型字段重复
- **文件**: `app/models/video.py`
- `status` 和 `upload_status` 两个状态字段，语义重叠
- `codec`、`video_codec`、`audio_codec` 三个编解码字段，命名不一致
- `format` 字段与 `video_codec` 含义模糊
- **建议**: 只保留 `status`（合并状态值），只保留 `video_codec` + `audio_codec`，`format` 改名 `file_format`

---

## 十一、前端重复/冗余

### [HIGH] 类型定义重复
- `types/index.ts` 和 `services/auth.ts` 都定义了 `User` 接口
- `types/index.ts` 和 `services/videoDownloadApi.ts` 都定义了 `DownloadTask`
- **建议**: 统一从 `types/index.ts` 导出，service 文件只导入

### [HIGH] 通知机制不统一（3 种方式）
- `VideoUpload.tsx` — 自定义 `showNotification()` 函数
- `VideoDownload.tsx` — `setNotification()` state
- `Settings.tsx` — `react-hot-toast` 库
- **建议**: 统一用 `react-hot-toast`

### [MEDIUM] 工具函数重复
- `VideoDownload.tsx:44-69` 和 `services/videoUpload.ts:566-585` 都实现了 `formatSpeed()` / `formatTime()`
- **建议**: 提取到 `utils/formatters.ts`

### [MEDIUM] App.tsx 大量注释代码
- **文件**: `frontend/src/App.tsx:22-59`
- 注释掉的 state、breadcrumb、menu handler
- **建议**: 直接删除，需要时看 git history

### [MEDIUM] DebugInfoPanel 组件未使用
- **文件**: `frontend/src/components/DebugInfoPanel.tsx`
- 300+ 行代码，无任何地方引用
- **建议**: 删除

### [MEDIUM] VideoPlayer 过多 console.log
- **文件**: `frontend/src/components/VideoPlayer.tsx:66,76,81,148,174`
- 5 处 debug 日志
- **建议**: 删除或用环境变量控制

### [LOW] systemConfig 服务过度封装
- **文件**: `frontend/src/services/systemConfig.ts:216-239`
- `getAIConfigs()`、`getDownloadConfigs()` 等 5 个方法只是 `getConfigsByCategory('xxx')` 的包装
- **建议**: 删除这些包装方法，调用方直接用 `getConfigsByCategory()`

---

## 十二、可访问性 (Accessibility)

### [LOW] 平台图标缺少 aria-label
- **文件**: `frontend/src/pages/VideoDownload.tsx:587-597`
- **建议**: 给纯图标按钮添加 `aria-label`

### [LOW] 视频缩略图播放按钮缺少 aria-label
- **文件**: `frontend/src/pages/VideoList.tsx:359-362`
- **建议**: 添加 `aria-label="播放视频"`
