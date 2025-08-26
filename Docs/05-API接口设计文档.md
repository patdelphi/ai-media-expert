# AI新媒体专家系统API接口设计文档

## 文档信息
- **文档版本**: v1.0
- **创建日期**: 2025-01-26
- **最后更新**: 2025-01-26
- **负责人**: API架构师
- **审核人**: 技术总监

## 1. 概述

### 1.1 API设计原则
- **RESTful设计**：遵循REST架构风格
- **统一响应格式**：标准化的响应结构
- **版本控制**：支持API版本管理
- **安全认证**：JWT令牌认证机制
- **错误处理**：统一的错误码和错误信息
- **文档完整**：详细的API文档和示例

### 1.2 技术规范
- **协议**: HTTPS
- **数据格式**: JSON
- **字符编码**: UTF-8
- **认证方式**: JWT Bearer Token
- **API版本**: URL路径版本控制 (/api/v1/)

### 1.3 基础URL
```
开发环境: https://dev-api.ai-media-expert.com/api/v1
测试环境: https://test-api.ai-media-expert.com/api/v1
生产环境: https://api.ai-media-expert.com/api/v1
```

## 2. 认证与授权

### 2.1 认证流程

#### 2.1.1 用户登录
```http
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}
```

**响应示例**:
```json
{
  "code": 200,
  "message": "登录成功",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "Bearer",
    "expires_in": 3600,
    "user": {
      "id": 1,
      "email": "user@example.com",
      "username": "testuser",
      "role": "user"
    }
  }
}
```

#### 2.1.2 令牌刷新
```http
POST /auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

#### 2.1.3 用户注册
```http
POST /auth/register
Content-Type: application/json

{
  "email": "newuser@example.com",
  "password": "password123",
  "username": "newuser",
  "full_name": "New User"
}
```

#### 2.1.4 用户登出
```http
POST /auth/logout
Authorization: Bearer {access_token}
```

### 2.2 权限验证

所有需要认证的接口都需要在请求头中包含JWT令牌：
```http
Authorization: Bearer {access_token}
```

## 3. 统一响应格式

### 3.1 成功响应
```json
{
  "code": 200,
  "message": "操作成功",
  "data": {
    // 具体数据内容
  },
  "timestamp": "2025-01-26T10:30:00Z",
  "request_id": "req_123456789"
}
```

### 3.2 错误响应
```json
{
  "code": 400,
  "message": "请求参数错误",
  "error": {
    "type": "ValidationError",
    "details": [
      {
        "field": "email",
        "message": "邮箱格式不正确"
      }
    ]
  },
  "timestamp": "2025-01-26T10:30:00Z",
  "request_id": "req_123456789"
}
```

### 3.3 分页响应
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "items": [
      // 数据列表
    ],
    "pagination": {
      "page": 1,
      "size": 20,
      "total": 100,
      "pages": 5,
      "has_next": true,
      "has_prev": false
    }
  }
}
```

## 4. 用户管理API

### 4.1 用户信息

#### 4.1.1 获取当前用户信息
```http
GET /users/me
Authorization: Bearer {access_token}
```

**响应示例**:
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "id": 1,
    "uuid": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "username": "testuser",
    "full_name": "Test User",
    "avatar_url": "https://example.com/avatar.jpg",
    "role": "user",
    "status": "active",
    "created_at": "2025-01-01T00:00:00Z",
    "last_login_at": "2025-01-26T10:00:00Z",
    "preferences": {
      "language": "zh-CN",
      "theme": "light"
    }
  }
}
```

#### 4.1.2 更新用户信息
```http
PUT /users/me
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "username": "newusername",
  "full_name": "New Full Name",
  "preferences": {
    "language": "en-US",
    "theme": "dark"
  }
}
```

#### 4.1.3 修改密码
```http
PUT /users/me/password
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "current_password": "oldpassword",
  "new_password": "newpassword123"
}
```

#### 4.1.4 上传头像
```http
POST /users/me/avatar
Authorization: Bearer {access_token}
Content-Type: multipart/form-data

