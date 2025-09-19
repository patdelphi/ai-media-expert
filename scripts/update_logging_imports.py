#!/usr/bin/env python3
"""
批量更新logging导入的脚本
将所有 from app.core.logging import 改为 from app.core.app_logging import
"""

import os
import re
from pathlib import Path

def update_logging_imports():
    """更新所有文件中的logging导入"""
    project_root = Path(__file__).parent.parent
    
    # 需要更新的文件模式
    patterns = [
        "**/*.py",
    ]
    
    # 排除的目录
    exclude_dirs = {".git", "__pycache__", ".pytest_cache", "node_modules", ".venv", "venv"}
    
    updated_files = []
    
    for pattern in patterns:
        for file_path in project_root.glob(pattern):
            # 跳过排除的目录
            if any(exclude_dir in file_path.parts for exclude_dir in exclude_dirs):
                continue
                
            # 跳过当前脚本文件
            if file_path.name == "update_logging_imports.py":
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 替换导入语句
                original_content = content
                content = re.sub(
                    r'from app\.core\.logging import',
                    'from app.core.app_logging import',
                    content
                )
                
                # 如果内容有变化，写回文件
                if content != original_content:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    updated_files.append(str(file_path.relative_to(project_root)))
                    print(f"✅ 更新: {file_path.relative_to(project_root)}")
                    
            except Exception as e:
                print(f"❌ 处理文件失败 {file_path}: {e}")
    
    print(f"\n🎉 完成! 共更新了 {len(updated_files)} 个文件")
    return updated_files

if __name__ == "__main__":
    update_logging_imports()