#!/usr/bin/env python3
"""测试EXIF创建时间获取功能

测试get_video_creation_time函数是否能正确获取视频文件的EXIF创建时间。
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.utils.video_utils import get_video_creation_time

def test_exif_creation_time():
    """测试EXIF创建时间获取"""
    print("=== 测试EXIF创建时间获取功能 ===")
    
    # 查找uploads目录中的视频文件
    uploads_dir = project_root / "uploads" / "videos"
    
    if not uploads_dir.exists():
        print("❌ uploads/videos 目录不存在")
        return
    
    video_files = list(uploads_dir.glob("*.mp4"))
    
    if not video_files:
        print("❌ 没有找到视频文件")
        return
    
    print(f"✅ 找到 {len(video_files)} 个视频文件")
    
    # 测试每个视频文件的EXIF创建时间
    for i, test_file in enumerate(video_files[:3], 1):  # 只测试前3个文件
        print(f"\n🎬 测试文件 #{i}: {test_file.name}")
        print(f"📁 文件路径: {test_file}")
        print(f"📊 文件大小: {test_file.stat().st_size} bytes")
        
        try:
            print("\n🔍 开始获取视频创建时间...")
            creation_time = get_video_creation_time(str(test_file))
            
            if creation_time:
                print(f"✅ 成功获取视频创建时间: {creation_time}")
                print(f"📅 格式化时间: {creation_time.strftime('%Y年%m月%d日 %H:%M:%S')}")
            else:
                print("❌ 未能获取视频元数据创建时间")
                
            # 总是显示文件系统时间作为对比
            import os
            from datetime import datetime
            file_stat = os.stat(test_file)
            fs_time = datetime.fromtimestamp(file_stat.st_ctime)
            print(f"📁 文件系统创建时间: {fs_time.strftime('%Y年%m月%d日 %H:%M:%S')}")
            
            # 显示文件修改时间
            mod_time = datetime.fromtimestamp(file_stat.st_mtime)
            print(f"📝 文件修改时间: {mod_time.strftime('%Y年%m月%d日 %H:%M:%S')}")
                
        except Exception as e:
            print(f"❌ 获取EXIF创建时间时发生错误: {e}")
            import traceback
            traceback.print_exc()
        
        print("-" * 60)

if __name__ == "__main__":
    test_exif_creation_time()