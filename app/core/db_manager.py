#!/usr/bin/env python3
"""数据库自动配置管理器

提供数据库自动检测、初始化、迁移等功能，确保应用启动时数据库环境正确配置。
"""

import os
import sys
import sqlite3
import time
from pathlib import Path
from typing import Optional, Dict, Any
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import OperationalError, SQLAlchemyError
import logging

from app.core.config import settings
from app.core.database import Base, engine

logger = logging.getLogger(__name__)


class DatabaseManager:
    """数据库管理器 - 负责数据库的自动配置和管理"""
    
    def __init__(self):
        self.settings = settings
        self.engine = engine
        self.db_path = None
        
        # 如果是SQLite，获取数据库文件路径
        if self.settings.database_url.startswith("sqlite"):
            self.db_path = self._extract_sqlite_path()
    
    def _extract_sqlite_path(self) -> Optional[Path]:
        """从DATABASE_URL中提取SQLite数据库文件路径"""
        try:
            # 格式: sqlite:///./ai_media_expert.db
            url_path = self.settings.database_url.replace("sqlite:///", "")
            return Path(url_path).resolve()
        except Exception as e:
            logger.error(f"无法解析SQLite数据库路径: {e}")
            return None
    
    def check_database_exists(self) -> bool:
        """检查数据库是否存在"""
        try:
            if self.settings.database_url.startswith("sqlite"):
                return self.db_path and self.db_path.exists()
            else:
                # PostgreSQL等其他数据库，尝试连接
                with self.engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                return True
        except Exception as e:
            logger.debug(f"数据库连接检查失败: {e}")
            return False
    
    def check_tables_exist(self) -> Dict[str, bool]:
        """检查必要的表是否存在"""
        required_tables = [
            'users', 'user_sessions', 'system_configs', 
            'videos', 'video_analyses', 'ai_configs'
        ]
        
        table_status = {}
        
        try:
            inspector = inspect(self.engine)
            existing_tables = inspector.get_table_names()
            
            for table in required_tables:
                table_status[table] = table in existing_tables
                
        except Exception as e:
            logger.error(f"检查表结构失败: {e}")
            # 如果检查失败，假设所有表都不存在
            table_status = {table: False for table in required_tables}
        
        return table_status
    
    def create_database_file(self) -> bool:
        """创建SQLite数据库文件"""
        if not self.settings.database_url.startswith("sqlite"):
            return True  # 非SQLite数据库不需要创建文件
        
        try:
            if self.db_path:
                # 确保父目录存在
                self.db_path.parent.mkdir(parents=True, exist_ok=True)
                
                # 创建空的SQLite数据库文件
                conn = sqlite3.connect(str(self.db_path))
                conn.close()
                
                logger.info(f"已创建SQLite数据库文件: {self.db_path}")
                return True
        except Exception as e:
            logger.error(f"创建SQLite数据库文件失败: {e}")
            return False
        
        return False
    
    def create_tables(self) -> bool:
        """创建数据库表结构"""
        try:
            # 导入所有模型以确保它们被注册
            from app.models import user, video, system_config  # noqa: F401
            
            # 创建所有表
            Base.metadata.create_all(bind=self.engine)
            logger.info("数据库表结构创建成功")
            return True
            
        except Exception as e:
            logger.error(f"创建数据库表结构失败: {e}")
            return False
    
    def initialize_default_data(self) -> bool:
        """初始化默认数据"""
        try:
            from sqlalchemy.orm import sessionmaker
            from sqlalchemy import or_
            from app.models.user import User
            from app.models.system_config import SystemConfig
            from app.core.security import get_password_hash
            
            SessionLocal = sessionmaker(bind=self.engine)
            db = SessionLocal()
            
            try:
                # 检查是否已有管理员用户
                admin_exists = db.query(User).filter(
                    or_(User.email == "admin@example.com", User.username == "admin")
                ).first()
                if not admin_exists:
                    # 创建默认管理员用户
                    admin_user = User(
                        email="admin@example.com",
                        username="admin",
                        full_name="系统管理员",
                        hashed_password=get_password_hash("admin123"),
                        is_active=True,
                        is_superuser=True,
                        is_verified=True,
                        role="admin"
                    )
                    db.add(admin_user)
                    logger.info("已创建默认管理员用户")
                
                # 创建默认系统配置
                default_configs = [
                    {
                        "key": "system.name",
                        "value": "AI新媒体专家系统",
                        "description": "系统名称",
                        "category": "system",
                        "data_type": "string"
                    },
                    {
                        "key": "system.version",
                        "value": "0.1.0",
                        "description": "系统版本",
                        "category": "system",
                        "data_type": "string"
                    },
                    {
                        "key": "upload.max_file_size",
                        "value": "1073741824",
                        "description": "最大上传文件大小（字节）",
                        "category": "upload",
                        "data_type": "integer"
                    }
                ]
                
                for config_data in default_configs:
                    existing = db.query(SystemConfig).filter(
                        SystemConfig.key == config_data["key"]
                    ).first()
                    if not existing:
                        config = SystemConfig(**config_data)
                        db.add(config)
                
                db.commit()
                logger.info("默认数据初始化完成")
                return True
                
            except Exception as e:
                db.rollback()
                logger.error(f"初始化默认数据失败: {e}")
                return False
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"初始化默认数据过程失败: {e}")
            return False
    
    def auto_setup(self) -> bool:
        """自动设置数据库环境"""
        logger.info("开始数据库自动配置...")
        
        # 1. 检查数据库是否存在
        if not self.check_database_exists():
            logger.info("数据库不存在，开始创建...")
            if not self.create_database_file():
                logger.error("创建数据库文件失败")
                return False
        
        # 2. 检查表结构
        table_status = self.check_tables_exist()
        missing_tables = [table for table, exists in table_status.items() if not exists]
        
        if missing_tables:
            logger.info(f"发现缺失的表: {missing_tables}")
            if not self.create_tables():
                logger.error("创建数据库表结构失败")
                return False
        
        # 3. 初始化默认数据
        if not self.initialize_default_data():
            logger.error("初始化默认数据失败")
            return False
        
        logger.info("数据库自动配置完成")
        return True
    
    def get_database_info(self) -> Dict[str, Any]:
        """获取数据库信息"""
        info = {
            "database_type": "sqlite" if self.settings.database_url.startswith("sqlite") else "postgresql",
            "database_url": self.settings.database_url,
            "database_exists": self.check_database_exists(),
            "tables": self.check_tables_exist()
        }
        
        if self.db_path:
            info["database_file"] = str(self.db_path)
            info["file_size"] = self.db_path.stat().st_size if self.db_path.exists() else 0
        
        return info
    
    def backup_database(self, backup_path: Optional[Path] = None) -> bool:
        """备份数据库（仅SQLite）"""
        if not self.settings.database_url.startswith("sqlite") or not self.db_path:
            logger.warning("仅支持SQLite数据库备份")
            return False
        
        try:
            if not backup_path:
                backup_path = self.db_path.parent / f"{self.db_path.stem}_backup_{int(time.time())}.db"
            
            import shutil
            shutil.copy2(self.db_path, backup_path)
            logger.info(f"数据库备份完成: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"数据库备份失败: {e}")
            return False


# 创建全局数据库管理器实例
db_manager = DatabaseManager()


def ensure_database_ready() -> bool:
    """确保数据库环境就绪 - 应用启动时调用"""
    try:
        return db_manager.auto_setup()
    except Exception as e:
        logger.error(f"数据库环境检查失败: {e}")
        return False


def get_database_status() -> Dict[str, Any]:
    """获取数据库状态信息"""
    return db_manager.get_database_info()