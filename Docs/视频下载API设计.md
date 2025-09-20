# 视频下载功能API设计

## 1. 设计概述

### 1.1 设计原则
1. **RESTful设计**：遵循REST API设计规范
2. **统一响应格式**：与现有API保持一致的响应结构
3. **异步处理**：下载任务采用异步处理模式
4. **错误处理**：完善的错误处理和状态码
5. **安全性**：用户认证和权限控制
6. **可扩展性**：支持新平台和功能的扩展

### 1.2 技术架构
```
Frontend (React/TypeScript)
    ↓ HTTP/WebSocket
Backend API (FastAPI/Python)
    ↓ HTTP
Douyin_TikTok_Download_API (独立服务)
    ↓ 
Database (PostgreSQL)
```

## 2. API接口设计

### 2.1 基础响应格式

#### 2.1.1 统一响应结构
```typescript
interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
  code?: number;
  timestamp?: string;
}

// 分页响应
interface PaginatedResponse<T> extends ApiResponse<T[]> {
  pagination: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
  };
}
```

### 2.2 平台管理API

#### 2.2.1 获取支持的平台列表
```http
GET /api/v1/download/platforms
```

**响应示例：**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "douyin",
      "display_name": "抖音",
      "icon": "fab fa-tiktok",
      "color": "text-red-500",
      "enabled": true,
      "supported_features": ["video", "image"],
      "quality_options": ["720p", "1080p", "original"],
      "format_options": ["mp4"],
      "rate_limit": 10,
      "timeout": 300
    }
  ]
}
```

#### 2.2.2 更新平台配置（管理员）
```http
PUT /api/v1/download/platforms/{platform_id}
Authorization: Bearer {token}
Content-Type: application/json

{
  "enabled": true,
  "rate_limit": 15,
  "timeout": 300,
  "config": {
    "custom_setting": "value"
  }
}
```

### 2.3 URL解析API

#### 2.3.1 解析视频URL
```http
POST /api/v1/download/parse
Authorization: Bearer {token}
Content-Type: application/json

{
  "url": "https://www.douyin.com/video/7234567890123456789",
  "platform": "douyin"  // 可选，自动检测
}
```

**响应示例：**
```json
{
  "success": true,
  "data": {
    "platform": "douyin",
    "video_id": "7234567890123456789",
    "title": "精彩视频标题",
    "description": "视频描述内容",
    "author": {
      "name": "作者名称",
      "id": "author_id_123",
      "avatar_url": "https://example.com/avatar.jpg"
    },
    "thumbnail_url": "https://example.com/thumbnail.jpg",
    "duration": 30,
    "view_count": 10000,
    "like_count": 500,
    "comment_count": 100,
    "share_count": 50,
    "available_qualities": ["720p", "1080p"],
    "available_formats": ["mp4"],
    "subtitles_available": false,
    "file_size_estimate": 15728640,
    "upload_date": "2024-01-15"
  }
}
```

#### 2.3.2 批量解析URL
```http
POST /api/v1/download/parse/batch
Authorization: Bearer {token}
Content-Type: application/json

{
  "urls": [
    "https://www.douyin.com/video/7234567890123456789",
    "https://www.tiktok.com/@user/video/7234567890123456790"
  ]
}
```

### 2.4 下载任务API

#### 2.4.1 创建下载任务
```http
POST /api/v1/download/tasks
Authorization: Bearer {token}
Content-Type: application/json

