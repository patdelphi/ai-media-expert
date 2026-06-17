# API 路由清单

## 正式路由

- `"/api/v1/simple-upload/simple"`: 正式单文件上传入口
- `"/api/v1/upload/init"`: 正式分片上传初始化
- `"/api/v1/upload/chunk"`: 正式分片上传分块提交
- `"/api/v1/upload/control"`: 正式上传控制接口
- `"/api/v1/upload/progress/{upload_session_id}"`: 正式上传进度查询
- `"/api/v1/files/files"`: 正式文件管理列表入口
- `"/api/v1/video-analysis/*"`: 正式视频分析接口
- `"/api/v1/download/*"`: 正式下载任务接口
- `"/api/v1/download/platforms"`: 正式下载平台清单接口
- `"/api/v1/download/statistics/overview"`: 正式下载统计概览接口
- `"/api/v1/download/statistics/platforms"`: 正式下载统计平台接口
- `"/api/v1/download/statistics/trends"`: 正式下载趋势接口
- `"/api/v1/download/queue"`: 正式下载队列接口
- `"/api/v1/ai-config/*"`: 正式 AI 配置接口
- `"/api/v1/prompt-templates/*"`: 正式提示词模板接口
- `"/api/v1/video-auto-tags/*"`: 正式视频自动打标任务接口
- `"/api/v1/uploaded-files/{video_file_id}/tags"`: 视频历史标签集合（含生效/排除状态）
- `"/api/v1/uploaded-files/{video_file_id}/tags/revisions*"`: 视频标签修订（创建/列表/详情）
- `"/api/v1/websocket/ws?token=..."`: 正式 WebSocket 认证入口

## 兼容路由

- 当前无新增兼容别名；本轮直接停止挂载未使用旧路由。

## 已停挂旧路由

- `"/api/v1/videos/*"`: 旧视频管理 API，已停止注册
- `"/api/v1/analysis/*"`: 旧分析 API，已停止注册
- `"/api/v1/upload/"`: 旧单文件上传 API，已停止注册
- `"/api/v1/upload/batch"`: 旧批量上传 API，已停止注册
- `"/api/v1/upload/status/{video_id}"`: 旧上传状态 API，已停止注册
- `"/api/v1/download/platforms/platforms"`: 重复前缀平台接口，已停止注册
- `"/api/v1/download/statistics/statistics/*"`: 重复前缀统计接口，已停止注册
- `"/api/v1/download/queue/queue"`: 重复前缀队列接口，已停止注册

## 说明

- 前端当前仍使用 `"/api/v1/upload/*"`，但仅使用分片上传相关正式端点。
- 旧路由已由自动化测试 `app/tests/test_registered_routes.py` 固定，防止后续重新挂载。
