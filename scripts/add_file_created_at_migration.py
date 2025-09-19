#!/usr/bin/env python3
"""数据库迁移脚本 - 添加文件原始生成时间字段

为uploaded_files表添加file_created_at字段。
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
    print("开始添加文件原始生成时间字段...")
    
    # SQL语句
    migration_sql = [
        "ALTER TABLE uploaded_files ADD COLUMN file_created_at TIMESTAMP WITH TIME ZONE;",
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
                print("\n✅ 字段添加成功！")
                
            except Exception as e:
                # 回滚事务
                trans.rollback()
                print(f"\n❌ 迁移失败，已回滚: {e}")
                raise
                
    except Exception as e:
        print(f"\n❌ 数据库连接失败: {e}")
        sys.exit(1)

def main():
    """主函数"""
    print("=== 文件原始生成时间字段迁移脚本 ===")
    
    # 执行迁移
    run_migration()
    
    print("\n=== 迁移完成 ===")

if __name__ == "__main__":
    main()