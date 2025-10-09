#!/usr/bin/env python3
"""数据库迁移脚本 - 添加视频信息字段

为uploaded_files表添加完整的视频信息字段。
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from app.core.database import engine

def run_migration():
    """执行数据库迁移"""
    print("开始添加视频信息字段...")
    
    # SQL语句列表
    migration_sql = [
        # 基本视频信息
        "ALTER TABLE uploaded_files ADD COLUMN format_name VARCHAR(100);",
        "ALTER TABLE uploaded_files ADD COLUMN format_long_name VARCHAR(255);",
        "ALTER TABLE uploaded_files ADD COLUMN bit_rate BIGINT;",
        
        # 视频流信息
        "ALTER TABLE uploaded_files ADD COLUMN width INTEGER;",
        "ALTER TABLE uploaded_files ADD COLUMN height INTEGER;",
        "ALTER TABLE uploaded_files ADD COLUMN video_codec VARCHAR(50);",
        "ALTER TABLE uploaded_files ADD COLUMN video_codec_long VARCHAR(255);",
        "ALTER TABLE uploaded_files ADD COLUMN frame_rate VARCHAR(20);",
        "ALTER TABLE uploaded_files ADD COLUMN avg_frame_rate VARCHAR(20);",
        "ALTER TABLE uploaded_files ADD COLUMN aspect_ratio VARCHAR(20);",
        "ALTER TABLE uploaded_files ADD COLUMN pixel_format VARCHAR(50);",
        "ALTER TABLE uploaded_files ADD COLUMN video_bit_rate BIGINT;",
        "ALTER TABLE uploaded_files ADD COLUMN nb_frames BIGINT;",
        
        # 音频流信息
        "ALTER TABLE uploaded_files ADD COLUMN audio_codec VARCHAR(50);",
        "ALTER TABLE uploaded_files ADD COLUMN audio_codec_long VARCHAR(255);",
        "ALTER TABLE uploaded_files ADD COLUMN sample_rate INTEGER;",
        "ALTER TABLE uploaded_files ADD COLUMN channels INTEGER;",
        "ALTER TABLE uploaded_files ADD COLUMN channel_layout VARCHAR(50);",
        "ALTER TABLE uploaded_files ADD COLUMN audio_bit_rate BIGINT;",
        
        # 颜色和质量信息
        "ALTER TABLE uploaded_files ADD COLUMN color_space VARCHAR(50);",
        "ALTER TABLE uploaded_files ADD COLUMN color_range VARCHAR(50);",
        "ALTER TABLE uploaded_files ADD COLUMN color_transfer VARCHAR(50);",
        "ALTER TABLE uploaded_files ADD COLUMN color_primaries VARCHAR(50);",
        "ALTER TABLE uploaded_files ADD COLUMN profile VARCHAR(100);",
        "ALTER TABLE uploaded_files ADD COLUMN level VARCHAR(20);",
        
        # 元数据
        "ALTER TABLE uploaded_files ADD COLUMN encoder VARCHAR(255);",
        "ALTER TABLE uploaded_files ADD COLUMN creation_time TIMESTAMP WITH TIME ZONE;",
    ]
    
    try:
        with engine.connect() as conn:
            # 开始事务
            trans = conn.begin()
            
            try:
                for sql in migration_sql:
                    print(f"执行: {sql}")
                    conn.execute(text(sql))
                
                # 提交事务
                trans.commit()
                print("\n✅ 所有字段添加成功！")
                
            except Exception as e:
                # 回滚事务
                trans.rollback()
                print(f"\n❌ 迁移失败，已回滚: {e}")
                raise
                
    except Exception as e:
        print(f"\n❌ 数据库连接失败: {e}")
        sys.exit(1)

def check_existing_columns():
    """检查已存在的列"""
    print("检查现有表结构...")
    
    try:
        with engine.connect() as conn:
            # 查询表结构
            result = conn.execute(text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'uploaded_files' ORDER BY ordinal_position;"
            ))
            
            columns = [row[0] for row in result]
            print(f"现有列: {', '.join(columns)}")
            
            # 检查是否已有新字段
            new_fields = ['width', 'height', 'video_codec', 'audio_codec']
            existing_new_fields = [field for field in new_fields if field in columns]
            
            if existing_new_fields:
                print(f"\n⚠️  警告: 以下字段已存在: {', '.join(existing_new_fields)}")
                return False
            else:
                print("\n✅ 可以安全执行迁移")
                return True
                
    except Exception as e:
        print(f"\n❌ 检查表结构失败: {e}")
        return False

def main():
    """主函数"""
    print("=== 视频信息字段迁移脚本 ===")
    
    # 检查现有表结构
    if not check_existing_columns():
        response = input("\n是否继续执行迁移？(y/N): ")
        if response.lower() != 'y':
            print("迁移已取消")
            return
    
    # 执行迁移
    run_migration()
    
    print("\n=== 迁移完成 ===")
    print("现在可以上传视频文件，系统将自动获取并保存完整的视频信息。")

if __name__ == "__main__":
    main()