{
  "url": "https://www.douyin.com/video/7234567890123456789",
  "platform": "douyin",
  "quality": "1080p",
  "format_preference": "mp4",
  "audio_only": false,
  "download_subtitles": false,
  "priority": 5,
  "options": {
    "custom_filename": "my_video",
    "download_thumbnail": true
  }
}
```

**响应示例：**
```json
{
  "success": true,
  "data": {
    "task_id": 123,
    "status": "pending",
    "url": "https://www.douyin.com/video/7234567890123456789",
    "platform": "douyin",
    "quality": "1080p",
    "format_preference": "mp4",
    "priority": 5,
    "created_at": "2024-01-15T10:30:00Z",
    "estimated_completion": "2024-01-15T10:35:00Z"
  }
}
```

#### 2.4.2 获取下载任务列表
```http
GET /api/v1/download/tasks?page=1&limit=20&status=all&platform=all&sort=created_at&order=desc
Authorization: Bearer {token}
```

**查询参数：**
- `page`: 页码（默认1）
- `limit`: 每页数量（默认20，最大100）
- `status`: 任务状态过滤（all, pending, analyzing, downloading, completed, failed, cancelled）
- `platform`: 平台过滤（all, douyin, tiktok, bilibili等）
- `sort`: 排序字段（created_at, updated_at, priority）
- `order`: 排序方向（asc, desc）

**响应示例：**
```json
{
  "success": true,
  "data": [
    {
      "id": 123,
      "url": "https://www.douyin.com/video/7234567890123456789",
      "platform": "douyin",
      "status": "completed",
      "progress": 100,
      "video_title": "精彩视频标题",
      "author_name": "作者名称",
      "thumbnail_url": "https://example.com/thumbnail.jpg",
      "duration": 30,
      "file_size": 15728640,
      "quality": "1080p",
      "format_preference": "mp4",
      "file_path": "/downloads/user_123/video_123.mp4",
      "download_speed": 1048576,
      "created_at": "2024-01-15T10:30:00Z",
      "started_at": "2024-01-15T10:30:05Z",
      "completed_at": "2024-01-15T10:32:30Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 50,
    "totalPages": 3
  }
}
```

#### 2.4.3 获取单个下载任务详情
```http
GET /api/v1/download/tasks/{task_id}
Authorization: Bearer {token}
```

#### 2.4.4 取消下载任务
```http
DELETE /api/v1/download/tasks/{task_id}
Authorization: Bearer {token}
```

#### 2.4.5 重试下载任务
```http
POST /api/v1/download/tasks/{task_id}/retry
Authorization: Bearer {token}
```

#### 2.4.6 批量操作下载任务
```http
POST /api/v1/download/tasks/batch
Authorization: Bearer {token}
Content-Type: application/json

{
  "action": "cancel", // cancel, retry, delete
  "task_ids": [123, 124, 125]
}
```

### 2.5 文件管理API

#### 2.5.1 下载文件
```http
GET /api/v1/download/files/{task_id}
Authorization: Bearer {token}
```

**响应：** 文件流下载

#### 2.5.2 获取文件信息
```http
GET /api/v1/download/files/{task_id}/info
Authorization: Bearer {token}
```

**响应示例：**
```json
{
  "success": true,
  "data": {
    "task_id": 123,
    "filename": "video_123.mp4",
    "file_size": 15728640,
    "file_path": "/downloads/user_123/video_123.mp4",
    "mime_type": "video/mp4",
    "created_at": "2024-01-15T10:32:30Z",
    "expires_at": "2024-02-14T10:32:30Z",
    "download_count": 3
  }
}
```

#### 2.5.3 删除下载文件
```http
DELETE /api/v1/download/files/{task_id}
Authorization: Bearer {token}
```

### 2.6 统计分析API

#### 2.6.1 获取用户下载统计
```http
GET /api/v1/download/statistics/user?period=7d&platform=all
Authorization: Bearer {token}
```

**查询参数：**
- `period`: 统计周期（1d, 7d, 30d, 90d, 1y）
- `platform`: 平台过滤

**响应示例：**
```json
{
  "success": true,
  "data": {
    "total_downloads": 150,
    "successful_downloads": 140,
    "failed_downloads": 10,
    "success_rate": 93.33,
    "total_size": 1073741824,
    "total_duration": 7200,
    "avg_download_speed": 1048576,
    "platform_breakdown": {
      "douyin": {
        "count": 80,
        "success_rate": 95.0
      },
      "tiktok": {
        "count": 70,
        "success_rate": 91.4
      }
    },
    "daily_stats": [
      {
        "date": "2024-01-15",
        "downloads": 20,
        "success": 19,
        "failed": 1
      }
    ]
  }
}
```

#### 2.6.2 获取系统统计（管理员）
```http
GET /api/v1/download/statistics/system?period=30d
Authorization: Bearer {admin_token}
```

### 2.7 WebSocket实时通信

#### 2.7.1 连接WebSocket
```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/download/ws?token={jwt_token}');
```

#### 2.7.2 消息格式

**任务状态更新：**
```json
{
  "type": "task_update",
  "data": {
    "task_id": 123,
    "status": "downloading",
    "progress": 45,
    "download_speed": 1048576,
    "eta": 120,
    "message": "正在下载..."
  }
}
```

**任务完成通知：**
```json
{
  "type": "task_completed",
  "data": {
    "task_id": 123,
    "status": "completed",
    "file_path": "/downloads/user_123/video_123.mp4",
    "file_size": 15728640,
    "duration": 145
  }
}
```

**错误通知：**
```json
{
  "type": "task_error",
  "data": {
    "task_id": 123,
    "status": "failed",
    "error_message": "下载失败：网络连接超时",
    "error_code": "NETWORK_TIMEOUT"
  }
}
```

## 3. 服务架构设计

### 3.1 后端服务结构

#### 3.1.1 目录结构
```
app/
├── api/
│   ├── v1/
│   │   ├── endpoints/
│   │   │   ├── download/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── platforms.py      # 平台管理
│   │   │   │   ├── parse.py          # URL解析
│   │   │   │   ├── tasks.py          # 任务管理
│   │   │   │   ├── files.py          # 文件管理
│   │   │   │   ├── statistics.py     # 统计分析
│   │   │   │   └── websocket.py      # WebSocket
│   │   │   └── __init__.py
│   │   ├── api.py
│   │   └── __init__.py
│   └── __init__.py
├── core/
│   ├── download/
│   │   ├── __init__.py
│   │   ├── manager.py                # 下载管理器
│   │   ├── queue.py                  # 任务队列
│   │   ├── worker.py                 # 下载工作进程
│   │   ├── parser.py                 # URL解析器
│   │   └── platforms/
│   │       ├── __init__.py
│   │       ├── base.py               # 基础平台类
│   │       ├── douyin.py             # 抖音平台
│   │       ├── tiktok.py             # TikTok平台
│   │       └── bilibili.py           # B站平台
│   ├── config.py
│   ├── security.py
│   └── __init__.py
├── models/
│   ├── download.py                   # 下载相关模型
│   └── __init__.py
├── schemas/
│   ├── download.py                   # 下载相关Schema
│   └── __init__.py
├── services/
│   ├── download_service.py           # 下载服务
│   ├── file_service.py               # 文件服务
│   ├── statistics_service.py         # 统计服务
│   └── __init__.py
└── utils/
    ├── download_api_client.py        # Douyin_TikTok_Download_API客户端
    ├── file_utils.py                 # 文件工具
    └── __init__.py
```

### 3.2 核心服务类设计

#### 3.2.1 下载管理器
```python
# app/core/download/manager.py
from typing import List, Optional, Dict, Any
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession

class DownloadManager:
    """下载管理器 - 负责协调下载任务的整个生命周期"""
    
    def __init__(self, db: AsyncSession, config: Dict[str, Any]):
        self.db = db
        self.config = config
        self.queue = DownloadQueue()
        self.workers: List[DownloadWorker] = []
        self.max_concurrent = config.get('max_concurrent', 3)
    
    async def create_task(self, user_id: int, url: str, options: Dict[str, Any]) -> int:
        """创建下载任务"""
        # 1. 解析URL获取视频信息
        parsed_data = await self.parse_url(url, options.get('platform'))
        
        # 2. 创建数据库记录
        task = await self.create_db_task(user_id, url, parsed_data, options)
        
        # 3. 添加到队列
        await self.queue.add_task(task.id, options.get('priority', 5))
        
        # 4. 触发处理
        await self.process_queue()
        
        return task.id
    
    async def parse_url(self, url: str, platform: Optional[str] = None) -> Dict[str, Any]:
        """解析URL获取视频信息"""
        parser = URLParser()
        return await parser.parse(url, platform)
    
    async def process_queue(self):
        """处理队列中的任务"""
        if len(self.workers) >= self.max_concurrent:
            return
        
        # 获取下一个待处理任务
        next_task = await self.queue.get_next_task()
        if next_task:
            worker = DownloadWorker(self.db, self.config)
            self.workers.append(worker)
            asyncio.create_task(self.run_worker(worker, next_task))
    
    async def run_worker(self, worker: DownloadWorker, task_id: int):
        """运行下载工作进程"""
        try:
            await worker.process_task(task_id)
        finally:
            self.workers.remove(worker)
            # 继续处理队列
            await self.process_queue()
```

#### 3.2.2 URL解析器
```python
# app/core/download/parser.py
from typing import Dict, Any, Optional
import httpx
from app.utils.download_api_client import DownloadAPIClient

class URLParser:
    """URL解析器 - 负责解析各平台视频URL"""
    
    def __init__(self):
        self.api_client = DownloadAPIClient()
        self.platform_patterns = {
            'douyin': [r'douyin\.com', r'iesdouyin\.com'],
            'tiktok': [r'tiktok\.com', r'vm\.tiktok\.com'],
            'bilibili': [r'bilibili\.com', r'b23\.tv'],
        }
    
    async def parse(self, url: str, platform: Optional[str] = None) -> Dict[str, Any]:
        """解析URL获取视频信息"""
        if not platform:
            platform = self.detect_platform(url)
        
        if not platform:
            raise ValueError("不支持的平台或无法识别URL")
        
        # 调用Douyin_TikTok_Download_API
        try:
            result = await self.api_client.parse_video(url, platform)
            return self.normalize_result(result, platform)
        except Exception as e:
            raise ValueError(f"解析失败: {str(e)}")
    
    def detect_platform(self, url: str) -> Optional[str]:
        """自动检测平台"""
        import re
        for platform, patterns in self.platform_patterns.items():
            for pattern in patterns:
                if re.search(pattern, url, re.IGNORECASE):
                    return platform
        return None
    
    def normalize_result(self, result: Dict[str, Any], platform: str) -> Dict[str, Any]:
        """标准化解析结果"""
        return {
            'platform': platform,
            'video_id': result.get('video_id'),
            'title': result.get('title', ''),
            'description': result.get('description', ''),
            'author': {
                'name': result.get('author', ''),
                'id': result.get('author_id', ''),
                'avatar_url': result.get('author_avatar', '')
            },
            'thumbnail_url': result.get('thumbnail', ''),
            'duration': result.get('duration', 0),
            'view_count': result.get('view_count', 0),
            'like_count': result.get('like_count', 0),
            'comment_count': result.get('comment_count', 0),
            'share_count': result.get('share_count', 0),
            'available_qualities': result.get('qualities', []),
            'available_formats': result.get('formats', []),
            'subtitles_available': result.get('has_subtitles', False),
            'file_size_estimate': result.get('file_size', 0),
            'upload_date': result.get('upload_date')
        }
```

#### 3.2.3 下载工作进程
```python
# app/core/download/worker.py
import asyncio
import aiofiles
from pathlib import Path
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

class DownloadWorker:
    """下载工作进程 - 负责执行具体的下载任务"""
    
    def __init__(self, db: AsyncSession, config: Dict[str, Any]):
        self.db = db
        self.config = config
        self.api_client = DownloadAPIClient()
    
    async def process_task(self, task_id: int):
        """处理下载任务"""
        # 1. 获取任务信息
        task = await self.get_task(task_id)
        if not task:
            return
        
        try:
            # 2. 更新任务状态为分析中
            await self.update_task_status(task_id, 'analyzing')
            
            # 3. 获取下载链接
            download_info = await self.get_download_info(task)
            
            # 4. 更新任务状态为下载中
            await self.update_task_status(task_id, 'downloading')
            
            # 5. 执行下载
            file_path = await self.download_file(task, download_info)
            
            # 6. 创建视频记录
            video_id = await self.create_video_record(task, file_path)
            
            # 7. 更新任务状态为完成
            await self.update_task_status(task_id, 'completed', {
                'file_path': str(file_path),
                'video_id': video_id
            })
            
        except Exception as e:
            # 更新任务状态为失败
            await self.update_task_status(task_id, 'failed', {
                'error_message': str(e)
            })
            raise
    
    async def get_download_info(self, task) -> Dict[str, Any]:
        """获取下载信息"""
        return await self.api_client.get_download_info(
            task.url,
            task.platform,
            quality=task.quality,
            format_preference=task.format_preference
        )
    
    async def download_file(self, task, download_info: Dict[str, Any]) -> Path:
        """下载文件"""
        download_url = download_info['download_url']
        file_extension = download_info.get('format', 'mp4')
        
        # 生成文件路径
        file_path = self.generate_file_path(task, file_extension)
        
        # 确保目录存在
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 下载文件
        async with httpx.AsyncClient() as client:
            async with client.stream('GET', download_url) as response:
                response.raise_for_status()
                
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                
                async with aiofiles.open(file_path, 'wb') as f:
                    async for chunk in response.aiter_bytes(chunk_size=8192):
                        await f.write(chunk)
                        downloaded += len(chunk)
                        
                        # 更新进度
                        if total_size > 0:
                            progress = int((downloaded / total_size) * 100)
                            await self.update_task_progress(task.id, progress, downloaded)
        
        return file_path
    
    def generate_file_path(self, task, extension: str) -> Path:
        """生成文件路径"""
        base_dir = Path(self.config['storage_path'])
        user_dir = base_dir / f"user_{task.user_id}"
        
        # 生成文件名
        filename = f"task_{task.id}_{task.original_video_id}.{extension}"
        
        return user_dir / filename
```

### 3.3 API客户端设计

#### 3.3.1 Douyin_TikTok_Download_API客户端
```python
# app/utils/download_api_client.py
import httpx
from typing import Dict, Any, Optional
from app.core.config import settings

class DownloadAPIClient:
    """Douyin_TikTok_Download_API客户端"""
    
    def __init__(self):
        self.base_url = settings.DOWNLOAD_API_BASE_URL
        self.timeout = settings.DOWNLOAD_API_TIMEOUT
    
    async def parse_video(self, url: str, platform: str) -> Dict[str, Any]:
        """解析视频信息"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/video_data",
                json={"url": url, "platform": platform}
            )
            response.raise_for_status()
            return response.json()
    
    async def get_download_info(self, url: str, platform: str, 
                              quality: str = "best", 
                              format_preference: str = "mp4") -> Dict[str, Any]:
        """获取下载信息"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/download_info",
                json={
                    "url": url,
                    "platform": platform,
                    "quality": quality,
                    "format": format_preference
                }
            )
            response.raise_for_status()
            return response.json()
    
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except:
            return False
