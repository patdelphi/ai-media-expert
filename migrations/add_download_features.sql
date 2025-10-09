-- 数据迁移脚本：添加下载功能支持
-- 文件：migrations/add_download_features.sql
-- 创建时间：2025-01-20
-- 说明：扩展现有表结构，添加视频下载功能所需的字段和表
-- 数据库类型：SQLite

-- 1. 扩展videos表 - 添加下载相关字段
ALTER TABLE videos ADD COLUMN source_type VARCHAR(20) DEFAULT 'upload';
ALTER TABLE videos ADD COLUMN download_task_id INTEGER;
ALTER TABLE videos ADD COLUMN original_platform_id VARCHAR(255);
ALTER TABLE videos ADD COLUMN download_quality VARCHAR(20);
ALTER TABLE videos ADD COLUMN download_format VARCHAR(10);
ALTER TABLE videos ADD COLUMN thumbnail_url TEXT;
ALTER TABLE videos ADD COLUMN download_metadata TEXT DEFAULT '{}';

-- 2. 扩展download_tasks表 - 添加视频元数据和统计信息
ALTER TABLE download_tasks ADD COLUMN video_title TEXT;
ALTER TABLE download_tasks ADD COLUMN video_description TEXT;
ALTER TABLE download_tasks ADD COLUMN author_name VARCHAR(255);
ALTER TABLE download_tasks ADD COLUMN author_id VARCHAR(255);
ALTER TABLE download_tasks ADD COLUMN author_avatar_url TEXT;
ALTER TABLE download_tasks ADD COLUMN thumbnail_url TEXT;
ALTER TABLE download_tasks ADD COLUMN duration INTEGER;
ALTER TABLE download_tasks ADD COLUMN view_count INTEGER DEFAULT 0;
ALTER TABLE download_tasks ADD COLUMN like_count INTEGER DEFAULT 0;
ALTER TABLE download_tasks ADD COLUMN comment_count INTEGER DEFAULT 0;
ALTER TABLE download_tasks ADD COLUMN share_count INTEGER DEFAULT 0;
ALTER TABLE download_tasks ADD COLUMN original_video_id VARCHAR(255);
ALTER TABLE download_tasks ADD COLUMN download_speed INTEGER;
ALTER TABLE download_tasks ADD COLUMN eta INTEGER;
ALTER TABLE download_tasks ADD COLUMN file_size INTEGER;
ALTER TABLE download_tasks ADD COLUMN download_config TEXT DEFAULT '{}';
ALTER TABLE download_tasks ADD COLUMN parsed_data TEXT DEFAULT '{}';
ALTER TABLE download_tasks ADD COLUMN subtitles_available INTEGER DEFAULT 0;
ALTER TABLE download_tasks ADD COLUMN subtitles_downloaded INTEGER DEFAULT 0;

-- 3. 创建下载平台配置表
CREATE TABLE download_platforms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(50) UNIQUE NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    icon VARCHAR(100),
    color VARCHAR(20),
    enabled INTEGER DEFAULT 1,
    supported_features TEXT DEFAULT '[]',
    quality_options TEXT DEFAULT '[]',
    format_options TEXT DEFAULT '[]',
    api_endpoint VARCHAR(255),
    rate_limit INTEGER DEFAULT 10,
    timeout INTEGER DEFAULT 300,
    config TEXT DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. 创建下载统计表
CREATE TABLE download_statistics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id),
    platform VARCHAR(50),
    date DATE NOT NULL,
    total_downloads INTEGER DEFAULT 0,
    successful_downloads INTEGER DEFAULT 0,
    failed_downloads INTEGER DEFAULT 0,
    total_size INTEGER DEFAULT 0,
    total_duration INTEGER DEFAULT 0,
    avg_download_speed INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. 创建下载队列表
CREATE TABLE download_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER REFERENCES download_tasks(id) NOT NULL,
    priority INTEGER DEFAULT 5,
    status VARCHAR(20) DEFAULT 'queued',
    worker_id VARCHAR(100),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. 创建索引优化查询性能
CREATE INDEX idx_videos_source_type ON videos(source_type);
CREATE INDEX idx_videos_download_task_id ON videos(download_task_id);
CREATE INDEX idx_download_tasks_status ON download_tasks(status);
CREATE INDEX idx_download_tasks_platform ON download_tasks(platform);
CREATE INDEX idx_download_platforms_name ON download_platforms(name);
CREATE INDEX idx_download_statistics_platform_date ON download_statistics(platform, date DESC);
CREATE INDEX idx_download_queue_status_priority ON download_queue(status, priority ASC);

-- 7. 插入默认平台配置数据
INSERT OR IGNORE INTO download_platforms (name, display_name, icon, color, supported_features, quality_options, format_options) VALUES
('douyin', '抖音', 'fab fa-tiktok', 'text-red-500', '["video", "image"]', '["720p", "1080p", "original"]', '["mp4"]'),
('tiktok', 'TikTok', 'fab fa-tiktok', 'text-black', '["video"]', '["720p", "1080p", "original"]', '["mp4"]'),
('bilibili', 'B站', 'fas fa-video', 'text-blue-500', '["video"]', '["360p", "480p", "720p", "1080p"]', '["mp4", "flv"]'),
('xiaohongshu', '小红书', 'fas fa-book', 'text-pink-500', '["video", "image"]', '["720p", "1080p"]', '["mp4"]'),
('kuaishou', '快手', 'fas fa-play', 'text-yellow-500', '["video"]', '["720p", "1080p"]', '["mp4"]'),
('weixin', '微信视频号', 'fab fa-weixin', 'text-green-500', '["video"]', '["720p", "1080p"]', '["mp4"]');