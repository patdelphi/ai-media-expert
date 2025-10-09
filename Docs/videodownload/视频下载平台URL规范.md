# 视频下载平台URL规范

## 1. 概述

本文档定义了视频下载功能支持的各个平台的URL格式规范，用于URL识别、解析和验证。

## 2. 支持的平台和URL格式

### 2.1 抖音 (Douyin)

#### 2.1.1 URL格式
- **完整链接**: `https://www.douyin.com/video/[video_id]`
- **短链接**: `https://v.douyin.com/[short_id]`
- **分享链接**: `https://www.iesdouyin.com/share/video/[video_id]`

#### 2.1.2 识别规则
```javascript
const douyinPatterns = [
    /^https?:\/\/(?:www\.)?douyin\.com\/video\/(\d+)/,
    /^https?:\/\/v\.douyin\.com\/([A-Za-z0-9]+)/,
    /^https?:\/\/(?:www\.)?iesdouyin\.com\/share\/video\/(\d+)/
];
```

#### 2.1.3 示例URL
```
https://www.douyin.com/video/7234567890123456789
https://v.douyin.com/ieFyPqR/
https://www.iesdouyin.com/share/video/7234567890123456789
```

### 2.2 TikTok

#### 2.2.1 URL格式
- **完整链接**: `https://www.tiktok.com/@[username]/video/[video_id]`
- **短链接**: `https://vm.tiktok.com/[short_id]`
- **移动端**: `https://m.tiktok.com/v/[video_id]`

#### 2.2.2 识别规则
```javascript
const tiktokPatterns = [
    /^https?:\/\/(?:www\.)?tiktok\.com\/@([^\/]+)\/video\/(\d+)/,
    /^https?:\/\/vm\.tiktok\.com\/([A-Za-z0-9]+)/,
    /^https?:\/\/m\.tiktok\.com\/v\/(\d+)/
];
```

#### 2.2.3 示例URL
```
https://www.tiktok.com/@username/video/7234567890123456789
https://vm.tiktok.com/ZMeFyPqR/
https://m.tiktok.com/v/7234567890123456789
```

### 2.3 哔哩哔哩 (Bilibili)

#### 2.3.1 URL格式
- **BV号**: `https://www.bilibili.com/video/BV[bv_id]`
- **AV号**: `https://www.bilibili.com/video/av[av_id]`
- **短链接**: `https://b23.tv/[short_id]`
- **移动端**: `https://m.bilibili.com/video/BV[bv_id]`

#### 2.3.2 识别规则
```javascript
const bilibiliPatterns = [
    /^https?:\/\/(?:www\.)?bilibili\.com\/video\/(BV[A-Za-z0-9]+)/,
    /^https?:\/\/(?:www\.)?bilibili\.com\/video\/av(\d+)/,
    /^https?:\/\/b23\.tv\/([A-Za-z0-9]+)/,
    /^https?:\/\/m\.bilibili\.com\/video\/(BV[A-Za-z0-9]+)/
];
```

#### 2.3.3 示例URL
```
https://www.bilibili.com/video/BV1xx411c7mD
https://www.bilibili.com/video/av123456789
https://b23.tv/BV1xx411c7mD
https://m.bilibili.com/video/BV1xx411c7mD
```

### 2.4 小红书 (Xiaohongshu)

#### 2.4.1 URL格式
- **笔记链接**: `https://www.xiaohongshu.com/explore/[note_id]`
- **短链接**: `https://xhslink.com/[short_id]`
- **用户分享**: `http://xhslink.com/[short_id]`

#### 2.4.2 识别规则
```javascript
const xiaohongshuPatterns = [
    /^https?:\/\/(?:www\.)?xiaohongshu\.com\/explore\/([A-Za-z0-9]+)/,
    /^https?:\/\/xhslink\.com\/([A-Za-z0-9]+)/
];
```

#### 2.4.3 示例URL
```
https://www.xiaohongshu.com/explore/64a1b2c3d4e5f6789012
https://xhslink.com/AbCdEf
http://xhslink.com/AbCdEf
```

