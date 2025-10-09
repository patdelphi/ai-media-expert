#!/usr/bin/env python3
"""创建uploaded_files表的数据库迁移脚本

运行此脚本来创建存储上传文件元数据的表。
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
from app.models.uploaded_file import UploadedFile

def create_tables():
    """创建数据库表"""
    try:
        # 创建数据库引擎
        engine = create_engine(settings.database_url)
        
        # 创建所有表
        Base.metadata.create_all(bind=engine)
        
        print("✅ uploaded_files表创建成功！")
        
    except Exception as e:
        print(f"❌ 创建表失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("🚀 开始创建uploaded_files表...")
    create_tables()
    print("🎉 数据库迁移完成！")