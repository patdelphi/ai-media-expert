#!/usr/bin/env python3
"""数据库初始化脚本

创建数据库表和初始数据。
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine
from app.core.config import settings
from app.core.database import Base
from app.models.user import User, UserSession
from app.models.system_config import SystemConfig
from app.models.video import AIConfig
from app.core.security import get_password_hash

def create_tables():
    """创建数据库表"""
    print("Creating database tables...")
    
    # 创建数据库引擎
    engine = create_engine(settings.database_url)
    
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    
    print("Database tables created successfully!")
    return engine

def create_admin_user(engine):
    """创建管理员用户"""
    print("Creating admin user...")
    
    from sqlalchemy.orm import sessionmaker
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = SessionLocal()
    try:
        # 检查是否已存在管理员用户
        existing_admin = db.query(User).filter(User.email == "admin@example.com").first()
        if existing_admin:
            print("Admin user already exists.")
            return
        
        # 创建管理员用户
        admin_user = User(
            email="admin@example.com",
            username="admin",
            full_name="System Administrator",
            hashed_password=get_password_hash("admin123"),
            is_active=True,
            is_verified=True,
            is_superuser=True,
            role="admin"
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        print(f"Admin user created successfully! ID: {admin_user.id}")
        print("Login credentials:")
        print("  Email: admin@example.com")
        print("  Password: admin123")
        
    except Exception as e:
        print(f"Error creating admin user: {e}")
        db.rollback()
    finally:
        db.close()

def create_default_configs(engine):
    """创建默认系统配置"""
    print("Creating default system configurations...")
    
    from sqlalchemy.orm import sessionmaker
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = SessionLocal()
    try:
        # 默认配置列表
        default_configs = [
            {
                "key": "system.app_name",
                "value": "AI媒体专家系统",
                "description": "应用程序名称",
                "category": "system",
                "is_public": True,
                "data_type": "string"
            },
            {
                "key": "system.app_version",
                "value": "1.0.0",
                "description": "应用程序版本",
                "category": "system",
                "is_public": True,
                "data_type": "string"
            },
            {
                "key": "system.max_upload_size",
                "value": "1073741824",  # 1GB
                "description": "最大上传文件大小（字节）",
                "category": "system",
                "is_public": False,
                "data_type": "integer"
            },
            {
                "key": "ai.default_model",
                "value": "gpt-3.5-turbo",
                "description": "默认AI模型",
                "category": "ai",
                "is_public": False,
                "data_type": "string"
            },
            {
                "key": "ai.max_tokens",
                "value": "4096",
                "description": "AI模型最大token数",
                "category": "ai",
                "is_public": False,
                "data_type": "integer"
            },
            {
                "key": "download.concurrent_limit",
                "value": "3",
                "description": "并发下载任务限制",
                "category": "download",
                "is_public": False,
                "data_type": "integer"
            },
            {
                "key": "download.timeout",
                "value": "300",
                "description": "下载超时时间（秒）",
                "category": "download",
                "is_public": False,
                "data_type": "integer"
            },
            {
                "key": "ui.theme",
                "value": "light",
                "description": "默认UI主题",
                "category": "ui",
                "is_public": True,
                "data_type": "string"
            },
            {
                "key": "ui.language",
                "value": "zh-CN",
                "description": "默认语言",
                "category": "ui",
                "is_public": True,
                "data_type": "string"
            }
        ]
        
        # 创建配置
        created_count = 0
        for config_data in default_configs:
            # 检查配置是否已存在
            existing = db.query(SystemConfig).filter(SystemConfig.key == config_data["key"]).first()
            if existing:
                continue
            
            config = SystemConfig(**config_data)
            db.add(config)
            created_count += 1
        
        db.commit()
        print(f"Created {created_count} default configurations.")
        
    except Exception as e:
        print(f"Error creating default configurations: {e}")
        db.rollback()
    finally:
        db.close()

def main():
    """主函数"""
    print("Initializing database...")
    print(f"Database URL: {settings.database_url}")
    
    try:
        # 创建数据库表
        engine = create_tables()
        
        # 创建管理员用户
        create_admin_user(engine)
        
        # 创建默认配置
        create_default_configs(engine)
        
        print("\nDatabase initialization completed successfully!")
        print("\nYou can now:")
        print("1. Start the backend server: python -m uvicorn app.app:app --reload")
        print("2. Access the frontend at: http://localhost:3000")
        print("3. Login with admin@example.com / admin123")
        
    except Exception as e:
        print(f"Database initialization failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()