#!/usr/bin/env python3
"""
数据库表创建脚本
创建缺失的数据库表，确保与模型定义一致
"""

import sqlite3
import sys
from datetime import datetime

def create_missing_tables():
    """创建缺失的数据库表"""
    try:
        conn = sqlite3.connect('ai_media_expert.db')
        cursor = conn.cursor()
        
        print("🔧 开始创建缺失的数据库表...")
        
        # 1. 创建 download_tasks 表
        print("📝 创建 download_tasks 表...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS download_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                url TEXT NOT NULL,
                platform VARCHAR(50),
                status VARCHAR(20) NOT NULL DEFAULT 'pending',
                progress INTEGER NOT NULL DEFAULT 0,
                quality VARCHAR(20),
                format_preference VARCHAR(20),
                audio_only BOOLEAN NOT NULL DEFAULT 0,
                video_id INTEGER,
                file_path TEXT,
                error_message TEXT,
                started_at DATETIME,
                completed_at DATETIME,
                options JSON,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (video_id) REFERENCES videos (id)
            )
        ''')
        
        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_download_tasks_user_id ON download_tasks (user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_download_tasks_video_id ON download_tasks (video_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_download_tasks_status ON download_tasks (status)')
        
        # 2. 创建 analysis_tasks 表
        print("📝 创建 analysis_tasks 表...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analysis_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                video_id INTEGER NOT NULL,
                template_id INTEGER,
                status VARCHAR(20) NOT NULL DEFAULT 'pending',
                progress INTEGER NOT NULL DEFAULT 0,
                analysis_type VARCHAR(50),
                config JSON,
                result_data JSON,
                result_summary TEXT,
                confidence_score FLOAT,
                error_message TEXT,
                started_at DATETIME,
                completed_at DATETIME,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (video_id) REFERENCES videos (id)
            )
        ''')
        
        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_analysis_tasks_user_id ON analysis_tasks (user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_analysis_tasks_video_id ON analysis_tasks (video_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_analysis_tasks_status ON analysis_tasks (status)')
        
        # 3. 创建 download_history 表
        print("📝 创建 download_history 表...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS download_history (
                id VARCHAR(255) PRIMARY KEY,
                user_id VARCHAR(255) NOT NULL,
                task_id VARCHAR(255),
                original_url TEXT NOT NULL,
                video_title VARCHAR(500),
                video_id VARCHAR(100),
                platform VARCHAR(50) NOT NULL,
                video_duration INTEGER,
                author_name VARCHAR(200),
                author_id VARCHAR(100),
                download_format VARCHAR(20),
                download_quality VARCHAR(20),
                download_options TEXT,
                status VARCHAR(20) NOT NULL DEFAULT 'pending',
                file_path TEXT,
                file_size INTEGER,
                download_speed FLOAT,
                download_time INTEGER,
                error_message TEXT,
                retry_count INTEGER DEFAULT 0,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_download_history_user_id ON download_history (user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_download_history_platform ON download_history (platform)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_download_history_status ON download_history (status)')
        
        # 4. 创建 download_statistics 表
        print("📝 创建 download_statistics 表...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS download_statistics (
                id VARCHAR(255) PRIMARY KEY,
                user_id VARCHAR(255) NOT NULL,
                date DATETIME NOT NULL,
                platform VARCHAR(50),
                total_downloads INTEGER NOT NULL DEFAULT 0,
                successful_downloads INTEGER NOT NULL DEFAULT 0,
                failed_downloads INTEGER NOT NULL DEFAULT 0,
                cancelled_downloads INTEGER NOT NULL DEFAULT 0,
                total_file_size INTEGER NOT NULL DEFAULT 0,
                total_duration INTEGER NOT NULL DEFAULT 0,
                total_download_time INTEGER NOT NULL DEFAULT 0,
                avg_download_speed FLOAT,
                peak_download_speed FLOAT,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_download_statistics_user_id ON download_statistics (user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_download_statistics_date ON download_statistics (date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_download_statistics_platform ON download_statistics (platform)')
        
        # 5. 创建 download_tags 表
        print("📝 创建 download_tags 表...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS download_tags (
                id VARCHAR(255) PRIMARY KEY,
                user_id VARCHAR(255) NOT NULL,
                name VARCHAR(100) NOT NULL,
                color VARCHAR(20),
                description TEXT,
                usage_count INTEGER NOT NULL DEFAULT 0,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_download_tags_user_id ON download_tags (user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_download_tags_user_name ON download_tags (user_id, name)')
        
        # 6. 创建 user_sessions 表
        print("📝 创建 user_sessions 表...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                session_token VARCHAR(255) UNIQUE NOT NULL,
                refresh_token VARCHAR(255) UNIQUE,
                device_info TEXT,
                ip_address VARCHAR(45),
                user_agent TEXT,
                is_active BOOLEAN NOT NULL DEFAULT 1,
                expires_at DATETIME NOT NULL,
                last_activity_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions (user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_sessions_session_token ON user_sessions (session_token)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_sessions_refresh_token ON user_sessions (refresh_token)')
        
        # 提交事务
        conn.commit()
        
        # 验证表创建
        print("\n✅ 验证表创建结果...")
        tables_to_check = [
            'download_tasks', 'analysis_tasks', 'download_history', 
            'download_statistics', 'download_tags', 'user_sessions'
        ]
        
        for table_name in tables_to_check:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
            result = cursor.fetchone()
            if result:
                print(f"✅ {table_name} 表创建成功")
            else:
                print(f"❌ {table_name} 表创建失败")
        
        print("\n🎉 所有缺失表创建完成！")
        
    except Exception as e:
        print(f"❌ 创建表时发生错误: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()
    
    return True

if __name__ == "__main__":
    success = create_missing_tables()
    sys.exit(0 if success else 1)