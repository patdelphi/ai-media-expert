#!/usr/bin/env python3
"""
添加video_url字段到video_analyses表的数据库迁移脚本

用于支持GLM-4.5V等视频理解模型，添加视频URL字段存储视频的可访问地址。
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.core.database import SessionLocal, engine
<<<<<<< HEAD
from app.core.app_logging import setup_logging
=======
from app.core.logging import setup_logging
>>>>>>> bf58121 (feat: 优化视频分析流式输出和历史记录功能)

def add_video_url_column():
    """添加video_url字段到video_analyses表"""
    
    # 设置日志
    logger = setup_logging()
    
    print("🔧 开始添加video_url字段到video_analyses表...")
    
    db = SessionLocal()
    
    try:
        # 检查字段是否已存在
        result = db.execute(text("""
            SELECT COUNT(*) as count
            FROM pragma_table_info('video_analyses')
            WHERE name = 'video_url'
        """))
        
        count = result.fetchone()[0]
        
        if count > 0:
            print("✅ video_url字段已存在，跳过迁移")
            return
        
        # 添加video_url字段
        db.execute(text("""
            ALTER TABLE video_analyses 
            ADD COLUMN video_url VARCHAR(1000)
        """))
        
        # 添加字段注释（SQLite不直接支持，但我们可以记录）
        print("📝 添加video_url字段注释：视频文件的可访问URL，用于AI视频理解")
        
        db.commit()
        print("✅ 成功添加video_url字段到video_analyses表")
        
        # 验证字段添加
        result = db.execute(text("""
            SELECT COUNT(*) as count
            FROM pragma_table_info('video_analyses')
            WHERE name = 'video_url'
        """))
        
        count = result.fetchone()[0]
        if count == 1:
            print("✅ 字段添加验证成功")
        else:
            print("❌ 字段添加验证失败")
            
    except Exception as e:
        print(f"❌ 迁移失败: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

def main():
    """主函数"""
    print("🎬 视频URL字段迁移脚本")
    print("=" * 50)
    
    try:
        add_video_url_column()
        print("\n🎉 迁移完成！")
        print("\n📋 迁移内容：")
        print("  - 添加video_url字段到video_analyses表")
        print("  - 字段类型：VARCHAR(1000)")
        print("  - 字段用途：存储视频文件的可访问URL，用于GLM-4.5V等视频理解模型")
        print("\n💡 使用说明：")
        print("  - GLM-4.5V模型现在可以直接分析视频内容")
        print("  - 其他模型仍使用元数据分析方式")
        print("  - 系统会自动根据模型类型选择处理方式")
        
    except Exception as e:
        print(f"\n❌ 迁移失败: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()