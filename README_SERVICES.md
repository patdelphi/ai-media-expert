# AI新媒体专家系统 - 服务启动指南

## 概述

本项目提供了多种方式来启动前后端服务，包括自动化脚本和手动启动方式。

## 🚀 快速启动（推荐）

### 方式一：Windows批处理脚本（推荐）
```bash
# 启动所有服务
start_all_services.bat

# 停止所有服务  
stop_all_services.bat
```

### 方式二：Python自动启动脚本
```bash
# 启动所有服务（跨平台）
python start_auto.py
```

### 方式三：原始启动脚本（交互式）
```bash
# 交互式启动（需要用户选择服务）
python start.py
```

## 📋 服务说明

### 后端服务
- **FastAPI应用**: 主要的Web API服务
- **端口**: 8000
- **访问地址**: http://localhost:8000
- **API文档**: http://localhost:8000/docs

### Celery工作进程
- **功能**: 处理后台任务（视频下载、分析等）
- **依赖**: Redis消息队列
- **日志**: logs/celery.log

### 前端服务
- **React + Vite**: 开发服务器
- **端口**: 5173
- **访问地址**: http://localhost:5173

## 🔧 环境要求

### 必需软件
- Python 3.9+
- Node.js 16+
- Redis（可选，用于生产环境）

### 配置文件
- `.env`: 环境配置文件（从.env.example复制）

## 📁 日志文件

所有服务的日志文件都保存在 `logs/` 目录下：

```
logs/
├── backend.log     # 后端API日志
├── celery.log      # Celery工作进程日志
└── frontend.log    # 前端开发服务器日志
```

## 🛠️ 手动启动方式

如果自动脚本无法使用，可以手动启动各个服务：

### 1. 启动后端API
```bash
# 初始化数据库
python -c "from app.core.db_manager import ensure_database_ready; ensure_database_ready()"

# 启动API服务
python -m uvicorn app.app:app --host 0.0.0.0 --port 8000 --reload
```

### 2. 启动Celery工作进程
```bash
python -m celery -A app.tasks.celery_app worker --loglevel=info
```

### 3. 启动前端开发服务器
```bash
cd frontend
npm install  # 首次运行需要安装依赖
npm run dev
```

## 🔍 服务状态检查

### 检查服务是否运行
```bash
# 检查后端API
curl http://localhost:8000/health

# 检查前端服务
curl http://localhost:5173
```

### 查看进程
```bash
# Windows
tasklist | findstr python
tasklist | findstr node

# Linux/Mac
ps aux | grep python
ps aux | grep node
```

## 🛑 停止服务

### 使用停止脚本
```bash
stop_all_services.bat
```

### 手动停止
- 按 `Ctrl+C` 停止当前运行的服务
- 或关闭对应的命令行窗口

### 强制停止（Windows）
```bash
# 停止所有Python进程
taskkill /f /im python.exe

# 停止所有Node.js进程  
taskkill /f /im node.exe
```

## 🐛 故障排除

### 常见问题

1. **前端服务启动失败**
   - 确保已安装 Node.js (版本 >= 16)
   - 在 Windows 环境下，npm 命令可能需要使用 `npm.cmd`
   - 检查前端目录是否存在 `node_modules` 文件夹
   - 运行 `cd frontend && npm install` 重新安装依赖

2. **后端服务启动失败**
   - 确保已激活虚拟环境
   - 检查 Python 版本 (>= 3.8)
   - 运行 `pip install -e .` 重新安装依赖
   - 检查 `.env` 配置文件是否存在

3. **Celery 工作进程启动失败**
   - 确保 Redis 服务正在运行
   - 检查 Redis 连接配置
   - 在 Windows 环境下可能需要额外配置

4. **端口占用问题**
   - 后端默认端口: 8000
   - 前端默认端口: 5173
   - 使用 `netstat -ano | findstr :8000` 检查端口占用
   - 使用 `taskkill /PID <PID> /F` 强制结束进程

### 修复记录

**2025-09-20 更新:**
- 修复了 Windows 环境下前端启动失败的问题
- 添加了 `platform` 模块导入
- 优化了 npm 命令在 Windows 下的执行方式
- 使用 `shell=True` 和 `npm.cmd` 确保命令正确执行

5. **端口被占用**
   ```bash
   # 查看端口占用
   netstat -ano | findstr :8000
   netstat -ano | findstr :5173
   
   # 杀死占用进程
   taskkill /f /pid <PID>
   ```

6. **依赖安装失败**
   ```bash
   # 清理并重新安装Python依赖
   pip cache purge
   pip install -e .
   
   # 清理并重新安装Node.js依赖
   cd frontend
   rm -rf node_modules package-lock.json
   npm install
   ```

7. **数据库连接失败**
   - 检查 `.env` 文件中的数据库配置
   - 确保数据库服务正在运行

8. **Redis连接失败**
   - 检查Redis服务是否启动
   - 验证 `.env` 文件中的Redis配置

### 查看详细日志
```bash
# 实时查看日志
tail -f logs/backend.log
tail -f logs/celery.log  
tail -f logs/frontend.log
```

## 📝 开发建议

1. **开发环境**: 使用 `start_all_services.bat` 快速启动所有服务
2. **调试模式**: 使用 `python start.py` 交互式选择需要的服务
3. **生产环境**: 使用 Docker Compose 部署

## 🔗 相关文档

- [项目README](README.md)
- [开发文档](DEVELOPMENT.md)
- [API文档](docs/05-API接口设计文档.md)
- [部署文档](docs/07-部署运维文档.md)