file: [binary data]
```

### 4.2 用户管理（管理员）

#### 4.2.1 获取用户列表
```http
GET /users?page=1&size=20&role=user&status=active&search=keyword
Authorization: Bearer {access_token}
```

**查询参数**:
- `page`: 页码（默认1）
- `size`: 每页数量（默认20，最大100）
- `role`: 用户角色筛选
- `status`: 用户状态筛选
- `search`: 搜索关键词（用户名、邮箱）

#### 4.2.2 获取用户详情
```http
GET /users/{user_id}
Authorization: Bearer {access_token}
```

#### 4.2.3 更新用户状态
```http
PUT /users/{user_id}/status
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "status": "suspended",
  "reason": "违规操作"
}
```

## 5. 视频管理API

### 5.1 视频信息

#### 5.1.1 获取视频列表
```http
GET /videos?page=1&size=20&platform=tiktok&author=username&date_from=2025-01-01&date_to=2025-01-31&tags=tag1,tag2
Authorization: Bearer {access_token}
```

**查询参数**:
- `page`: 页码
- `size`: 每页数量
- `platform`: 平台筛选
- `author`: 作者筛选
- `date_from`: 开始日期
- `date_to`: 结束日期
- `tags`: 标签筛选（逗号分隔）
- `search`: 搜索关键词
- `sort`: 排序字段（created_at, view_count, duration）
- `order`: 排序方向（asc, desc）

**响应示例**:
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "items": [
      {
        "id": 1,
        "uuid": "550e8400-e29b-41d4-a716-446655440001",
        "title": "示例视频标题",
        "description": "视频描述",
        "thumbnail_url": "https://example.com/thumb.jpg",
        "duration": 120,
        "resolution": "1920x1080",
        "file_size": 52428800,
        "platform": "tiktok",
        "author": "testauthor",
        "view_count": 1000,
        "like_count": 50,
        "tags": ["教育", "科技"],
        "created_at": "2025-01-26T10:00:00Z",
        "status": "active"
      }
    ],
    "pagination": {
      "page": 1,
      "size": 20,
      "total": 100,
      "pages": 5
    }
  }
}
```

#### 5.1.2 获取视频详情
```http
GET /videos/{video_id}
Authorization: Bearer {access_token}
```

**响应示例**:
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "id": 1,
    "uuid": "550e8400-e29b-41d4-a716-446655440001",
    "title": "示例视频标题",
    "description": "详细的视频描述内容",
    "file_path": "/videos/2025/01/video_001.mp4",
    "file_size": 52428800,
    "duration": 120,
    "width": 1920,
    "height": 1080,
    "fps": 30.0,
    "bitrate": 2000000,
    "format": "mp4",
    "codec_video": "h264",
    "codec_audio": "aac",
    "thumbnail_url": "https://example.com/thumb.jpg",
    "preview_url": "https://example.com/preview.gif",
    "platform": "tiktok",
    "platform_id": "7123456789",
    "original_url": "https://tiktok.com/@user/video/7123456789",
    "author": "testauthor",
    "author_id": "author123",
    "upload_date": "2025-01-25",
    "view_count": 1000,
    "like_count": 50,
    "comment_count": 10,
    "share_count": 5,
    "language": "zh-CN",
    "category": "教育",
    "tags": ["教育", "科技", "AI"],
    "metadata": {
      "hashtags": ["#AI", "#教育"],
      "mentions": ["@user1"],
      "location": "北京"
    },
    "created_at": "2025-01-26T10:00:00Z",
    "updated_at": "2025-01-26T10:00:00Z",
    "status": "active"
  }
}
```

#### 5.1.3 更新视频信息
```http
PUT /videos/{video_id}
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "title": "新的视频标题",
  "description": "更新的描述",
  "tags": ["新标签1", "新标签2"],
  "category": "娱乐"
}
```

#### 5.1.4 删除视频
```http
DELETE /videos/{video_id}
Authorization: Bearer {access_token}
```

#### 5.1.5 获取视频播放URL
```http
GET /videos/{video_id}/play-url
Authorization: Bearer {access_token}
```

**响应示例**:
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "play_url": "https://example.com/videos/signed-url?token=xxx",
    "expires_at": "2025-01-26T11:00:00Z",
    "duration": 3600
  }
}
```

### 5.2 视频上传

#### 5.2.1 手动上传视频
```http
POST /videos/upload
Authorization: Bearer {access_token}
Content-Type: multipart/form-data

file: [binary data]
title: "视频标题"
description: "视频描述"
tags: "标签1,标签2"
category: "教育"
```

