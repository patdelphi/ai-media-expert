# 🎬 AI新媒体专家系统（开发版）

一个基于 AI 的视频上传与内容分析平台（当前为开发版本，功能仍在快速迭代）。

## ⚠️ 项目状态（重要）

本仓库当前为 **开发版本（Development Preview）**：
- 接口/数据结构仍可能调整，暂不保证向后兼容
- 部分能力为“已接入 UI，但后端能力尚未完全闭环”的阶段
- 适合本地开发与联调验证，不建议直接用于生产环境

## ✅ 已实现功能（当前可用）

1. **本地视频上传（Simple Upload）**
   - 支持上传本地视频文件并保存到服务器
   - 上传完成后可在“最近上传文件”中查看与播放
   - 视频参数（时长/分辨率/帧率/比特率/音频等）会在上传后异步补齐

2. **视频分析（流式输出）**
   - 支持上传/选择视频后进行 AI 分析
   - 支持流式输出与进度展示（前端实时更新）

3. **用户系统与管理员后台**
   - 登录/注册
   - 管理员用户管理：创建/禁用/删除（软删除）/修改用户密码
   - 系统配置页基础能力

## 🧪 其他功能（未完全闭环/开发中）

- **视频下载**：页面与部分后端模块已存在，但稳定性/平台适配/队列闭环仍在完善中
- **任务队列**：Celery 配置存在，但默认 broker/result backend 可能采用内存后备方案，需按部署环境完善
- **更多分析维度/导出能力**：以 docs 规划与后续迭代为准

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
- **Web界面**: React + Vite 前端应用
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
