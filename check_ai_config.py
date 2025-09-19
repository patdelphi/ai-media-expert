#!/usr/bin/env python3
"""
检查AI配置的脚本
"""

from app.core.database import SessionLocal
from app.models.video import AIConfig

def check_ai_configs():
    db = SessionLocal()
    try:
        configs = db.query(AIConfig).all()
        print(f'AI配置数量: {len(configs)}')
        
        for config in configs:
            api_key_status = "已设置" if config.api_key else "未设置"
            print(f'- {config.name}: {config.provider}/{config.model}')
            print(f'  API Key: {api_key_status}')
            print(f'  API Base: {config.api_base or "默认"}')
            print(f'  激活状态: {"是" if config.is_active else "否"}')
            print()
            
    finally:
        db.close()

if __name__ == "__main__":
    check_ai_configs()