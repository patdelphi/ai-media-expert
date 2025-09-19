#!/usr/bin/env python3
"""为video_analyses表添加user_id字段的数据库迁移脚本

该脚本用于修复视频解析功能中缺少user_id字段的问题。
"""

import sqlite3
import sys
from pathlib import Path

def add_user_id_column():
    """为video_analyses表添加user_id字段"""
    db_path = Path("ai_media_expert.db")
    
    if not db_path.exists():
        print("❌ 数据库文件不存在")
        return False
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # 检查user_id字段是否已存在
        cursor.execute("PRAGMA table_info(video_analyses)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'user_id' in columns:
            print("✅ user_id字段已存在，无需添加")
            return True
        
        # 添加user_id字段
        print("📝 正在添加user_id字段...")
        cursor.execute("""
            ALTER TABLE video_analyses 
            ADD COLUMN user_id VARCHAR(255) 
            REFERENCES users(id)
        """)
        
        # 创建索引
        print("📝 正在创建索引...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS ix_video_analyses_user_id 
            ON video_analyses(user_id)
        """)
        
        conn.commit()
        print("✅ user_id字段添加成功")
        
        # 验证字段是否添加成功
        cursor.execute("PRAGMA table_info(video_analyses)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'user_id' in columns:
            print("✅ 验证通过：user_id字段已成功添加")
            return True
        else:
            print("❌ 验证失败：user_id字段未添加")
            return False
            
    except sqlite3.Error as e:
        print(f"❌ 数据库操作失败: {e}")
        return False
    finally:
        if conn:
            conn.close()

def main():
    """主函数"""
    print("🔧 开始为video_analyses表添加user_id字段...")
    print("=" * 50)
    
    success = add_user_id_column()
    
    if success:
        print("=" * 50)
        print("✅ 迁移完成！")
        sys.exit(0)
    else:
        print("=" * 50)
        print("❌ 迁移失败！")
        sys.exit(1)

if __name__ == "__main__":
    main()