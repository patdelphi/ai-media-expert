#!/usr/bin/env python3
"""添加AI API调试信息字段的数据库迁移脚本

为video_analyses表添加AI API调试相关的字段，用于记录和监控AI API调用的详细信息。
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from app.core.config import settings

def add_debug_info_fields():
    """添加AI API调试信息字段"""
    
    # 创建数据库引擎
    engine = create_engine(settings.database_url)
    
    print("开始添加AI API调试信息字段...")
    
    # 添加字段的SQL语句
    add_fields_sql = [
        "ALTER TABLE video_analyses ADD COLUMN api_call_time DATETIME;",
        "ALTER TABLE video_analyses ADD COLUMN api_response_time DATETIME;",
        "ALTER TABLE video_analyses ADD COLUMN api_duration REAL;",
        "ALTER TABLE video_analyses ADD COLUMN prompt_tokens INTEGER;",
        "ALTER TABLE video_analyses ADD COLUMN completion_tokens INTEGER;",
        "ALTER TABLE video_analyses ADD COLUMN total_tokens INTEGER;",
        "ALTER TABLE video_analyses ADD COLUMN temperature REAL;",
        "ALTER TABLE video_analyses ADD COLUMN max_tokens INTEGER;",
        "ALTER TABLE video_analyses ADD COLUMN model_name VARCHAR(100);",
        "ALTER TABLE video_analyses ADD COLUMN api_provider VARCHAR(50);",
        "ALTER TABLE video_analyses ADD COLUMN request_id VARCHAR(100);",
        "ALTER TABLE video_analyses ADD COLUMN debug_info JSON;"
    ]
    
    try:
        with engine.connect() as conn:
            # 检查表是否存在
            result = conn.execute(text(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='video_analyses'"
            ))
            
            if not result.fetchone():
                print("❌ video_analyses表不存在，请先运行基础迁移")
                return False
            
            # 检查字段是否已存在
            columns = conn.execute(text("PRAGMA table_info(video_analyses)")).fetchall()
            existing_columns = [col[1] for col in columns]
            
            fields_to_add = [
                ("api_call_time", "ALTER TABLE video_analyses ADD COLUMN api_call_time DATETIME;"),
                ("api_response_time", "ALTER TABLE video_analyses ADD COLUMN api_response_time DATETIME;"),
                ("api_duration", "ALTER TABLE video_analyses ADD COLUMN api_duration REAL;"),
                ("prompt_tokens", "ALTER TABLE video_analyses ADD COLUMN prompt_tokens INTEGER;"),
                ("completion_tokens", "ALTER TABLE video_analyses ADD COLUMN completion_tokens INTEGER;"),
                ("total_tokens", "ALTER TABLE video_analyses ADD COLUMN total_tokens INTEGER;"),
                ("temperature", "ALTER TABLE video_analyses ADD COLUMN temperature REAL;"),
                ("max_tokens", "ALTER TABLE video_analyses ADD COLUMN max_tokens INTEGER;"),
                ("model_name", "ALTER TABLE video_analyses ADD COLUMN model_name VARCHAR(100);"),
                ("api_provider", "ALTER TABLE video_analyses ADD COLUMN api_provider VARCHAR(50);"),
                ("request_id", "ALTER TABLE video_analyses ADD COLUMN request_id VARCHAR(100);"),
                ("debug_info", "ALTER TABLE video_analyses ADD COLUMN debug_info JSON;")
            ]
            
            added_count = 0
            for field_name, sql in fields_to_add:
                if field_name not in existing_columns:
                    try:
                        conn.execute(text(sql))
                        print(f"✅ 添加字段: {field_name}")
                        added_count += 1
                    except Exception as e:
                        print(f"❌ 添加字段 {field_name} 失败: {e}")
                else:
                    print(f"⚠️  字段 {field_name} 已存在，跳过")
            
            # 提交事务
            conn.commit()
            
            print(f"\n✅ 成功添加 {added_count} 个调试信息字段")
            
    except Exception as e:
        print(f"❌ 添加字段失败: {e}")
        return False
    
    return True

def create_debug_indexes():
    """创建调试信息相关的索引"""
    
    engine = create_engine(settings.database_url)
    
    print("创建调试信息索引...")
    
    # 创建索引的SQL语句
    create_indexes_sql = [
        "CREATE INDEX IF NOT EXISTS idx_video_analyses_api_call_time ON video_analyses (api_call_time);",
        "CREATE INDEX IF NOT EXISTS idx_video_analyses_api_provider ON video_analyses (api_provider);",
        "CREATE INDEX IF NOT EXISTS idx_video_analyses_model_name ON video_analyses (model_name);",
        "CREATE INDEX IF NOT EXISTS idx_video_analyses_total_tokens ON video_analyses (total_tokens);",
        "CREATE INDEX IF NOT EXISTS idx_video_analyses_request_id ON video_analyses (request_id);"
    ]
    
    try:
        with engine.connect() as conn:
            for index_sql in create_indexes_sql:
                conn.execute(text(index_sql))
            
            conn.commit()
            print("✅ 调试信息索引创建成功")
            
    except Exception as e:
        print(f"❌ 创建索引失败: {e}")
        return False
    
    return True

def verify_migration():
    """验证迁移结果"""
    
    engine = create_engine(settings.database_url)
    
    print("验证迁移结果...")
    
    try:
        with engine.connect() as conn:
            # 检查新字段
            columns = conn.execute(text("PRAGMA table_info(video_analyses)")).fetchall()
            column_names = [col[1] for col in columns]
            
            required_fields = [
                'api_call_time', 'api_response_time', 'api_duration',
                'prompt_tokens', 'completion_tokens', 'total_tokens',
                'temperature', 'max_tokens', 'model_name',
                'api_provider', 'request_id', 'debug_info'
            ]
            
            missing_fields = [field for field in required_fields if field not in column_names]
            if missing_fields:
                print(f"❌ 缺少字段: {missing_fields}")
                return False
            
            # 检查索引
            indexes = conn.execute(text("PRAGMA index_list(video_analyses)")).fetchall()
            index_names = [idx[1] for idx in indexes]
            
            required_indexes = [
                'idx_video_analyses_api_call_time',
                'idx_video_analyses_api_provider',
                'idx_video_analyses_model_name',
                'idx_video_analyses_total_tokens',
                'idx_video_analyses_request_id'
            ]
            
            missing_indexes = [idx for idx in required_indexes if idx not in index_names]
            if missing_indexes:
                print(f"⚠️  缺少索引: {missing_indexes}")
            
            print("✅ 迁移验证通过")
            print(f"✅ 新增调试字段数量: {len(required_fields)}")
            print(f"✅ 新增索引数量: {len(required_indexes) - len(missing_indexes)}")
            
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        return False
    
    return True

def main():
    """主函数"""
    print("=" * 60)
    print("AI API调试信息字段迁移")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 添加调试信息字段
    if not add_debug_info_fields():
        print("\n❌ 添加调试信息字段失败")
        return False
    
    # 创建索引
    if not create_debug_indexes():
        print("\n⚠️  创建索引失败，但字段已添加")
    
    # 验证迁移结果
    if not verify_migration():
        print("\n❌ 迁移验证失败")
        return False
    
    print("\n" + "=" * 60)
    print("✅ AI API调试信息字段迁移完成！")
    print("\n📋 新增功能:")
    print("  - API调用时间记录")
    print("  - Token使用统计")
    print("  - 模型参数记录")
    print("  - 详细调试信息")
    print("  - 性能监控数据")
    print("\n🚀 现在可以使用AI API调试功能了！")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)