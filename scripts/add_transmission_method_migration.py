#!/usr/bin/env python3
"""
添加transmission_method字段的数据库迁移脚本

为video_analyses表添加transmission_method字段，用于支持不同的视频传输方式。
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

def add_transmission_method_column():
    """添加transmission_method字段"""
    print("开始添加transmission_method字段...")
    
    db = SessionLocal()
    
    try:
        # 检查字段是否已存在
        result = db.execute(text("""
            SELECT COUNT(*) as count 
            FROM pragma_table_info('video_analyses') 
            WHERE name = 'transmission_method'
        """))
        
        count = result.fetchone()[0]
        
        if count > 0:
            print("✅ transmission_method字段已存在，无需添加")
            return True
        
        # 添加字段
        db.execute(text("""
            ALTER TABLE video_analyses 
            ADD COLUMN transmission_method VARCHAR(20) DEFAULT 'url' NOT NULL
        """))
        
        db.commit()
        print("✅ 成功添加transmission_method字段")
        
        # 验证字段添加成功
        result = db.execute(text("""
            SELECT COUNT(*) as count 
            FROM pragma_table_info('video_analyses') 
            WHERE name = 'transmission_method'
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
    """更新现有记录的transmission_method字段"""
    print("\n开始更新现有记录...")
    
    db = SessionLocal()
    
    try:
        # 查询需要更新的记录（transmission_method为NULL或空的记录）
        result = db.execute(text("""
            SELECT COUNT(*) as count
            FROM video_analyses 
            WHERE transmission_method IS NULL OR transmission_method = ''
        """))
        
        count = result.fetchone()[0]
        
        if count == 0:
            print("✅ 没有需要更新的记录")
            return True
        
        print(f"📊 找到 {count} 条需要更新的记录")
        
        # 更新所有记录为默认的URL方式
        result = db.execute(text("""
            UPDATE video_analyses 
            SET transmission_method = 'url' 
            WHERE transmission_method IS NULL OR transmission_method = ''
        """))
        
        updated_count = result.rowcount
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
            WHERE name = 'transmission_method'
        """))
        
        field_info = result.fetchone()
        
        if field_info:
            name, field_type, not_null, default_value = field_info
            print(f"✅ 字段信息: {name} {field_type} (NOT NULL: {bool(not_null)}, DEFAULT: {default_value})")
        else:
            print("❌ 字段不存在")
            return False
        
        # 检查数据分布
        result = db.execute(text("""
            SELECT 
                transmission_method,
                COUNT(*) as count
            FROM video_analyses
            GROUP BY transmission_method
            ORDER BY count DESC
        """))
        
        distribution = result.fetchall()
        
        print(f"📊 传输方式分布:")
        for method, count in distribution:
            print(f"  {method}: {count} 条记录")
        
        # 检查总记录数
        result = db.execute(text("""
            SELECT COUNT(*) as total
            FROM video_analyses
        """))
        
        total = result.fetchone()[0]
        print(f"📊 总记录数: {total}")
        
        return True
        
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        return False
    finally:
        db.close()

def main():
    """主函数"""
    print("🚀 开始transmission_method字段迁移\n")
    
    # 添加字段
    if not add_transmission_method_column():
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
    
    print("\n🎉 transmission_method字段迁移完成！")
    print("\n💡 现在可以使用不同的视频传输方式了：")
    print("  - url: 通过公网URL访问视频（默认）")
    print("  - base64: Base64编码传输视频数据")
    print("  - upload: 上传到AI服务商（开发中）")
    print("\n🔧 前端界面已添加传输方式选择器")
    print("🔧 后端API已支持transmission_method参数")
    print("🔧 AI服务已根据传输方式智能选择处理逻辑")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)