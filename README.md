# AI新媒体专家系统（开发版）

一个基于 AI 的视频上传、下载与内容分析平台（当前为开发版本，功能仍在快速迭代）。

## 项目状态

本仓库当前为 **开发版本（Development Preview）**：
- 接口/数据结构仍可能调整，暂不保证向后兼容
- 部分能力为"已接入 UI，但后端能力尚未完全闭环"的阶段
- 适合本地开发与联调验证，不建议直接用于生产环境

## 已实现功能

1. **本地视频上传（Simple Upload）** — 上传本地视频，异步提取元数据（时长/分辨率/帧率/编码等）
2. **视频分析（流式输出）** — 选择视频后进行 AI 分析，支持流式输出与进度展示
3. **用户系统与管理后台** — 登录/注册、用户管理（创建/禁用/删除/改密）、系统配置
4. **视频下载（开发中）** — 多平台支持（抖音/TikTok/B站/小红书/快手等），队列管理

## 技术栈

| 层 | 技术 |
|----|------|
| 后端 | FastAPI + SQLAlchemy + Pydantic + Celery |
| 前端 | React 19 + TypeScript + Vite + Tailwind CSS |
| 数据库 | SQLite（开发）/ PostgreSQL（生产） |
| 缓存/队列 | Redis |
| 视频处理 | FFmpeg + yt-dlp |
| 部署 | Docker Compose（app + redis + celery worker/beat + flower） |

## 快速开始

### 环境要求
- Python 3.10+
- Node.js 18+
- Redis（可选，用于 Celery）
- FFmpeg

### 后端

```bash
# 安装依赖（推荐用 uv）
uv sync
# 或
pip install -e .

# 复制并编辑环境配置
cp .env.example .env

# 启动
python -m app.main
```

开发工具：`pip install -e ".[dev]"`

### 前端

```bash
cd frontend
npm install
npm run dev
```

### 访问地址
- 前端: http://localhost:5173
- API 文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health

### 默认管理员账号（开发环境）

首次启动自动创建：
- 账号：`admin@example.com`
- 密码：`admin123`

生产环境请立即修改。

## API 端点概览

| 前缀 | 功能 |
|------|------|
| `/api/v1/auth` | 认证（登录/注册/刷新/登出） |
| `/api/v1/users` | 用户管理 |
| `/api/v1/simple-upload` | 视频上传 |
| `/api/v1/video-analysis` | AI 视频分析 |
| `/api/v1/video-download` | 视频下载 |
| `/api/v1/system/config` | 系统配置 |
| `/api/v1/tag-groups` | 标签组管理 |
| `/api/v1/ai-config` | AI 模型配置 |
| `/api/v1/prompt-templates` | 提示词模板 |

完整接口文档见启动后的 `/docs`（Swagger UI）。

## 项目结构

```
app/
  api/v1/endpoints/   # API 端点
  models/             # SQLAlchemy 模型
  schemas/            # Pydantic 校验
  services/           # 业务逻辑
  tasks/              # Celery 异步任务
  core/               # 配置、数据库、安全、日志
  crawlers/           # 平台爬虫（抖音/TikTok）
  tests/              # 测试
frontend/
  src/pages/          # 页面组件
  src/components/     # 通用组件
  src/services/       # API 调用
  src/types/          # TypeScript 类型
Docs/                 # 项目文档
```

## Docker 部署

```bash
docker-compose up -d    # 启动（app + redis + celery + flower）
docker-compose logs -f  # 查看日志
docker-compose down     # 停止
```

## 文档

- [代码审查与清理报告](Docs/code-review-cleanup-report.md)
- [待办事项](Docs/todo.md)
- [系统架构设计](Docs/03-系统架构设计文档.md)
- [API 接口设计](Docs/05-API接口设计文档.md)
- [部署运维](Docs/07-部署运维文档.md)

## 许可证

MIT
