#!/usr/bin/env python3
"""创建测试用户脚本

用于创建一个测试用户来验证登录功能。
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.core.database import get_db
from app.models.user import User
from app.core.security import get_password_hash
from sqlalchemy.orm import Session

def create_test_user():
    """创建测试用户"""
    db = next(get_db())
    
    try:
        # 检查用户是否已存在
        existing = db.query(User).filter(User.email == 'test@example.com').first()
        
        if existing:
            print('测试用户已存在:')
            print(f'  邮箱: {existing.email}')
            print(f'  用户名: {existing.username}')
            print(f'  激活状态: {existing.is_active}')
            print(f'  验证状态: {existing.is_verified}')
            return
        
        # 创建新用户
        user = User(
            email='test@example.com',
            username='testuser',
            full_name='Test User',
            hashed_password=get_password_hash('password123'),
            is_active=True,
            is_verified=True,
            role='user'
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        print('测试用户创建成功:')
        print(f'  邮箱: {user.email}')
        print(f'  用户名: {user.username}')
        print(f'  密码: password123')
        print(f'  用户ID: {user.id}')
        
    except Exception as e:
        print(f'创建用户失败: {e}')
        db.rollback()
    finally:
        db.close()

if __name__ == '__main__':
    create_test_user()