**响应示例**:
```json
{
  "code": 200,
  "message": "上传成功",
  "data": {
    "video_id": 123,
    "uuid": "550e8400-e29b-41d4-a716-446655440123",
    "upload_status": "processing",
    "file_size": 52428800,
    "estimated_processing_time": 300
  }
}
```

#### 5.2.2 获取上传进度
```http
GET /videos/upload/{upload_id}/progress
Authorization: Bearer {access_token}
```

## 6. 下载任务API

### 6.1 任务管理

#### 6.1.1 创建下载任务
```http
POST /download/tasks
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "url": "https://tiktok.com/@user/video/7123456789",
  "options": {
    "quality": "best",
    "format": "mp4",
    "download_subtitles": true,
    "download_comments": false
  },
  "priority": 5
}
```

**响应示例**:
```json
{
  "code": 200,
  "message": "任务创建成功",
  "data": {
    "task_id": 456,
    "uuid": "550e8400-e29b-41d4-a716-446655440456",
    "status": "pending",
    "estimated_start_time": "2025-01-26T10:35:00Z",
    "queue_position": 3
  }
}
```

#### 6.1.2 获取任务状态
```http
GET /download/tasks/{task_id}
Authorization: Bearer {access_token}
```

**响应示例**:
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "id": 456,
    "uuid": "550e8400-e29b-41d4-a716-446655440456",
    "url": "https://tiktok.com/@user/video/7123456789",
    "platform": "tiktok",
    "status": "processing",
    "progress": 65,
    "priority": 5,
    "file_size": 52428800,
    "downloaded_size": 34078720,
    "download_speed": 1048576,
    "eta": 18,
    "started_at": "2025-01-26T10:30:00Z",
    "created_at": "2025-01-26T10:25:00Z",
    "video_info": {
      "title": "视频标题",
      "author": "作者名",
      "duration": 120
    }
  }
}
```

#### 6.1.3 获取任务列表
```http
GET /download/tasks?page=1&size=20&status=processing&platform=tiktok
Authorization: Bearer {access_token}
```

**查询参数**:
- `page`: 页码
- `size`: 每页数量
- `status`: 任务状态筛选
- `platform`: 平台筛选
- `date_from`: 开始日期
- `date_to`: 结束日期

#### 6.1.4 暂停任务
```http
PUT /download/tasks/{task_id}/pause
Authorization: Bearer {access_token}
```

#### 6.1.5 恢复任务
```http
PUT /download/tasks/{task_id}/resume
Authorization: Bearer {access_token}
```

#### 6.1.6 取消任务
```http
DELETE /download/tasks/{task_id}
Authorization: Bearer {access_token}
```

#### 6.1.7 重试任务
```http
PUT /download/tasks/{task_id}/retry
Authorization: Bearer {access_token}
```

### 6.2 批量操作

#### 6.2.1 批量创建任务
```http
POST /download/tasks/batch
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "urls": [
    "https://tiktok.com/@user/video/1",
    "https://tiktok.com/@user/video/2",
    "https://tiktok.com/@user/video/3"
  ],
  "options": {
    "quality": "best",
    "format": "mp4"
  },
  "priority": 5
}
```

#### 6.2.2 批量操作任务
```http
PUT /download/tasks/batch
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "task_ids": [456, 457, 458],
  "action": "pause"
}
```

## 7. 视频分析API

### 7.1 分析任务

#### 7.1.1 创建分析任务
```http
POST /analysis/tasks
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "video_id": 123,
  "template_id": 1,
  "name": "营销分析任务",
  "config": {
    "analyzers": ["brand_detection", "emotion_analysis"],
    "confidence_threshold": 0.7,
    "output_format": "detailed_report"
  },
  "priority": 5
}
```

**响应示例**:
```json
{
  "code": 200,
  "message": "分析任务创建成功",
  "data": {
    "task_id": 789,
    "uuid": "550e8400-e29b-41d4-a716-446655440789",
    "status": "pending",
    "estimated_processing_time": 600,
    "queue_position": 2
  }
}
```

#### 7.1.2 获取分析任务状态
```http
GET /analysis/tasks/{task_id}
Authorization: Bearer {access_token}
```

**响应示例**:
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "id": 789,
    "uuid": "550e8400-e29b-41d4-a716-446655440789",
    "video_id": 123,
    "template_id": 1,
    "name": "营销分析任务",
    "status": "processing",
    "progress": 45,
    "current_stage": "emotion_analysis",
    "started_at": "2025-01-26T10:30:00Z",
    "estimated_completion": "2025-01-26T10:40:00Z",
    "processing_time": 300,
    "resource_usage": {
      "cpu_percent": 75,
      "memory_mb": 2048,
      "gpu_percent": 60
    }
  }
}
```