### 2.5 快手 (Kuaishou)

#### 2.5.1 URL格式
- **完整链接**: `https://www.kuaishou.com/short-video/[video_id]`
- **短链接**: `https://v.kuaishou.com/[short_id]`
- **用户作品**: `https://www.kuaishou.com/profile/[user_id]/video/[video_id]`

#### 2.5.2 识别规则
```javascript
const kuaishouPatterns = [
    /^https?:\/\/(?:www\.)?kuaishou\.com\/short-video\/([A-Za-z0-9]+)/,
    /^https?:\/\/v\.kuaishou\.com\/([A-Za-z0-9]+)/,
    /^https?:\/\/(?:www\.)?kuaishou\.com\/profile\/([^\/]+)\/video\/([A-Za-z0-9]+)/
];
```

#### 2.5.3 示例URL
```
https://www.kuaishou.com/short-video/3xbCqARqrqE
https://v.kuaishou.com/3xbCqARqrqE
https://www.kuaishou.com/profile/username/video/3xbCqARqrqE
```

### 2.6 微信视频号 (Weixin)

#### 2.6.1 URL格式
- **视频号链接**: `https://channels.weixin.qq.com/video/[video_id]`
- **分享链接**: `https://mp.weixin.qq.com/mp/video?[params]`

#### 2.6.2 识别规则
```javascript
const weixinPatterns = [
    /^https?:\/\/channels\.weixin\.qq\.com\/video\/([A-Za-z0-9_-]+)/,
    /^https?:\/\/mp\.weixin\.qq\.com\/mp\/video\?.*vid=([A-Za-z0-9_-]+)/
];
```

#### 2.6.3 示例URL
```
https://channels.weixin.qq.com/video/wxv_123456789
https://mp.weixin.qq.com/mp/video?vid=wxv_123456789&sn=abc123
```

## 3. URL识别和验证

### 3.1 平台识别函数
```python
def identify_platform(url: str) -> str:
    """根据URL识别视频平台"""
    url = url.strip().lower()
    
    # 抖音
    if any(domain in url for domain in ['douyin.com', 'iesdouyin.com']):
        return 'douyin'
    
    # TikTok
    if 'tiktok.com' in url:
        return 'tiktok'
    
    # B站
    if any(domain in url for domain in ['bilibili.com', 'b23.tv']):
        return 'bilibili'
    
    # 小红书
    if any(domain in url for domain in ['xiaohongshu.com', 'xhslink.com']):
        return 'xiaohongshu'
    
    # 快手
    if 'kuaishou.com' in url:
        return 'kuaishou'
    
    # 微信视频号
    if any(domain in url for domain in ['channels.weixin.qq.com', 'mp.weixin.qq.com']):
        return 'weixin'
    
    return 'unknown'
```

### 3.2 URL验证函数
```python
import re
from typing import Optional, Dict

def validate_video_url(url: str) -> Dict[str, any]:
    """验证视频URL格式并提取信息"""
    result = {
        'valid': False,
        'platform': None,
        'video_id': None,
        'normalized_url': None,
        'error': None
    }
    
    try:
        platform = identify_platform(url)
        if platform == 'unknown':
            result['error'] = '不支持的视频平台'
            return result
        
        # 根据平台验证URL格式
        patterns = get_platform_patterns(platform)
        for pattern in patterns:
            match = re.match(pattern, url)
            if match:
                result['valid'] = True
                result['platform'] = platform
                result['video_id'] = match.group(1)
                result['normalized_url'] = normalize_url(url, platform)
                break
        
        if not result['valid']:
            result['error'] = f'{platform}平台URL格式不正确'
        
    except Exception as e:
        result['error'] = f'URL验证失败: {str(e)}'
    
    return result
```

