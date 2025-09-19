#!/usr/bin/env python3
"""获取文件原始创建时间的工具脚本

尝试从文件内容中读取原始创建时间，而不是依赖文件系统时间。
支持多种方法获取原始时间戳。
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import struct

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def get_file_original_time_from_content(file_path: str) -> datetime:
    """从文件内容中获取原始创建时间
    
    Args:
        file_path: 文件路径
        
    Returns:
        原始创建时间
    """
    try:
        with open(file_path, 'rb') as f:
            # 读取文件头部信息
            header = f.read(1024)  # 读取前1KB
            
            # 检查是否是MP4文件
            if b'ftyp' in header[:20]:
                return get_mp4_creation_time(file_path)
            
            # 检查是否是AVI文件
            if header.startswith(b'RIFF') and b'AVI ' in header[:20]:
                return get_avi_creation_time(file_path)
                
            # 其他格式的处理
            print(f"未识别的文件格式: {file_path}")
            
    except Exception as e:
        print(f"读取文件失败: {e}")
    
    # 如果无法从内容获取，返回文件系统时间
    stat = os.stat(file_path)
    return datetime.fromtimestamp(stat.st_mtime)

def get_mp4_creation_time(file_path: str) -> datetime:
    """从MP4文件中获取创建时间"""
    try:
        with open(file_path, 'rb') as f:
            # 查找mvhd atom（Movie Header）
            while True:
                # 读取atom大小和类型
                size_data = f.read(4)
                if len(size_data) < 4:
                    break
                    
                atom_size = struct.unpack('>I', size_data)[0]
                atom_type = f.read(4)
                
                if atom_type == b'mvhd':
                    # 找到Movie Header atom
                    version = f.read(1)[0]
                    f.read(3)  # flags
                    
                    if version == 0:
                        # 32位时间戳
                        creation_time = struct.unpack('>I', f.read(4))[0]
                    else:
                        # 64位时间戳
                        creation_time = struct.unpack('>Q', f.read(8))[0]
                    
                    # MP4时间戳从1904年1月1日开始计算
                    # 需要减去1904到1970的秒数：2082844800
                    unix_timestamp = creation_time - 2082844800
                    
                    if unix_timestamp > 0:
                        return datetime.fromtimestamp(unix_timestamp)
                    break
                    
                # 跳到下一个atom
                if atom_size > 8:
                    f.seek(f.tell() + atom_size - 8)
                else:
                    break
                    
    except Exception as e:
        print(f"解析MP4文件失败: {e}")
    
    # 如果解析失败，返回文件系统时间
    stat = os.stat(file_path)
    return datetime.fromtimestamp(stat.st_mtime)

def get_avi_creation_time(file_path: str) -> datetime:
    """从AVI文件中获取创建时间"""
    try:
        with open(file_path, 'rb') as f:
            # AVI文件结构比较复杂，这里简化处理
            # 通常创建时间信息在文件头部的某个位置
            f.seek(0)
            data = f.read(2048)  # 读取前2KB
            
            # 查找可能的时间戳模式
            # 这里需要根据具体的AVI文件格式来解析
            # 暂时返回文件系统时间
            pass
            
    except Exception as e:
        print(f"解析AVI文件失败: {e}")
    
    # 如果解析失败，返回文件系统时间
    stat = os.stat(file_path)
    return datetime.fromtimestamp(stat.st_mtime)

def test_original_time_extraction():
    """测试原始时间提取功能"""
    print("=== 测试文件原始创建时间提取 ===")
    
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
    
    # 测试每个视频文件
    for i, test_file in enumerate(video_files[:3], 1):
        print(f"\n🎬 测试文件 #{i}: {test_file.name}")
        print(f"📁 文件路径: {test_file}")
        print(f"📊 文件大小: {test_file.stat().st_size} bytes")
        
        try:
            # 获取原始创建时间
            original_time = get_file_original_time_from_content(str(test_file))
            print(f"✅ 原始创建时间: {original_time.strftime('%Y年%m月%d日 %H:%M:%S')}")
            
            # 对比文件系统时间
            stat = os.stat(test_file)
            fs_ctime = datetime.fromtimestamp(stat.st_ctime)
            fs_mtime = datetime.fromtimestamp(stat.st_mtime)
            
            print(f"📁 文件系统创建时间: {fs_ctime.strftime('%Y年%m月%d日 %H:%M:%S')}")
            print(f"📝 文件系统修改时间: {fs_mtime.strftime('%Y年%m月%d日 %H:%M:%S')}")
            
            # 计算时间差
            if original_time != fs_mtime:
                diff = abs((original_time - fs_mtime).total_seconds())
                print(f"⏰ 时间差: {diff:.0f} 秒")
            else:
                print("⚠️ 原始时间与文件系统时间相同")
                
        except Exception as e:
            print(f"❌ 获取原始创建时间失败: {e}")
        
        print("-" * 60)

if __name__ == "__main__":
    test_original_time_extraction()