#### 7.1.3 获取分析结果
```http
GET /analysis/tasks/{task_id}/results
Authorization: Bearer {access_token}
```

**响应示例**:
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "task_id": 789,
    "video_id": 123,
    "status": "completed",
    "completed_at": "2025-01-26T10:40:00Z",
    "processing_time": 600,
    "summary": {
      "overall_score": 8.5,
      "emotion_distribution": {
        "positive": 0.7,
        "neutral": 0.2,
        "negative": 0.1
      },
      "detected_brands": ["Brand A", "Brand B"],
      "key_moments": [
        {
          "timestamp": 15.5,
          "description": "品牌logo出现",
          "confidence": 0.95
        }
      ]
    },
    "detailed_results": [
      {
        "analyzer_type": "brand_detection",
        "timestamp_start": 15.0,
        "timestamp_end": 16.0,
        "confidence": 0.95,
        "data": {
          "brand_name": "Brand A",
          "logo_position": {"x": 100, "y": 50, "width": 80, "height": 40}
        }
      }
    ],
    "report_url": "https://example.com/reports/789.pdf"
  }
}
```

#### 7.1.4 导出分析结果
```http
POST /analysis/tasks/{task_id}/export
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "format": "pdf",
  "options": {
    "include_charts": true,
    "include_raw_data": false,
    "language": "zh-CN"
  }
}
```

**响应示例**:
```json
{
  "code": 200,
  "message": "导出成功",
  "data": {
    "export_id": "exp_123456",
    "download_url": "https://example.com/exports/789_report.pdf",
    "expires_at": "2025-01-27T10:40:00Z",
    "file_size": 2048576
  }
}
```

### 7.2 分析模板

#### 7.2.1 获取模板列表
```http
GET /analysis/templates?category=marketing&is_public=true
Authorization: Bearer {access_token}
```

**响应示例**:
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "items": [
      {
        "id": 1,
        "uuid": "550e8400-e29b-41d4-a716-446655440001",
        "name": "营销分析模板",
        "description": "分析视频中的营销元素和品牌露出",
        "category": "marketing",
        "is_public": true,
        "usage_count": 150,
        "created_by": {
          "id": 1,
          "username": "admin"
        },
        "created_at": "2025-01-01T00:00:00Z"
      }
    ]
  }
}
```

#### 7.2.2 获取模板详情
```http
GET /analysis/templates/{template_id}
Authorization: Bearer {access_token}
```

#### 7.2.3 创建自定义模板
```http
POST /analysis/templates
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "name": "自定义分析模板",
  "description": "针对特定需求的分析模板",
  "category": "custom",
  "config": {
    "analyzers": ["scene_analysis", "object_detection"],
    "output_format": "json",
    "confidence_threshold": 0.8
  },
  "is_public": false
}
```

#### 7.2.4 更新模板
```http
PUT /analysis/templates/{template_id}
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "name": "更新的模板名称",
  "description": "更新的描述",
  "config": {
    "analyzers": ["scene_analysis", "emotion_analysis"],
    "confidence_threshold": 0.75
  }
}
```

#### 7.2.5 删除模板
```http
DELETE /analysis/templates/{template_id}
Authorization: Bearer {access_token}
```

### 7.3 批量分析

#### 7.3.1 批量创建分析任务
```http
POST /analysis/tasks/batch
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "video_ids": [123, 124, 125],
  "template_id": 1,
  "config": {
    "confidence_threshold": 0.7
  },
  "priority": 5
}
```

#### 7.3.2 获取批量任务状态
```http
GET /analysis/tasks/batch/{batch_id}
Authorization: Bearer {access_token}
```

## 8. 标签管理API

### 8.1 标签操作

#### 8.1.1 获取标签列表
```http
GET /tags?category=content_type&parent_id=1&search=教育
Authorization: Bearer {access_token}
```