```

## 4. 错误处理和状态码

### 4.1 HTTP状态码规范

| 状态码 | 说明 | 使用场景 |
|--------|------|----------|
| 200 | 成功 | 正常请求成功 |
| 201 | 创建成功 | 创建下载任务成功 |
| 400 | 请求错误 | 参数错误、URL无效等 |
| 401 | 未授权 | 未登录或token无效 |
| 403 | 禁止访问 | 权限不足 |
| 404 | 资源不存在 | 任务不存在、文件不存在 |
| 409 | 冲突 | 重复创建任务 |
| 429 | 请求过多 | 超出速率限制 |
| 500 | 服务器错误 | 内部错误 |
| 502 | 网关错误 | 下载API服务不可用 |
| 503 | 服务不可用 | 系统维护中 |

### 4.2 错误代码规范

```typescript
enum ErrorCode {
  // 通用错误 (1000-1999)
  INVALID_REQUEST = 1000,
  UNAUTHORIZED = 1001,
  FORBIDDEN = 1002,
  NOT_FOUND = 1003,
  RATE_LIMITED = 1004,
  
  // URL解析错误 (2000-2099)
  INVALID_URL = 2000,
  UNSUPPORTED_PLATFORM = 2001,
  PARSE_FAILED = 2002,
  VIDEO_NOT_FOUND = 2003,
  VIDEO_PRIVATE = 2004,
  
