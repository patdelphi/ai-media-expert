# 🛠️ 开发指南

本文档为AI新媒体专家系统的开发者提供详细的开发指南和最佳实践。

## 📁 项目结构（以当前代码为准）

```
ai-media-expert/
├── "app"/                        # 主应用目录
│   ├── __init__.py
│   ├── "app.py"                  # FastAPI 应用入口（Uvicorn: "app.app:app"）
│   ├── "main.py"                 # CLI 入口（"python -m app.main"）
│   ├── "api"/                    # API接口层
│   │   ├── __init__.py
│   │   ├── deps.py               # API依赖项
│   │   └── v1/                   # API v1版本
│   │       ├── __init__.py
│   │       ├── api.py            # 路由汇总（单一真源）
│   │       └── endpoints/        # 具体端点实现
│   │           ├── auth.py       # 认证相关
│   │           ├── users.py      # 用户管理
│   │           ├── videos.py     # 视频管理
│   │           ├── download.py   # 下载功能
│   │           └── analysis.py   # 分析功能
│   ├── "core"/                   # 核心模块
│   │   ├── __init__.py
│   │   ├── config.py             # 配置管理
│   │   ├── database.py           # 数据库连接
│   │   ├── security.py           # 安全工具
│   │   └── app_logging.py        # 日志配置
│   ├── models/                   # 数据模型
│   │   ├── __init__.py
│   │   ├── user.py               # 用户模型
│   │   └── video.py              # 视频相关模型
│   ├── schemas/                  # Pydantic模式
│   │   ├── __init__.py
│   │   ├── common.py             # 通用模式
│   │   ├── auth.py               # 认证模式
│   │   └── video.py              # 视频模式
│   ├── services/                 # 业务逻辑层
│   │   ├── __init__.py
│   │   ├── download_service.py   # 下载服务
│   │   ├── analysis_service.py   # 分析服务
│   │   └── platform_adapters.py  # 平台适配器
│   ├── "tasks"/                  # 异步任务
│   │   ├── __init__.py
│   │   ├── celery_app.py         # Celery配置
│   │   ├── celery.py             # Celery 入口（`-A app.tasks.celery`）
│   │   ├── download_tasks.py     # 下载任务
│   │   ├── analysis_tasks.py     # 分析任务
│   │   └── maintenance_tasks.py  # 维护任务
├── "docs"/                       # 历史文档
├── "Docs"/                       # 文档入口与导航
├── "scripts"/                    # 运维/一次性脚本
├── "app/tests"/                  # 自动化测试（pytest 仅收集此目录）
├── "uploads"/                    # 上传目录
├── "downloads"/                  # 下载目录
├── "models"/                     # AI模型缓存
├── "logs"/                       # 日志文件
├── ".env"                        # 环境配置
├── ".env.example"                # 环境配置示例
├── "docker-compose.yml"          # Docker 编排
├── "Dockerfile"                  # Docker 镜像
├── "pyproject.toml"              # 项目配置
├── "start.py"                    # 启动脚本
└── "README.md"                   # 项目说明
```

## 🏗️ 架构设计

### 分层架构

1. **表示层 (Presentation Layer)**
   - 前端 React 应用
   - FastAPI REST接口
   - WebSocket实时通信（按实现为准）

2. **业务逻辑层 (Business Logic Layer)**
   - 服务类 (Services)
   - 业务规则和流程
   - 数据验证和转换

3. **数据访问层 (Data Access Layer)**
   - SQLAlchemy ORM模型
   - 数据库操作
   - 缓存管理

4. **基础设施层 (Infrastructure Layer)**
   - 配置管理
   - 日志系统
   - 安全认证
   - 任务队列

### 设计模式

- **依赖注入**: 使用FastAPI的依赖注入系统
- **工厂模式**: 平台适配器的创建
- **策略模式**: 不同分析类型的处理
- **观察者模式**: 任务进度通知
- **单例模式**: 配置和日志管理

## 🔧 开发环境设置

### 1. 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd ai-media-expert

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# 或
.venv\Scripts\activate     # Windows

# 安装开发依赖
pip install -e ".[dev]"
```

### 2. 开发工具配置

#### VS Code配置

创建 `.vscode/settings.json`:

```json
{
    "python.defaultInterpreterPath": "./.venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": false,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "python.sortImports.args": ["--profile", "black"],
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true
    }
}
```

#### Pre-commit钩子

```bash
# 安装pre-commit
pip install pre-commit