**响应示例**:
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "items": [
      {
        "id": 1,
        "name": "教育",
        "slug": "education",
        "category": "content_type",
        "description": "教育相关内容",
        "color": "#007bff",
        "icon": "education",
        "parent_id": null,
        "level": 0,
        "usage_count": 150,
        "is_system": true,
        "children": [
          {
            "id": 11,
            "name": "在线教育",
            "slug": "online-education",
            "parent_id": 1,
            "level": 1,
            "usage_count": 80
          }
        ]
      }
    ]
  }
}
```

#### 8.1.2 创建标签
```http
POST /tags
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "name": "新标签",
  "slug": "new-tag",
  "category": "custom",
  "description": "自定义标签",
  "color": "#28a745",
  "parent_id": 1
}
```

#### 8.1.3 更新标签
```http
PUT /tags/{tag_id}
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "name": "更新的标签名",
  "description": "更新的描述",
  "color": "#dc3545"
}
```

#### 8.1.4 删除标签
```http
DELETE /tags/{tag_id}
Authorization: Bearer {access_token}
```

### 8.2 视频标签关联

#### 8.2.1 为视频添加标签
```http
POST /videos/{video_id}/tags
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "tag_ids": [1, 2, 3],
  "source": "manual"
}
```

#### 8.2.2 移除视频标签
```http
DELETE /videos/{video_id}/tags
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "tag_ids": [2, 3]
}
```

#### 8.2.3 获取视频标签
```http
GET /videos/{video_id}/tags
Authorization: Bearer {access_token}
```

#### 8.2.4 批量标签操作
```http
PUT /videos/tags/batch
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "video_ids": [123, 124, 125],
  "action": "add",
  "tag_ids": [1, 2]
}
```

### 8.3 标签统计

#### 8.3.1 获取热门标签
```http
GET /tags/popular?limit=20&category=content_type
Authorization: Bearer {access_token}
```

#### 8.3.2 获取标签使用统计
```http
GET /tags/{tag_id}/stats?date_from=2025-01-01&date_to=2025-01-31
Authorization: Bearer {access_token}
```

## 9. 搜索API

### 9.1 视频搜索

#### 9.1.1 全文搜索
```http
GET /search/videos?q=关键词&page=1&size=20&platform=tiktok&date_from=2025-01-01
Authorization: Bearer {access_token}
```

**查询参数**:
- `q`: 搜索关键词
- `page`: 页码
- `size`: 每页数量
- `platform`: 平台筛选
- `author`: 作者筛选
- `tags`: 标签筛选
- `date_from`: 开始日期
- `date_to`: 结束日期
- `duration_min`: 最小时长（秒）
- `duration_max`: 最大时长（秒）
- `sort`: 排序字段
- `order`: 排序方向

**响应示例**:
```json
{
  "code": 200,
  "message": "搜索成功",
  "data": {
    "query": "关键词",
    "total_hits": 150,
    "search_time": 0.05,
    "items": [
      {
        "id": 123,
        "title": "包含关键词的视频标题",
        "description": "视频描述...",
        "author": "作者名",
        "platform": "tiktok",
        "duration": 120,
        "view_count": 1000,
        "created_at": "2025-01-26T10:00:00Z",
        "highlights": {
          "title": ["包含<em>关键词</em>的视频标题"],
          "description": ["描述中的<em>关键词</em>..."]
        },
        "score": 8.5
      }
    ],
    "aggregations": {
      "platforms": {
        "tiktok": 80,
        "youtube": 50,
        "bilibili": 20
      },
      "tags": {
        "教育": 60,
        "科技": 40,
        "娱乐": 30
      }
    },
    "pagination": {
      "page": 1,
      "size": 20,
      "total": 150,
      "pages": 8
    }
  }
}
```

#### 9.1.2 搜索建议
```http
GET /search/suggestions?q=关键&type=video&limit=10
Authorization: Bearer {access_token}
```

**响应示例**:
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "suggestions": [
      "关键词1",
      "关键词2",
      "关键词3"
    ]
  }
}
```

### 9.2 高级搜索

#### 9.2.1 复合条件搜索
```http
POST /search/videos/advanced
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "query": {
    "must": [
      {"match": {"title": "教育"}},
      {"range": {"duration": {"gte": 60, "lte": 300}}}
    ],
    "filter": [
      {"term": {"platform": "tiktok"}},
      {"terms": {"tags": ["教育", "科技"]}}
    ]
  },
  "sort": [{"view_count": {"order": "desc"}}],
  "page": 1,
  "size": 20
}
```

