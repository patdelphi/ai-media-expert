#!/usr/bin/env python3
"""测试从文件名提取时间的功能

测试各种常见的文件名时间格式。
"""

import sys
from pathlib import Path
from datetime import datetime
import re

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def extract_time_from_filename(filename: str):
    """从文件名中提取时间信息"""
    # 常见的时间格式模式
    patterns = [
        # 20231225_143022 格式
        r'(\d{8})_(\d{6})',
        # 2023-12-25_14-30-22 格式
        r'(\d{4}-\d{2}-\d{2})_(\d{2}-\d{2}-\d{2})',
        # 20231225143022 格式
        r'(\d{14})',
        # IMG_20231225_143022 格式
        r'IMG_(\d{8})_(\d{6})',
        # VID_20231225_143022 格式
        r'VID_(\d{8})_(\d{6})'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, filename)
        if match:
            try:
                if len(match.groups()) == 2:
                    date_part, time_part = match.groups()
                    if '-' in date_part:
                        # 2023-12-25_14-30-22 格式
                        datetime_str = f"{date_part} {time_part.replace('-', ':')}"
                        return datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
                    else:
                        # 20231225_143022 格式
                        datetime_str = f"{date_part}{time_part}"
                        return datetime.strptime(datetime_str, "%Y%m%d%H%M%S")
                elif len(match.groups()) == 1:
                    # 20231225143022 格式
                    datetime_str = match.group(1)
                    return datetime.strptime(datetime_str, "%Y%m%d%H%M%S")
            except ValueError:
                continue
    
    return None

def test_filename_time_extraction():
    """测试文件名时间提取功能"""
    print("=== 测试文件名时间提取功能 ===")
    
    # 测试用例
    test_cases = [
        "20250821_140907.mp4",
        "VID_20250821_140907.mp4",
        "IMG_20250821_140907.jpg",
        "2025-08-21_14-09-07.mp4",
        "20250821140907.mp4",
        "video_20250821_140907_edited.mp4",
        "normal_video.mp4",  # 应该提取失败
        "61c1e37c9e7570491934d7db6cb0d504.mp4",  # 应该提取失败
        "recording_20250821_140907.mp4"
    ]
    
    for filename in test_cases:
        print(f"\n📁 测试文件名: {filename}")
        
        extracted_time = extract_time_from_filename(filename)
        
        if extracted_time:
            print(f"✅ 提取成功: {extracted_time.strftime('%Y年%m月%d日 %H:%M:%S')}")
        else:
            print("❌ 提取失败（文件名不包含时间信息）")
    
    print("\n" + "="*60)
    print("🎯 特别测试：用户提到的文件名")
    
    # 用户提到的具体文件
    user_filename = "61c1e37c9e7570491934d7db6cb0d504.mp4"
    print(f"📁 文件名: {user_filename}")
    print(f"📅 期望时间: 2025年8月21日 14:09:07")
    
    extracted = extract_time_from_filename(user_filename)
    if extracted:
        print(f"✅ 提取结果: {extracted.strftime('%Y年%m月%d日 %H:%M:%S')}")
    else:
        print("❌ 无法从此文件名提取时间")
        print("💡 建议：如果需要指定创建时间，可以重命名文件为包含时间的格式")
        print("   例如: VID_20250821_140907.mp4")

if __name__ == "__main__":
    test_filename_time_extraction()