#!/usr/bin/env python3
"""创建演示用户脚本

为WebSocket连接测试创建一个演示用户。
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.core.database import get_db
from app.models.user import User
from app.core.security import get_password_hash

def create_demo_user():
    """创建演示用户"""
    db = next(get_db())
    
    try:
        # 检查用户是否已存在
        existing = db.query(User).filter(User.id == 'demo_user_123').first()
        
        if existing:
            print('演示用户已存在')
            print(f'  ID: {existing.id}')
            print(f'  用户名: {existing.username}')
            print(f'  邮箱: {existing.email}')
            return
        
        # 创建新用户
        user = User(
            id='demo_user_123',
            email='demo@example.com',
            username='demo_user',
            full_name='演示用户',
            hashed_password=get_password_hash('demo123'),
            is_active=True,
            is_verified=True
        )
        
        db.add(user)
        db.commit()
        
        print('演示用户创建成功！')
        print(f'  ID: {user.id}')
        print(f'  用户名: {user.username}')
        print(f'  邮箱: {user.email}')
        print(f'  密码: demo123')
        
    except Exception as e:
        print(f'创建用户失败: {str(e)}')
        db.rollback()
    finally:
        db.close()

if __name__ == '__main__':
    create_demo_user()