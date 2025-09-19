#!/usr/bin/env python3
"""
添加video_file_path字段的数据库迁移脚本

为video_analyses表添加video_file_path字段，用于支持Base64视频编码功能。
"""

import sys
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import SessionLocal
<<<<<<< HEAD
from app.core.app_logging import api_logger
=======
from app.core.logging import api_logger
>>>>>>> bf58121 (feat: 优化视频分析流式输出和历史记录功能)

def add_video_file_path_column():
    """添加video_file_path字段"""
    print("开始添加video_file_path字段...")
    
    db = SessionLocal()
    
    try:
        # 检查字段是否已存在
        result = db.execute(text("""
            SELECT COUNT(*) as count 
            FROM pragma_table_info('video_analyses') 
            WHERE name = 'video_file_path'
        """))
        
        count = result.fetchone()[0]
        
        if count > 0:
            print("✅ video_file_path字段已存在，无需添加")
            return True
        
        # 添加字段
        db.execute(text("""
            ALTER TABLE video_analyses 
            ADD COLUMN video_file_path VARCHAR(1000)
        """))
        
        db.commit()
        print("✅ 成功添加video_file_path字段")
        
        # 验证字段添加成功
        result = db.execute(text("""
            SELECT COUNT(*) as count 
            FROM pragma_table_info('video_analyses') 
            WHERE name = 'video_file_path'
        """))
        
        count = result.fetchone()[0]
        
        if count > 0:
            print("✅ 字段添加验证成功")
            return True
        else:
            print("❌ 字段添加验证失败")
            return False
            
    except Exception as e:
        print(f"❌ 添加字段失败: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def update_existing_records():
    """更新现有记录的video_file_path字段"""
    print("\n开始更新现有记录...")
    
    db = SessionLocal()
    
    try:
        # 查询需要更新的记录
        result = db.execute(text("""
            SELECT va.id, va.video_file_id, uf.file_path
            FROM video_analyses va
            JOIN uploaded_files uf ON va.video_file_id = uf.id
            WHERE va.video_file_path IS NULL
        """))
        
        records = result.fetchall()
        
        if not records:
            print("✅ 没有需要更新的记录")
            return True
        
        print(f"📊 找到 {len(records)} 条需要更新的记录")
        
        # 更新每条记录
        updated_count = 0
        for record in records:
            analysis_id, video_file_id, file_path = record
            
            try:
                db.execute(text("""
                    UPDATE video_analyses 
                    SET video_file_path = :file_path 
                    WHERE id = :analysis_id
                """), {
                    'file_path': file_path,
                    'analysis_id': analysis_id
                })
                
                updated_count += 1
                
            except Exception as e:
                print(f"⚠️ 更新记录 {analysis_id} 失败: {e}")
                continue
        
        db.commit()
        print(f"✅ 成功更新 {updated_count} 条记录")
        
        return True
        
    except Exception as e:
        print(f"❌ 更新记录失败: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def verify_migration():
    """验证迁移结果"""
    print("\n开始验证迁移结果...")
    
    db = SessionLocal()
    
    try:
        # 检查字段结构
        result = db.execute(text("""
            SELECT name, type, "notnull", dflt_value 
            FROM pragma_table_info('video_analyses') 
            WHERE name = 'video_file_path'
        """))
        
        field_info = result.fetchone()
        
        if field_info:
            name, field_type, not_null, default_value = field_info
            print(f"✅ 字段信息: {name} {field_type} (NOT NULL: {bool(not_null)})")
        else:
            print("❌ 字段不存在")
            return False
        
        # 检查数据
        result = db.execute(text("""
            SELECT 
                COUNT(*) as total,
                COUNT(video_file_path) as with_path,
                COUNT(*) - COUNT(video_file_path) as without_path
            FROM video_analyses
        """))
        
        stats = result.fetchone()
        total, with_path, without_path = stats
        
        print(f"📊 数据统计:")
        print(f"  总记录数: {total}")
        print(f"  有路径的记录: {with_path}")
        print(f"  无路径的记录: {without_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        return False
    finally:
        db.close()

def main():
    """主函数"""
    print("🚀 开始video_file_path字段迁移\n")
    
    # 添加字段
    if not add_video_file_path_column():
        print("❌ 字段添加失败，终止迁移")
        return False
    
    # 更新现有记录
    if not update_existing_records():
        print("❌ 记录更新失败，但字段已添加")
        return False
    
    # 验证迁移
    if not verify_migration():
        print("❌ 迁移验证失败")
        return False
    
    print("\n🎉 video_file_path字段迁移完成！")
    print("\n💡 现在可以使用Base64视频编码功能了：")
    print("  - URL方式失败时自动回退到Base64编码")
    print("  - 支持ffmpeg压缩以减小文件大小")
    print("  - 适合小于10MB的视频文件")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)