### 3.3 URL标准化
```python
def normalize_url(url: str, platform: str) -> str:
    """将URL标准化为统一格式"""
    # 移除查询参数和片段标识符
    from urllib.parse import urlparse, urlunparse
    
    parsed = urlparse(url)
    normalized = urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        '',  # params
        '',  # query
        ''   # fragment
    ))
    
    return normalized
```

## 4. 数据库存储规范

### 4.1 字段定义
```sql
-- videos表中的URL相关字段
ALTER TABLE videos ADD COLUMN IF NOT EXISTS original_url TEXT NOT NULL;
ALTER TABLE videos ADD COLUMN IF NOT EXISTS platform VARCHAR(50) NOT NULL;
ALTER TABLE videos ADD COLUMN IF NOT EXISTS platform_video_id VARCHAR(255);

-- download_tasks表中的URL相关字段
ALTER TABLE download_tasks ADD COLUMN IF NOT EXISTS url TEXT NOT NULL;
ALTER TABLE download_tasks ADD COLUMN IF NOT EXISTS platform VARCHAR(50);
ALTER TABLE download_tasks ADD COLUMN IF NOT EXISTS original_video_id VARCHAR(255);
```

### 4.2 约束和索引
```sql
-- 创建检查约束
ALTER TABLE videos ADD CONSTRAINT chk_platform 
CHECK (platform IN ('douyin', 'tiktok', 'bilibili', 'xiaohongshu', 'kuaishou', 'weixin', 'youtube'));

-- 创建索引
CREATE INDEX idx_videos_platform_url ON videos(platform, original_url);
CREATE INDEX idx_download_tasks_platform_status ON download_tasks(platform, status);
CREATE INDEX idx_download_tasks_url_hash ON download_tasks(MD5(url));
```

## 5. 错误处理和边界情况

### 5.1 常见错误类型
1. **无效URL格式**: URL不符合平台规范
2. **不支持的平台**: URL来自不支持的视频平台
3. **私有视频**: 视频设置为私有或已删除
4. **地区限制**: 视频在当前地区不可访问
5. **网络错误**: 无法访问目标URL

### 5.2 错误处理策略
```python
class URLValidationError(Exception):
    """URL验证错误"""
    pass

class UnsupportedPlatformError(URLValidationError):
    """不支持的平台错误"""
    pass

class InvalidURLFormatError(URLValidationError):
    """无效URL格式错误"""
    pass

def handle_url_error(error: Exception, url: str) -> Dict[str, any]:
    """统一处理URL相关错误"""
    if isinstance(error, UnsupportedPlatformError):
        return {
            'code': 'UNSUPPORTED_PLATFORM',
            'message': '不支持的视频平台',
            'url': url
        }
    elif isinstance(error, InvalidURLFormatError):
        return {
            'code': 'INVALID_URL_FORMAT',
            'message': 'URL格式不正确',
            'url': url
        }
    else:
        return {
            'code': 'UNKNOWN_ERROR',
            'message': str(error),
            'url': url
        }
```

## 6. 测试用例

### 6.1 有效URL测试
```python
valid_urls = [
    'https://www.douyin.com/video/7234567890123456789',
    'https://v.douyin.com/ieFyPqR/',
    'https://www.tiktok.com/@username/video/7234567890123456789',
    'https://vm.tiktok.com/ZMeFyPqR/',
    'https://www.bilibili.com/video/BV1xx411c7mD',
    'https://b23.tv/BV1xx411c7mD',
    'https://www.xiaohongshu.com/explore/64a1b2c3d4e5f6789012',
    'https://www.kuaishou.com/short-video/3xbCqARqrqE'
]
```

### 6.2 无效URL测试
```python
invalid_urls = [
    'https://www.youtube.com/watch?v=dQw4w9WgXcQ',  # 不支持的平台
    'https://www.douyin.com/invalid/path',          # 无效路径
    'not-a-url',                                    # 不是URL
    'https://www.bilibili.com/video/',              # 缺少视频ID
]
```

---

*文档版本: 1.0*  
*更新时间: 2025-01-21*