#### 9.2.2 相似视频搜索
```http
GET /search/videos/{video_id}/similar?limit=10
Authorization: Bearer {access_token}
```

## 10. 统计分析API

### 10.1 概览统计

#### 10.1.1 获取仪表板数据
```http
GET /stats/dashboard?date_from=2025-01-01&date_to=2025-01-31
Authorization: Bearer {access_token}
```

**响应示例**:
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "overview": {
      "total_videos": 1500,
      "total_downloads": 2000,
      "total_analysis": 800,
      "active_users": 150
    },
    "trends": {
      "daily_downloads": [
        {"date": "2025-01-01", "count": 50},
        {"date": "2025-01-02", "count": 65}
      ],
      "daily_analysis": [
        {"date": "2025-01-01", "count": 20},
        {"date": "2025-01-02", "count": 25}
      ]
    },
    "platform_distribution": {
      "tiktok": 800,
      "youtube": 400,
      "bilibili": 300
    },
    "top_tags": [
      {"name": "教育", "count": 200},
      {"name": "科技", "count": 150}
    ]
  }
}
```

### 10.2 详细统计

#### 10.2.1 用户活动统计
```http
GET /stats/users/activity?period=7d&user_id=123
Authorization: Bearer {access_token}
```

#### 10.2.2 平台统计
```http
GET /stats/platforms?date_from=2025-01-01&date_to=2025-01-31
Authorization: Bearer {access_token}
```

#### 10.2.3 性能统计
```http
GET /stats/performance?metric=response_time&period=24h
Authorization: Bearer {access_token}
```

## 11. 系统管理API

### 11.1 系统配置

#### 11.1.1 获取配置列表
```http
GET /system/configs?category=download&is_public=true
Authorization: Bearer {access_token}
```

#### 11.1.2 更新配置
```http
PUT /system/configs/{key}
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "value": "10",
  "description": "更新的描述"
}
```

### 11.2 系统监控

#### 11.2.1 健康检查
```http
GET /system/health
```

**响应示例**:
```json
{
  "code": 200,
  "message": "系统正常",
  "data": {
    "status": "healthy",
    "timestamp": "2025-01-26T10:30:00Z",
    "services": {
      "database": "healthy",
      "redis": "healthy",
      "elasticsearch": "healthy",
      "storage": "healthy"
    },
    "metrics": {
      "cpu_usage": 45.2,
      "memory_usage": 68.5,
      "disk_usage": 35.8,
      "active_connections": 25
    }
  }
}
```

#### 11.2.2 系统信息
```http
GET /system/info
Authorization: Bearer {access_token}
```

## 12. WebSocket实时通信

### 12.1 连接建立

#### 12.1.1 WebSocket连接
```javascript
// 建立WebSocket连接
const ws = new WebSocket('wss://api.ai-media-expert.com/ws?token=your_jwt_token');

// 连接成功
ws.onopen = function(event) {
    console.log('WebSocket连接已建立');
    
    // 订阅特定频道
    ws.send(JSON.stringify({
        type: 'subscribe',
        channels: ['download_progress', 'analysis_progress']
    }));
};

