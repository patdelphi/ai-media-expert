#!/usr/bin/env python3
"""测试视频信息获取功能

测试get_complete_video_info函数是否能正确获取视频信息。
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.utils.video_utils import get_complete_video_info

def test_video_info():
    """测试视频信息获取"""
    print("=== 测试视频信息获取功能 ===")
    
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
    
    # 测试第一个视频文件
    test_file = video_files[0]
    print(f"\n🎬 测试文件: {test_file.name}")
    print(f"📁 文件路径: {test_file}")
    print(f"📊 文件大小: {test_file.stat().st_size} bytes")
    
    try:
        print("\n🔍 开始获取视频信息...")
        video_info = get_complete_video_info(str(test_file))
        
        if video_info:
            print("✅ 成功获取视频信息:")
            print(f"  时长: {video_info.get('duration')} 秒")
            print(f"  分辨率: {video_info.get('width')}×{video_info.get('height')}")
            print(f"  视频编码: {video_info.get('video_codec')}")
            print(f"  音频编码: {video_info.get('audio_codec')}")
            print(f"  比特率: {video_info.get('bit_rate')}")
            print(f"  帧率: {video_info.get('frame_rate')}")
            print(f"  格式: {video_info.get('format_name')}")
            
            # 显示所有字段
            print("\n📋 完整信息:")
            for key, value in video_info.items():
                if value is not None:
                    print(f"  {key}: {value}")
        else:
            print("❌ 获取视频信息失败")
            
    except Exception as e:
        print(f"❌ 获取视频信息时发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_video_info()