  // 下载错误 (2100-2199)
  DOWNLOAD_FAILED = 2100,
  NETWORK_ERROR = 2101,
  FILE_TOO_LARGE = 2102,
  INSUFFICIENT_STORAGE = 2103,
  DOWNLOAD_TIMEOUT = 2104,
  
  // 任务错误 (2200-2299)
  TASK_NOT_FOUND = 2200,
  TASK_ALREADY_EXISTS = 2201,
  TASK_CANCELLED = 2202,
  MAX_TASKS_EXCEEDED = 2203,
  
  // 系统错误 (9000-9999)
  INTERNAL_ERROR = 9000,
  DATABASE_ERROR = 9001,
  EXTERNAL_API_ERROR = 9002,
  CONFIGURATION_ERROR = 9003
}
```

### 4.3 错误响应示例

```json
{
  "success": false,
  "error": "视频解析失败",
  "code": 2002,
  "message": "无法解析该视频URL，可能是私有视频或链接已失效",
  "details": {
    "url": "https://example.com/video/123",
    "platform": "douyin",
    "reason": "VIDEO_PRIVATE"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## 5. 安全性设计

### 5.1 认证和授权

#### 5.1.1 JWT Token认证
```python
# 所有API都需要有效的JWT token
@router.post("/tasks")
async def create_download_task(
    request: CreateTaskRequest,
    current_user: User = Depends(get_current_user)
):
    # 业务逻辑
    pass
```

#### 5.1.2 权限控制
```python
# 用户只能访问自己的下载任务
async def get_user_tasks(
    user_id: int,
    current_user: User = Depends(get_current_user)
):
    if current_user.id != user_id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="权限不足")
```

### 5.2 速率限制

#### 5.2.1 用户级别限制
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/tasks")
@limiter.limit("10/minute")  # 每分钟最多10个任务
async def create_download_task(request: Request, ...):
    pass
```

### 5.3 输入验证

#### 5.3.1 URL验证
```python
import validators
from urllib.parse import urlparse

def validate_url(url: str) -> bool:
    """验证URL格式和安全性"""
    if not validators.url(url):
        return False
    
    parsed = urlparse(url)
    
    # 只允许HTTP/HTTPS协议
    if parsed.scheme not in ['http', 'https']:
        return False
    
    # 禁止内网地址
    if parsed.hostname in ['localhost', '127.0.0.1'] or \
       parsed.hostname.startswith('192.168.') or \
       parsed.hostname.startswith('10.'):
        return False
    
    return True
```

## 6. 性能优化

### 6.1 缓存策略

#### 6.1.1 Redis缓存
```python
import redis.asyncio as redis

class CacheService:
    def __init__(self):
        self.redis = redis.from_url("redis://localhost:6379")
    
    async def cache_parsed_data(self, url: str, data: Dict[str, Any], ttl: int = 3600):
        """缓存解析结果"""
        key = f"parsed:{hash(url)}"
        await self.redis.setex(key, ttl, json.dumps(data))
    
    async def get_cached_parsed_data(self, url: str) -> Optional[Dict[str, Any]]:
        """获取缓存的解析结果"""
        key = f"parsed:{hash(url)}"
        data = await self.redis.get(key)
        return json.loads(data) if data else None
```

### 6.2 异步处理

#### 6.2.1 任务队列
```python
import asyncio
from asyncio import Queue

class DownloadQueue:
    def __init__(self, max_size: int = 1000):
        self.queue = Queue(maxsize=max_size)
        self.processing = set()
    
    async def add_task(self, task_id: int, priority: int = 5):
        """添加任务到队列"""
        await self.queue.put((priority, task_id))
    
    async def get_next_task(self) -> Optional[int]:
        """获取下一个任务"""
        try:
            priority, task_id = await asyncio.wait_for(self.queue.get(), timeout=1.0)
            self.processing.add(task_id)
            return task_id
        except asyncio.TimeoutError:
            return None
```

## 7. 监控和日志

### 7.1 日志记录

#### 7.1.1 结构化日志
```python
import structlog

logger = structlog.get_logger()

async def create_download_task(user_id: int, url: str, options: Dict[str, Any]):
    logger.info(
        "创建下载任务",
        user_id=user_id,
        url=url,
        platform=options.get('platform'),
        quality=options.get('quality')
    )
    
    try:
        task_id = await download_manager.create_task(user_id, url, options)
        logger.info("下载任务创建成功", task_id=task_id)
        return task_id
    except Exception as e:
        logger.error("下载任务创建失败", error=str(e), exc_info=True)
        raise
```

### 7.2 性能监控

#### 7.2.1 指标收集
```python
from prometheus_client import Counter, Histogram, Gauge

# 定义指标
download_tasks_total = Counter('download_tasks_total', 'Total download tasks', ['platform', 'status'])
download_duration = Histogram('download_duration_seconds', 'Download duration', ['platform'])
active_downloads = Gauge('active_downloads', 'Active downloads')

# 使用指标
download_tasks_total.labels(platform='douyin', status='completed').inc()
download_duration.labels(platform='douyin').observe(145.2)
active_downloads.set(5)
```

## 8. 部署和配置

### 8.1 环境配置

#### 8.1.1 配置文件
```python
# app/core/config.py
from pydantic import BaseSettings

class Settings(BaseSettings):
    # 数据库配置
    DATABASE_URL: str = "postgresql+asyncpg://user:pass@localhost/db"
    
    # 下载API配置
    DOWNLOAD_API_BASE_URL: str = "http://localhost:8080"
    DOWNLOAD_API_TIMEOUT: int = 300
    
    # 下载配置
    MAX_CONCURRENT_DOWNLOADS: int = 3
    DOWNLOAD_STORAGE_PATH: str = "./downloads"
    MAX_FILE_SIZE: int = 1024 * 1024 * 1024  # 1GB
    
    # Redis配置
    REDIS_URL: str = "redis://localhost:6379"
    
    # 安全配置
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    class Config:
        env_file = ".env"

settings = Settings()
```

### 8.2 Docker部署

#### 8.2.1 Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 8.2.2 docker-compose.yml
```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/aiexpert
      - REDIS_URL=redis://redis:6379
      - DOWNLOAD_API_BASE_URL=http://download-api:8080
    depends_on:
      - db
      - redis
      - download-api
    volumes:
      - ./downloads:/app/downloads

  download-api:
    build: ./.ref/Douyin_TikTok_Download_API
    ports:
      - "8080:8080"
    volumes:
      - ./downloads:/app/downloads

  db:
    image: postgres:15
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=aiexpert
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

## 9. 总结

本API设计方案提供了完整的视频下载功能支持，包括：

1. **完整的API接口**：涵盖平台管理、URL解析、任务管理、文件管理、统计分析等
2. **异步处理架构**：支持高并发下载任务处理
3. **模块化设计**：清晰的服务分层和组件划分
4. **安全性保障**：认证授权、输入验证、速率限制等
5. **性能优化**：缓存策略、异步处理、队列管理等
6. **监控和日志**：完善的日志记录和性能监控
7. **部署支持**：Docker容器化部署方案

通过这个设计，可以实现稳定、高效、安全的视频下载功能，同时保持与现有系统的良好集成。