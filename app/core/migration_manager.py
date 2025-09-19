#!/usr/bin/env python3
"""
数据库迁移管理系统

提供数据库版本控制、迁移脚本管理、自动升级等功能。
支持SQLite和其他数据库的迁移管理。
"""

import os
import sys
import json
import time
import sqlite3
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.core.config import settings
from app.core.database import engine
from sqlalchemy import text, inspect


@dataclass
class Migration:
    """迁移记录数据类"""
    id: str
    name: str
    description: str
    version: str
    sql_up: str
    sql_down: str
    checksum: str
    created_at: str
    applied_at: Optional[str] = None
    status: str = "pending"  # pending, applied, failed


class MigrationManager:
    """数据库迁移管理器"""
    
    def __init__(self):
        self.migrations_dir = project_root / "migrations"
        self.migrations_dir.mkdir(exist_ok=True)
        self.migration_table = "schema_migrations"
        self._ensure_migration_table()
    
    def _ensure_migration_table(self):
        """确保迁移表存在"""
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {self.migration_table} (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            version TEXT NOT NULL,
            checksum TEXT NOT NULL,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'applied'
        )
        """
        
        try:
            with engine.connect() as conn:
                conn.execute(text(create_table_sql))
                conn.commit()
        except Exception as e:
            print(f"❌ 创建迁移表失败: {e}")
            raise
    
    def generate_migration_id(self) -> str:
        """生成迁移ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"migration_{timestamp}"
    
    def calculate_checksum(self, content: str) -> str:
        """计算内容校验和"""
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def create_migration(self, name: str, description: str = "", sql_up: str = "", sql_down: str = "") -> str:
        """创建新的迁移文件"""
        migration_id = self.generate_migration_id()
        version = datetime.now().strftime("%Y.%m.%d.%H%M%S")
        
        migration_data = {
            "id": migration_id,
            "name": name,
            "description": description,
            "version": version,
            "sql_up": sql_up,
            "sql_down": sql_down,
            "created_at": datetime.now().isoformat()
        }
        
        # 计算校验和
        content_for_checksum = f"{sql_up}{sql_down}"
        migration_data["checksum"] = self.calculate_checksum(content_for_checksum)
        
        # 保存迁移文件
        migration_file = self.migrations_dir / f"{migration_id}.json"
        with open(migration_file, 'w', encoding='utf-8') as f:
            json.dump(migration_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 创建迁移文件: {migration_file}")
        return migration_id
    
    def load_migrations(self) -> List[Migration]:
        """加载所有迁移文件"""
        migrations = []
        
        for migration_file in sorted(self.migrations_dir.glob("migration_*.json")):
            try:
                with open(migration_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                migration = Migration(**data)
                migrations.append(migration)
                
            except Exception as e:
                print(f"⚠️ 加载迁移文件失败 {migration_file}: {e}")
        
        return migrations
    
    def get_applied_migrations(self) -> List[str]:
        """获取已应用的迁移ID列表"""
        try:
            with engine.connect() as conn:
                result = conn.execute(
                    text(f"SELECT id FROM {self.migration_table} WHERE status = 'applied' ORDER BY applied_at")
                )
                return [row[0] for row in result.fetchall()]
        except Exception as e:
            print(f"⚠️ 获取已应用迁移失败: {e}")
            return []
    
    def get_pending_migrations(self) -> List[Migration]:
        """获取待应用的迁移"""
        all_migrations = self.load_migrations()
        applied_ids = set(self.get_applied_migrations())
        
        pending = []
        for migration in all_migrations:
            if migration.id not in applied_ids:
                migration.status = "pending"
                pending.append(migration)
        
        return pending
    
    def apply_migration(self, migration: Migration) -> bool:
        """应用单个迁移"""
        print(f"🔄 应用迁移: {migration.name} ({migration.id})")
        
        try:
            with engine.connect() as conn:
                # 开始事务
                trans = conn.begin()
                
                try:
                    # 执行迁移SQL
                    if migration.sql_up.strip():
                        # 分割SQL语句（处理多个语句）
                        sql_statements = [stmt.strip() for stmt in migration.sql_up.split(';') if stmt.strip()]
                        
                        for sql in sql_statements:
                            conn.execute(text(sql))
                    
                    # 记录迁移应用
                    conn.execute(text(f"""
                        INSERT INTO {self.migration_table} 
                        (id, name, description, version, checksum, applied_at, status)
                        VALUES (:id, :name, :description, :version, :checksum, :applied_at, :status)
                    """), {
                        "id": migration.id,
                        "name": migration.name,
                        "description": migration.description,
                        "version": migration.version,
                        "checksum": migration.checksum,
                        "applied_at": datetime.now().isoformat(),
                        "status": "applied"
                    })
                    
                    # 提交事务
                    trans.commit()
                    print(f"✅ 迁移应用成功: {migration.name}")
                    return True
                    
                except Exception as e:
                    # 回滚事务
                    trans.rollback()
                    print(f"❌ 迁移应用失败: {migration.name} - {e}")
                    return False
                    
        except Exception as e:
            print(f"❌ 数据库连接失败: {e}")
            return False
    
    def rollback_migration(self, migration_id: str) -> bool:
        """回滚指定迁移"""
        migrations = self.load_migrations()
        migration = next((m for m in migrations if m.id == migration_id), None)
        
        if not migration:
            print(f"❌ 未找到迁移: {migration_id}")
            return False
        
        print(f"🔄 回滚迁移: {migration.name} ({migration.id})")
        
        try:
            with engine.connect() as conn:
                trans = conn.begin()
                
                try:
                    # 执行回滚SQL
                    if migration.sql_down.strip():
                        sql_statements = [stmt.strip() for stmt in migration.sql_down.split(';') if stmt.strip()]
                        
                        for sql in sql_statements:
                            conn.execute(text(sql))
                    
                    # 删除迁移记录
                    conn.execute(text(f"DELETE FROM {self.migration_table} WHERE id = :id"), {"id": migration_id})
                    
                    trans.commit()
                    print(f"✅ 迁移回滚成功: {migration.name}")
                    return True
                    
                except Exception as e:
                    trans.rollback()
                    print(f"❌ 迁移回滚失败: {migration.name} - {e}")
                    return False
                    
        except Exception as e:
            print(f"❌ 数据库连接失败: {e}")
            return False
    
    def migrate_up(self, target_version: Optional[str] = None) -> bool:
        """执行向上迁移（应用所有待处理的迁移）"""
        pending_migrations = self.get_pending_migrations()
        
        if not pending_migrations:
            print("✅ 没有待应用的迁移")
            return True
        
        print(f"🔄 发现 {len(pending_migrations)} 个待应用的迁移")
        
        success_count = 0
        for migration in pending_migrations:
            if target_version and migration.version > target_version:
                break
                
            if self.apply_migration(migration):
                success_count += 1
            else:
                print(f"❌ 迁移失败，停止后续迁移")
                break
        
        print(f"🎉 成功应用 {success_count}/{len(pending_migrations)} 个迁移")
        return success_count == len(pending_migrations)
    
    def get_migration_status(self) -> Dict:
        """获取迁移状态报告"""
        all_migrations = self.load_migrations()
        applied_ids = set(self.get_applied_migrations())
        
        status = {
            "total_migrations": len(all_migrations),
            "applied_count": len(applied_ids),
            "pending_count": len(all_migrations) - len(applied_ids),
            "migrations": []
        }
        
        for migration in all_migrations:
            migration_status = {
                "id": migration.id,
                "name": migration.name,
                "version": migration.version,
                "status": "applied" if migration.id in applied_ids else "pending",
                "created_at": migration.created_at
            }
            status["migrations"].append(migration_status)
        
        return status
    
    def print_status(self):
        """打印迁移状态"""
        status = self.get_migration_status()
        
        print("\n" + "="*60)
        print("📊 数据库迁移状态")
        print("="*60)
        print(f"总迁移数: {status['total_migrations']}")
        print(f"已应用: {status['applied_count']}")
        print(f"待应用: {status['pending_count']}")
        print()
        
        if status['migrations']:
            print("迁移列表:")
            for migration in status['migrations']:
                status_icon = "✅" if migration['status'] == 'applied' else "⏳"
                print(f"  {status_icon} {migration['name']} ({migration['version']})")
        
        print("="*60)


def main():
    """主函数 - 命令行接口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="数据库迁移管理工具")
    parser.add_argument("command", choices=["status", "migrate", "create", "rollback"], 
                       help="执行的命令")
    parser.add_argument("--name", help="迁移名称（用于create命令）")
    parser.add_argument("--description", help="迁移描述（用于create命令）")
    parser.add_argument("--id", help="迁移ID（用于rollback命令）")
    parser.add_argument("--version", help="目标版本（用于migrate命令）")
    
    args = parser.parse_args()
    
    manager = MigrationManager()
    
    if args.command == "status":
        manager.print_status()
    
    elif args.command == "migrate":
        manager.migrate_up(args.version)
    
    elif args.command == "create":
        if not args.name:
            print("❌ 创建迁移需要指定名称 (--name)")
            return
        
        migration_id = manager.create_migration(
            name=args.name,
            description=args.description or ""
        )
        print(f"✅ 创建迁移: {migration_id}")
    
    elif args.command == "rollback":
        if not args.id:
            print("❌ 回滚迁移需要指定ID (--id)")
            return
        
        manager.rollback_migration(args.id)


if __name__ == "__main__":
    main()