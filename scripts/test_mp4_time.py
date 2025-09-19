#!/usr/bin/env python3
"""测试MP4文件原始创建时间获取功能

直接测试从MP4文件内容中读取原始创建时间的功能。
"""

import sys
from pathlib import Path
from datetime import datetime
import struct

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.utils.video_utils import get_video_creation_time, get_mp4_creation_time_from_content

def analyze_mp4_structure(file_path: str):
    """分析MP4文件结构"""
    print(f"\n🔍 分析MP4文件结构: {Path(file_path).name}")
    
    try:
        with open(file_path, 'rb') as f:
            print("📋 MP4 Atoms:")
            
            while True:
                pos = f.tell()
                size_data = f.read(4)
                if len(size_data) < 4:
                    break
                    
                atom_size = struct.unpack('>I', size_data)[0]
                atom_type = f.read(4)
                
                print(f"  - {atom_type.decode('ascii', errors='ignore')} (size: {atom_size}, pos: {pos})")
                
                if atom_type == b'mvhd':
                    print("    ✅ 找到Movie Header atom")
                    version = f.read(1)[0]
                    flags = f.read(3)
                    print(f"    📝 版本: {version}, 标志: {flags.hex()}")
                    
                    if version == 0:
                        creation_time = struct.unpack('>I', f.read(4))[0]
                        modification_time = struct.unpack('>I', f.read(4))[0]
                        print(f"    ⏰ 创建时间戳: {creation_time}")
                        print(f"    ⏰ 修改时间戳: {modification_time}")
                        
                        # 转换为Unix时间戳
                        unix_creation = creation_time - 2082844800
                        unix_modification = modification_time - 2082844800
                        
                        if unix_creation > 0:
                            dt_creation = datetime.fromtimestamp(unix_creation)
                            print(f"    📅 创建时间: {dt_creation.strftime('%Y年%m月%d日 %H:%M:%S')}")
                        
                        if unix_modification > 0:
                            dt_modification = datetime.fromtimestamp(unix_modification)
                            print(f"    📅 修改时间: {dt_modification.strftime('%Y年%m月%d日 %H:%M:%S')}")
                    else:
                        creation_time = struct.unpack('>Q', f.read(8))[0]
                        modification_time = struct.unpack('>Q', f.read(8))[0]
                        print(f"    ⏰ 64位创建时间戳: {creation_time}")
                        print(f"    ⏰ 64位修改时间戳: {modification_time}")
                
                # 跳到下一个atom
                if atom_size > 8:
                    f.seek(pos + atom_size)
                else:
                    break
                    
                # 限制读取前20个atoms
                if f.tell() > 10000:
                    print("  ... (限制显示前10KB内容)")
                    break
                    
    except Exception as e:
        print(f"❌ 分析MP4结构失败: {e}")

def test_mp4_creation_time():
    """测试MP4创建时间获取"""
    print("=== 测试MP4原始创建时间获取 ===")
    
    # 查找uploads目录中的视频文件
    uploads_dir = project_root / "uploads" / "videos"
    
    if not uploads_dir.exists():
        print("❌ uploads/videos 目录不存在")
        return
    
    video_files = list(uploads_dir.glob("*.mp4"))
    
    if not video_files:
        print("❌ 没有找到MP4文件")
        return
    
    print(f"✅ 找到 {len(video_files)} 个MP4文件")
    
    # 测试第一个文件
    test_file = video_files[0]
    print(f"\n🎬 测试文件: {test_file.name}")
    print(f"📁 文件路径: {test_file}")
    print(f"📊 文件大小: {test_file.stat().st_size} bytes")
    
    # 分析文件结构
    analyze_mp4_structure(str(test_file))
    
    # 测试创建时间获取函数
    print("\n🔧 测试创建时间获取函数:")
    
    try:
        # 测试直接从内容获取
        direct_time = get_mp4_creation_time_from_content(str(test_file))
        if direct_time:
            print(f"✅ 直接获取: {direct_time.strftime('%Y年%m月%d日 %H:%M:%S')}")
        else:
            print("❌ 直接获取失败")
        
        # 测试通用函数
        general_time = get_video_creation_time(str(test_file))
        if general_time:
            print(f"✅ 通用函数: {general_time.strftime('%Y年%m月%d日 %H:%M:%S')}")
        else:
            print("❌ 通用函数失败")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_mp4_creation_time()