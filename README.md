# 🎬 AI新媒体专家系统

一个基于AI的智能视频下载和内容分析平台，提供视频下载、内容分析、字幕处理等专业服务。

## 🎯 项目状态

- ✅ **前端已可用** - React + TypeScript + Vite
- ✅ **后端 API 已可用** - FastAPI + SQLAlchemy
- ✅ **基础工程化** - pytest 可稳定运行（自动化测试仅收集 `app/tests`）

## ✨ 主要功能

### 🎯 1号专家：视频下载专家
- **多平台支持**: TikTok、抖音、YouTube、哔哩哔哩等主流平台
- **智能下载**: 自动选择最佳质量，支持批量下载
- **格式转换**: 支持多种视频格式输出
- **任务管理**: 下载队列管理，进度实时跟踪
- **断点续传**: 网络中断自动恢复下载

### 🧠 2号专家：视频分析专家
- **AI内容分析**: 场景识别、物体检测、人脸识别
- **情感分析**: 视频情感倾向和观众反应预测
- **自动标签**: 智能生成内容标签和分类
- **质量评估**: 视频质量和专业度评分
- **多模态分析**: 视觉、音频、内容全方位分析

### 🌐 用户界面
- **Web界面**: 前后端分离（前端 React，后端提供 REST API）
- **API接口**: RESTful API 支持第三方集成
- **批量操作**: 支持批量下载和分析（部分能力按后端实现进度为准）

## 🚀 快速开始

### 前端应用

前端应用已完成开发，包含完整的用户界面和交互功能：

```bash
cd frontend
npm install
npm run dev
```

访问 http://localhost:5173 查看应用（以 Vite 输出为准）

**前端特性：**
- ✅ 现代化UI设计，简洁优雅
- ✅ 响应式布局，支持多设备
- ✅ 完整的路由系统和导航
- ✅ 6个核心功能模块全部实现
- ✅ TypeScript类型安全
- ✅ 组件化开发，易于维护

### 后端服务（开发中）

#### 环境要求
- Python 3.9+
- Redis（可选：用于 Celery broker/result backend）
- FFmpeg (用于视频处理)
- 8GB+ RAM (推荐)
- 100GB+ 可用磁盘空间

#### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/your-repo/ai-media-expert.git
cd ai-media-expert
```

2. **安装依赖**
```bash
pip install -e .
```

可选安装（按需开启重型能力）：
```bash
# 开发工具
pip install -e ".[dev]"

# AI 相关（重型依赖）
pip install -e ".[ai]"
```

3. **配置环境**
```bash
# 复制环境配置文件
cp .env.example .env

# 编辑配置文件
nano .env
```

4. **启动Redis (可选)**
```bash
# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis

# macOS
brew install redis
brew services start redis

# Windows
# 下载并安装Redis for Windows
```

5. **启动应用**
```bash
# 使用启动脚本 (推荐)
python start.py

# 或直接启动
python -m app.main
```

6. **访问界面**
- 前端: http://localhost:5173
- API 文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health

## 📖 使用指南

### 视频下载

1. **单个视频下载**
   - 在Web界面的"视频下载"标签页输入视频URL
   - 选择下载质量和格式
   - 点击"开始下载"按钮

2. **批量下载**
   - 使用"批量下载"功能
   - 每行输入一个视频URL
   - 系统会自动创建下载队列

3. **API调用**
```python
import requests

# 创建下载任务
response = requests.post(
    "http://localhost:8000/api/v1/download/tasks",
    json={
        "url": "https://www.tiktok.com/@user/video/123456789",
        "quality": "best",
        "format_preference": "mp4"
    },
    headers={"Authorization": "Bearer YOUR_TOKEN"}
)

print(response.json())
```

### 视频分析

1. **选择视频**
   - 在"视频分析"标签页选择已下载的视频
   - 或上传本地视频文件

2. **配置分析**
   - 选择分析类型：视觉、音频、内容或全面分析
   - 调整高级参数（可选）

3. **查看结果**
   - 分析完成后查看摘要和详细结果
   - 导出分析报告（JSON、PDF、Markdown格式）

### 任务管理

- **监控进度**: 在"任务管理"标签页查看所有任务状态
- **取消任务**: 可以取消正在进行的下载或分析任务
- **重试失败**: 自动重试失败的任务

## 🔧 配置说明

### 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `DATABASE_URL` | 数据库连接URL | `sqlite:///./ai_media_expert.db` |
| `REDIS_URL` | Redis连接URL | `redis://localhost:6379/0` |
| `DOWNLOAD_DIR` | 下载目录 | `./downloads` |
| `MAX_CONCURRENT_DOWNLOADS` | 最大并发下载数 | `5` |
| `DEVICE` | AI模型运行设备 | `cpu` |
| `LOG_LEVEL` | 日志级别 | `INFO` |

## 🧰 手工脚本

根目录存在若干 `"test_*.py"` / `"debug_*.py"` 手工验证脚本，默认不纳入 pytest 自动化测试。清单见 ["manual_tools.md"](file:///c:/Users/patde/Documents/GitHub/ai-media-expert/scripts/manual_tools.md)。

## 🐳 Docker部署

### 使用Docker Compose

```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

## 📊 系统架构

本系统采用微服务架构，主要包含以下组件：

- **API网关**: FastAPI提供RESTful API服务
- **Web界面**: Gradio构建的用户友好界面
- **任务队列**: Celery + Redis处理异步任务
- **数据存储**: SQLite/PostgreSQL + Redis缓存
- **AI引擎**: 多模态AI模型进行内容分析

## 🤝 贡献指南

欢迎提交Issue和Pull Request来改进项目！

## 📄 许可证

本项目采用 MIT 许可证。

---

**⭐ 如果这个项目对你有帮助，请给我们一个星标！**
AI新媒体专家