// 接收消息
ws.onmessage = function(event) {
    const message = JSON.parse(event.data);
    console.log('收到消息:', message);
};
```

### 12.2 消息格式

#### 12.2.1 下载进度推送
```json
{
  "type": "download_progress",
  "data": {
    "task_id": 456,
    "status": "processing",
    "progress": 65,
    "download_speed": 1048576,
    "eta": 18,
    "timestamp": "2025-01-26T10:30:00Z"
  }
}
```

#### 12.2.2 分析进度推送
```json
{
  "type": "analysis_progress",
  "data": {
    "task_id": 789,
    "status": "processing",
    "progress": 45,
    "current_stage": "emotion_analysis",
    "eta": 300,
    "timestamp": "2025-01-26T10:30:00Z"
  }
}
```

#### 12.2.3 系统通知
```json
{
  "type": "notification",
  "data": {
    "id": "notif_123",
    "title": "任务完成",
    "message": "视频分析任务已完成",
    "level": "info",
    "timestamp": "2025-01-26T10:30:00Z",
    "action_url": "/analysis/tasks/789"
  }
}
```

## 13. 错误码定义

### 13.1 HTTP状态码
- `200`: 成功
- `201`: 创建成功
- `400`: 请求参数错误
- `401`: 未授权
- `403`: 权限不足
- `404`: 资源不存在
- `409`: 资源冲突
- `422`: 数据验证失败
- `429`: 请求频率限制
- `500`: 服务器内部错误
- `503`: 服务不可用

### 13.2 业务错误码

#### 13.2.1 用户相关 (1000-1999)
- `1001`: 用户不存在
- `1002`: 密码错误
- `1003`: 账号已被禁用
- `1004`: 邮箱已存在
- `1005`: 用户名已存在
- `1006`: 令牌已过期
- `1007`: 令牌无效

#### 13.2.2 视频相关 (2000-2999)
- `2001`: 视频不存在
- `2002`: 视频格式不支持
- `2003`: 视频文件损坏
- `2004`: 视频大小超限
- `2005`: 视频时长超限

#### 13.2.3 下载相关 (3000-3999)
- `3001`: URL格式错误
- `3002`: 平台不支持
- `3003`: 视频不可访问
- `3004`: 下载失败
- `3005`: 任务不存在
- `3006`: 任务状态错误

#### 13.2.4 分析相关 (4000-4999)
- `4001`: 分析模板不存在
- `4002`: 分析配置错误
- `4003`: 分析失败
- `4004`: 模型加载失败
- `4005`: 资源不足

#### 13.2.5 系统相关 (5000-5999)
- `5001`: 系统维护中
- `5002`: 服务不可用
- `5003`: 数据库连接失败
- `5004`: 存储空间不足
- `5005`: 配置错误

## 14. API限流策略

### 14.1 限流规则

#### 14.1.1 用户级别限流
- **普通用户**: 100次/分钟, 1000次/小时
- **VIP用户**: 200次/分钟, 2000次/小时
- **管理员**: 500次/分钟, 5000次/小时

#### 14.1.2 接口级别限流
- **登录接口**: 5次/分钟
- **上传接口**: 10次/分钟
- **下载接口**: 20次/分钟
- **分析接口**: 30次/分钟
- **查询接口**: 100次/分钟

### 14.2 限流响应

当触发限流时，API返回429状态码：
```json
{
  "code": 429,
  "message": "请求频率超限",
  "error": {
    "type": "RateLimitExceeded",
    "limit": 100,
    "remaining": 0,
    "reset_time": "2025-01-26T10:31:00Z"
  }
}
```

响应头包含限流信息：
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1706265060
Retry-After: 60
```

## 15. API版本管理

### 15.1 版本策略
- **URL版本控制**: `/api/v1/`, `/api/v2/`
- **向后兼容**: 旧版本保持6个月支持
- **废弃通知**: 提前3个月通知版本废弃
- **迁移指南**: 提供详细的版本迁移文档

### 15.2 版本信息
```http
GET /api/version
```

**响应示例**:
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "current_version": "v1",
    "supported_versions": ["v1"],
    "deprecated_versions": [],
    "latest_changes": {
      "v1.0.0": {
        "release_date": "2025-01-26",
        "changes": [
          "初始版本发布",
          "支持视频下载和分析功能"
        ]
      }
    }
  }
}
```

## 16. 总结

### 16.1 API特点
- **完整性**: 覆盖所有核心业务功能
- **一致性**: 统一的接口设计和响应格式
- **安全性**: 完善的认证授权机制
- **可扩展性**: 支持版本管理和功能扩展
- **易用性**: 清晰的文档和示例

### 16.2 最佳实践
- **RESTful设计**: 遵循REST架构原则
- **错误处理**: 统一的错误码和错误信息
- **性能优化**: 合理的分页和缓存策略
- **安全防护**: 完善的限流和验证机制
- **监控日志**: 详细的API调用日志

### 16.3 开发建议
- **接口测试**: 使用Postman或类似工具测试
- **文档维护**: 及时更新API文档
- **版本管理**: 谨慎处理接口变更
- **性能监控**: 监控API响应时间和错误率
- **用户反馈**: 收集和处理用户反馈

---

**文档状态**: 待审核  
**下次更新**: 根据开发进度和接口变更