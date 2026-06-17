# Changelog

## 2026-06-17

- 收敛前端 AI `provider` 列表：`"frontend/src/services/aiConfig.ts"` 现在仅保留 `openai`、`anthropic`、`custom`，移除未真正支持的 `google`、`zhipu`、`ollama`
- 新增前端回归测试：`"frontend/src/services/aiConfig.test.ts"` 断言 `provider` 列表只返回 `openai`、`anthropic`、`custom`
- 明确百炼 OpenAI 兼容模式配置要求：当前系统会原样使用 `"api_base"`，不会自动补全路径；使用百炼时应填写完整接口地址 `https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions`
- 补充 Qwen 文件上传双 Key 约束说明：百炼临时上传使用 `"upload_api_key"`，模型解析继续使用 `"api_key"`，两者不混用
- 追加运行与排障记录：`"chat_history.md"` 已记录百炼上传成功但解析地址少 `/chat/completions` 导致 `404` 的定位结论
- 新增“视频自动打标 + 标签修订”闭环：
  - 自动打标任务（启动/详情/历史）
  - 历史标签集合（含生效/排除状态）
  - `x` 一键排除/恢复（带确认）
  - 修订版本历史（版本号/原因/明细）
  - 标签来源仅用颜色区分（AI / 人工修订）

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
- 修复 FastAPI 生命周期与文件暴露缺口：`"app/app.py"` 改为异步 `lifespan`，并移除公开 `"/uploads"` 静态挂载
- 新增受保护视频直链：`"app/api/v1/endpoints/file_manager.py"` 增加 `"/stream/{filename}"`，通过 query token 访问文件；`"app/api/v1/endpoints/video_analysis.py"` 与 `"frontend/src/pages/VideoUpload.tsx"` 同步切换到受保护播放地址
- 补强 Markdown 链接净化：`"frontend/src/utils/markdown.ts"` 增加危险协议过滤与渲染后 `href/src` 清洗，并补充 `"frontend/src/utils/markdown.test.ts"` 覆盖 `javascript:` 场景
- 修正文件统计权限返回：`"app/api/v1/endpoints/file_manager.py"` 的 `"/stats"` 透传 `403`，并补充 `"app/tests/test_file_manager_security.py"` 回归测试
- 增加启动与路由安全回归：`"app/tests/test_app_smoke.py"` 断言 `lifespan` 为异步生成器且未再注册 `"/uploads/{path:path}"`
- 收紧媒体流令牌：`"app/core/security.py"` 新增短时、单文件、只读的媒体专用 token；`"app/api/v1/endpoints/file_manager.py"` 的 `"/stream/{filename}"` 不再接受完整登录 token
- 修复播放器内联响应：`"app/api/v1/endpoints/file_manager.py"` 的流媒体返回改为 `content_disposition_type=\"inline\"`，避免视频被默认当作附件下载
- 降低视频理解链路泄露面：`"app/api/v1/endpoints/video_analysis.py"` 不再将带 token 的完整媒体 URL 持久化到数据库，`"app/services/ai_service.py"` 也不再记录敏感 URL 日志
- 补充媒体流安全回归：`"app/tests/test_file_manager_security.py"` 新增缺少 token、错误 token 类型、文件名不匹配、跨用户访问、inline 响应和 Range 能力断言
- 修复上传页播放器 401：`"app/api/v1/endpoints/file_manager.py"` 新增 `"/stream-token/{filename}"`，通过登录态为当前文件换发短时 media token；`"frontend/src/pages/VideoUpload.tsx"` 播放前先调用该接口，再使用换发 token 打开受保护流地址
- 补充播放换发测试：`"app/tests/test_file_manager_security.py"` 增加 `stream-token` 鉴权依赖、本人文件换发成功、跨用户文件换发拒绝断言
- 修复 Windows 启动脚本乱码兼容性：`"start_all_services.bat"` 去除易触发乱码执行的 emoji/项目符号输出，改用更稳定的 ASCII 文本，并将本地服务状态检查切换为 PowerShell `Invoke-WebRequest`
- 修复 Windows 停止脚本乱码兼容性：`"stop_all_services.bat"` 去除易触发乱码执行的特殊字符输出，并与 `"start_all_services.bat"` 统一后台窗口标题匹配规则
- 简化启动流程并合并窗口：`"start_all_services.bat"` 改为 `start /b` 单窗口启动后端/Celery/前端，不再弹多个 cmd；并移除自动安装依赖步骤
- 停止脚本适配单窗口：`"stop_all_services.bat"` 不再依赖窗口标题停止，改为端口清理 + PowerShell 识别 celery 进程
- 修正单窗口启动实现：`"start_all_services.bat"` 改为委托 `"start_auto.py"`，避免批处理中的引号/重定向兼容问题；`"start_auto.py"` 增加立即刷新的控制台输出、依赖只检查不安装、前端固定 `5173`、Celery 入口对齐 `app.tasks.celery`
- 降低单机启动噪音：`"start_auto.py"` 增加 Redis 端口探测，Redis 不可用时跳过 Celery 启动，避免持续连接错误刷屏
- 强制启用本地 Redis：`"start_auto.py"` 增加 `start_redis()`，启动顺序调整为 Redis → 后端 → Celery → 前端；未找到 `redis-server(.exe)` 时明确报错并提示设置 `REDIS_SERVER_PATH` 或安装 Redis
- 调整为 Redis/Celery 可选启动：`"start_auto.py"` 在 Redis 缺失时仍启动后端与前端，并明确提示“视频下载/队列任务不可用，视频 AI 解析主流程仍可用”；只有 Redis 可用时才启动 Celery
- 优化启动器状态摘要：`"start_auto.py"` 新增运行模式/Redis/Celery/下载队列/视频AI解析状态面板，并修正成功启动服务数统计
- 收紧启动器字符集：`"start_auto.py"`、`"start_all_services.bat"`、`"stop_all_services.bat"` 的控制台输出与源码文本统一为 ASCII，避免 Windows `cmd` 因中文/emoji/特殊字符出现解析或乱码问题
- 精简启动器交互：`"start_all_services.bat"` 去除 `color` 设置；`"start_auto.py"` 在前端健康检查通过后自动打开 `http://localhost:5173`