# 安装钩子
pre-commit install
```

创建 `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.11.0
    hooks:
      - id: black
        language_version: python3

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: ["--profile", "black"]

  - repo: https://github.com/pycqa/flake8
    rev: 6.1.0
    hooks:
      - id: flake8
        args: ["--max-line-length=88", "--extend-ignore=E203,W503"]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.1
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
```

## 🧪 测试指南

### 自动化测试位置

- 自动化测试目录：`"app/tests"`
- 根目录 `"test_*.py"` / `"debug_*.py"`：手工脚本，不参与 pytest 收集，清单见 `"scripts/manual_tools.md"`

### 运行测试

```bash
python -m pytest -q
python -m compileall app
```

## 📝 编码规范

### Python代码风格

- 使用 **Black** 进行代码格式化
- 使用 **isort** 进行导入排序
- 使用 **flake8** 进行代码检查
- 使用 **mypy** 进行类型检查

### 命名规范

- **文件名**: 小写字母，下划线分隔 (`user_service.py`)
- **类名**: 大驼峰命名 (`UserService`)
- **函数名**: 小写字母，下划线分隔 (`get_user_info`)
- **变量名**: 小写字母，下划线分隔 (`user_id`)
- **常量名**: 大写字母，下划线分隔 (`MAX_FILE_SIZE`)

### 文档字符串

使用Google风格的文档字符串:

```python
def download_video(url: str, quality: str = "best") -> Dict[str, Any]:
    """下载视频文件
    
    Args:
        url: 视频URL
        quality: 视频质量，默认为"best"
    
    Returns:
        包含下载结果的字典
    
    Raises:
        ValueError: 当URL无效时
        DownloadError: 当下载失败时
    """
    pass
```

### 类型注解

所有函数都应该有完整的类型注解:

```python
from typing import Dict, List, Optional, Union

def process_videos(
    video_ids: List[int], 
    options: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Union[str, int]]]:
    """处理视频列表"""
    pass
```

## 🔄 开发流程

### Git工作流

1. **创建功能分支**
```bash
git checkout -b feature/video-analysis
```

2. **开发和提交**
```bash
# 添加文件
git add .

# 提交更改
git commit -m "feat: add video analysis functionality"
```

3. **推送和创建PR**
```bash
git push origin feature/video-analysis
# 在GitHub上创建Pull Request
```

### 提交信息规范

使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范:

- `feat:` 新功能
- `fix:` 错误修复
- `docs:` 文档更新
- `style:` 代码格式化
- `refactor:` 代码重构
- `test:` 测试相关
- `chore:` 构建过程或辅助工具的变动

示例:
```
feat: add video download functionality
fix: resolve authentication token expiration issue
docs: update API documentation
```

## 🚀 部署指南

### 本地开发部署

```bash
# 启动Redis
redis-server

# 启动Celery Worker
celery -A app.tasks.celery worker --loglevel=info

# 启动应用
python start.py
```

### Docker部署

```bash
# 构建镜像
docker build -t ai-media-expert .

# 使用Docker Compose
docker-compose up -d
```

### 生产环境部署

1. **环境配置**
```bash
# 设置生产环境变量
export ENVIRONMENT=production
export DEBUG=false
export SECRET_KEY=your-production-secret
```

2. **数据库迁移**
```bash
# 运行数据库迁移
alembic upgrade head
```

3. **启动服务**
```bash
# 使用Gunicorn启动
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

## 🐛 调试技巧

### 日志调试

```python
from app.core.logging import download_logger

# 记录调试信息
download_logger.debug("Processing video", video_id=123, url="https://...")

# 记录错误
download_logger.error("Download failed", error=str(e), exc_info=True)
```

### 断点调试

```python
# 使用pdb
import pdb; pdb.set_trace()

# 使用ipdb (推荐)
import ipdb; ipdb.set_trace()
```

### 性能分析

```python
# 使用cProfile
import cProfile
cProfile.run('your_function()')

# 使用line_profiler
@profile
def your_function():
    pass
```

## 📊 监控和维护

### 健康检查

```python
# 添加自定义健康检查
@app.get("/health/custom")
def custom_health_check():
    # 检查数据库连接
    # 检查Redis连接
    # 检查磁盘空间
    return {"status": "healthy"}
```

### 性能监控

```python
# 添加性能指标
from prometheus_client import Counter, Histogram

REQUEST_COUNT = Counter('requests_total', 'Total requests')
REQUEST_LATENCY = Histogram('request_duration_seconds', 'Request latency')

@REQUEST_LATENCY.time()
def process_request():
    REQUEST_COUNT.inc()
    # 处理请求
```

## 🔧 常见问题解决

### 依赖冲突

```bash
# 清理pip缓存
pip cache purge

# 重新安装依赖
pip install --force-reinstall -e .
```

### 数据库问题

```bash
# 重置数据库
rm ai_media_expert.db
python -c "from app.core.database import create_tables; create_tables()"
```

### Celery任务问题

```bash
# 清理Celery队列
celery -A app.tasks.celery_app purge

# 重启Worker
celery -A app.tasks.celery_app worker --loglevel=info
```

## 📚 参考资源

- [FastAPI文档](https://fastapi.tiangolo.com/)
- [SQLAlchemy文档](https://docs.sqlalchemy.org/)
- [Celery文档](https://docs.celeryproject.org/)
- [Gradio文档](https://gradio.app/docs/)
- [yt-dlp文档](https://github.com/yt-dlp/yt-dlp)

## 🤝 贡献指南

1. Fork项目
2. 创建功能分支
3. 编写代码和测试
4. 确保所有测试通过
5. 提交Pull Request
6. 等待代码审查

感谢您的贡献！
