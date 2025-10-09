#!/usr/bin/env python3
"""
数据库迁移执行脚本 - 下载功能扩展
文件：scripts/run_download_migration.py
创建时间：2025-01-20
说明：执行下载功能相关的数据库结构扩展迁移
"""

import os
import sys
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import SessionLocal, engine
from app.core.config import settings

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def read_migration_file():
    """读取迁移SQL文件"""
    migration_file = project_root / "migrations" / "add_download_features.sql"
    
    if not migration_file.exists():
        raise FileNotFoundError(f"迁移文件不存在: {migration_file}")
    
    with open(migration_file, 'r', encoding='utf-8') as f:
        return f.read()

def check_existing_tables():
    """检查现有表结构"""
    try:
        # 直接使用engine获取原始连接
        conn = engine.raw_connection()
        cursor = conn.cursor()
        
        # 检查必要的表是否存在
        required_tables = ['users', 'videos', 'download_tasks']
        existing_tables = []
        
        for table in required_tables:
            # SQLite语法检查表是否存在
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name=?
            """, (table,))
            
            if cursor.fetchone():
                existing_tables.append(table)
                logger.info(f"✓ 表 {table} 已存在")
            else:
                logger.warning(f"✗ 表 {table} 不存在")
        
        cursor.close()
        conn.close()
        
        return len(existing_tables) == len(required_tables)
        
    except Exception as e:
        logger.error(f"检查表结构失败: {e}")
        return False

def backup_existing_data():
    """备份现有数据（可选）"""
    try:
        conn = engine.raw_connection()
        cursor = conn.cursor()
        
        # 备份关键表的数据统计
        tables_to_check = ['videos', 'download_tasks']
        backup_info = {}
        
        for table in tables_to_check:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                backup_info[table] = count
                logger.info(f"表 {table} 当前记录数: {count}")
            except Exception as e:
                logger.warning(f"无法获取表 {table} 的记录数: {e}")
                backup_info[table] = 0
        
        cursor.close()
        conn.close()
        
        return backup_info
        
    except Exception as e:
        logger.error(f"备份数据统计失败: {e}")
        return {}

def execute_migration():
    """执行数据库迁移"""
    try:
        # 读取迁移SQL
        migration_sql = read_migration_file()
        logger.info("已读取迁移SQL文件")
        
        # 获取数据库连接
        conn = engine.raw_connection()
        cursor = conn.cursor()
        
        # 执行迁移
        logger.info("开始执行数据库迁移...")
        
        # 分割SQL语句并逐个执行
        statements = [stmt.strip() for stmt in migration_sql.split(';') if stmt.strip()]
        
        for i, statement in enumerate(statements):
            if statement:
                try:
                    logger.info(f"执行语句 {i+1}/{len(statements)}: {statement[:50]}...")
                    cursor.execute(statement)
                    conn.commit()
                except Exception as e:
                    # 忽略已存在的列或表的错误
                    if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                        logger.warning(f"跳过已存在的结构: {e}")
                        continue
                    else:
                        raise e
        
        logger.info("✓ 数据库迁移执行成功")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"执行迁移失败: {e}")
        return False

def verify_migration():
    """验证迁移结果"""
    try:
        conn = engine.raw_connection()
        cursor = conn.cursor()
        
        # 检查新增的表
        new_tables = ['download_platforms', 'download_statistics', 'download_queue']
        
        for table in new_tables:
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name=?
            """, (table,))
            
            if cursor.fetchone():
                logger.info(f"✓ 新表 {table} 创建成功")
            else:
                logger.error(f"✗ 新表 {table} 创建失败")
                return False
        
        # 检查新增的字段（示例：videos表的source_type字段）
        cursor.execute("PRAGMA table_info(videos)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'source_type' in columns:
            logger.info("✓ videos表新字段添加成功")
        else:
            logger.error("✗ videos表新字段添加失败")
            return False
        
        # 检查默认数据
        cursor.execute("SELECT COUNT(*) FROM download_platforms")
        platform_count = cursor.fetchone()[0]
        
        if platform_count >= 6:  # 应该有6个默认平台
            logger.info(f"✓ 默认平台数据插入成功 ({platform_count}个平台)")
        else:
            logger.warning(f"默认平台数据可能不完整 ({platform_count}个平台)")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"验证迁移结果失败: {e}")
        return False

def main():
    """主函数"""
    logger.info("=== 开始执行下载功能数据库迁移 ===")
    
    # 1. 检查现有表结构
    logger.info("1. 检查现有表结构...")
    if not check_existing_tables():
        logger.error("必要的表不存在，请先运行基础数据库初始化")
        return False
    
    # 2. 备份现有数据统计
    logger.info("2. 备份现有数据统计...")
    backup_info = backup_existing_data()
    
    # 3. 执行迁移
    logger.info("3. 执行数据库迁移...")
    if not execute_migration():
        logger.error("迁移执行失败")
        return False
    
    # 4. 验证迁移结果
    logger.info("4. 验证迁移结果...")
    if not verify_migration():
        logger.error("迁移验证失败")
        return False
    
    logger.info("=== 下载功能数据库迁移完成 ===")
    logger.info("新增功能:")
    logger.info("- 扩展了videos表，支持下载来源标识")
    logger.info("- 扩展了download_tasks表，支持视频元数据")
    logger.info("- 新增download_platforms表，管理支持的平台")
    logger.info("- 新增download_statistics表，统计下载数据")
    logger.info("- 新增download_queue表，管理下载队列")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)