"""视频工具函数

提供视频文件处理相关的工具函数，包括获取视频完整信息等功能。
使用moviepy库替代ffmpeg获取视频信息。
"""

import json
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
try:
    from moviepy import VideoFileClip
except ImportError:
    try:
        from moviepy.editor import VideoFileClip
    except ImportError:
        VideoFileClip = None

try:
    import exifread
except ImportError:
    exifread = None

try:
    from pymediainfo import MediaInfo
except ImportError:
    MediaInfo = None


def get_video_duration(video_path: str) -> Optional[float]:
    """获取视频文件的时长（秒）- 保持向后兼容
    
    Args:
        video_path: 视频文件路径
        
    Returns:
        视频时长（秒），如果获取失败返回None
    """
    info = get_complete_video_info(video_path)
    return info.get('duration') if info else None


def get_complete_video_info(video_path: str) -> Optional[Dict[str, Any]]:
    """获取视频文件的完整信息
    
    Args:
        video_path: 视频文件路径
        
    Returns:
        包含完整视频信息的字典，如果获取失败返回None
    """
    if VideoFileClip is None:
        print("MoviePy库未安装，无法获取视频信息")
        return None
        
    try:
        # 检查文件是否存在
        if not Path(video_path).exists():
            print(f"文件不存在: {video_path}")
            return None
            
        # 使用moviepy获取视频信息
        with VideoFileClip(video_path) as clip:
            # 获取基本信息
            duration = clip.duration
            fps = clip.fps
            size = clip.size  # (width, height)
            
            # 获取文件大小
            file_size = Path(video_path).stat().st_size
            
            # 构建信息字典
            info = {
                # 基本文件信息
                'duration': duration,
                'format_name': Path(video_path).suffix.lower().replace('.', ''),
                'format_long_name': f"{Path(video_path).suffix.upper()} Video",
                
                # 视频流信息
                'width': size[0] if size else None,
                'height': size[1] if size else None,
                'frame_rate': f"{fps:.2f}" if fps else None,
                
                # 计算比特率 (文件大小 * 8 / 时长)
                'bit_rate': int((file_size * 8) / duration) if duration > 0 else None,
                
                # 音频信息（如果有音频轨道）
                'audio_codec': 'unknown' if clip.audio else None,
                'channels': 2 if clip.audio else None,  # 默认立体声
                'sample_rate': 44100 if clip.audio else None,  # 默认采样率
            }
            
            # 添加宽高比和标准比例
            if size and size[0] and size[1]:
                width, height = size[0], size[1]
                aspect_ratio = width / height
                info['aspect_ratio'] = f"{aspect_ratio:.2f}:1"
                
                # 计算标准比例（如9:16, 16:9等）
                def gcd(a, b):
                    while b:
                        a, b = b, a % b
                    return a
                
                # 简化比例
                common_divisor = gcd(width, height)
                simplified_width = width // common_divisor
                simplified_height = height // common_divisor
                
                # 如果比例过大，尝试找到最接近的标准比例
                if simplified_width > 50 or simplified_height > 50:
                    # 常见的视频比例
                    standard_ratios = [
                        (16, 9), (9, 16), (4, 3), (3, 4), (1, 1),
                        (21, 9), (9, 21), (5, 4), (4, 5)
                    ]
                    
                    current_ratio = width / height
                    best_match = None
                    min_diff = float('inf')
                    
                    for w, h in standard_ratios:
                        ratio = w / h
                        diff = abs(current_ratio - ratio)
                        if diff < min_diff:
                            min_diff = diff
                            best_match = (w, h)
                    
                    if best_match and min_diff < 0.1:  # 允许10%的误差
                        simplified_width, simplified_height = best_match
                
                info['video_ratio'] = f"{simplified_width}:{simplified_height}"
            
            return info
        
    except Exception as e:
        print(f"获取视频信息失败: {e}")
        return None


def safe_int(value) -> Optional[int]:
    """安全转换为整数"""
    if value is None:
        return None
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return None


def safe_float(value) -> Optional[float]:
    """安全转换为浮点数"""
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def parse_mp4_atoms(f, end_pos=None) -> Optional[datetime]:
    """递归解析MP4 atoms查找mvhd"""
    import struct
    
    while f.tell() < (end_pos or float('inf')):
        try:
            pos = f.tell()
            size_data = f.read(4)
            if len(size_data) < 4:
                break
                
            atom_size = struct.unpack('>I', size_data)[0]
            atom_type = f.read(4)
            
            if atom_size < 8:
                break
                
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
                unix_timestamp = creation_time - 2082844800
                
                if unix_timestamp > 0:
                    return datetime.fromtimestamp(unix_timestamp)
                    
            elif atom_type in [b'moov', b'trak', b'mdia']:
                # 这些是容器atom，需要递归解析
                result = parse_mp4_atoms(f, pos + atom_size)
                if result:
                    return result
            else:
                # 跳过其他atom
                f.seek(pos + atom_size)
                
        except (struct.error, OSError):
            break
            
    return None

def get_mp4_creation_time_from_content(file_path: str) -> Optional[datetime]:
    """从MP4文件内容中获取原始创建时间"""
    try:
        with open(file_path, 'rb') as f:
            return parse_mp4_atoms(f)
    except Exception as e:
        print(f"解析MP4文件失败: {e}")
    
    return None

def get_video_creation_time(video_path: str) -> Optional[datetime]:
    """获取视频文件的创建时间
    
    Args:
        video_path: 视频文件路径
        
    Returns:
        视频创建时间，如果获取失败返回None
    """
    # 首先尝试从文件内容中获取原始创建时间
    if video_path.lower().endswith('.mp4'):
        original_time = get_mp4_creation_time_from_content(video_path)
        if original_time:
            print(f"从MP4内容获取到原始创建时间: {original_time}")
            return original_time
    
    # 尝试使用pymediainfo获取视频元数据
    if MediaInfo:
        try:
            media_info = MediaInfo.parse(video_path)
            
            # 查找视频轨道
            for track in media_info.tracks:
                if track.track_type == 'Video':
                    # 尝试获取各种可能的创建时间字段
                    creation_fields = [
                        'encoded_date',
                        'tagged_date', 
                        'file_last_modification_date',
                        'mastered_date'
                    ]
                    
                    for field in creation_fields:
                        if hasattr(track, field):
                            time_value = getattr(track, field)
                            if time_value:
                                try:
                                    # 解析UTC时间格式
                                    if 'UTC' in str(time_value):
                                        time_str = str(time_value).replace(' UTC', '')
                                        return datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
                                    else:
                                        # 尝试其他常见格式
                                        time_str = str(time_value)
                                        for fmt in ['%Y-%m-%d %H:%M:%S', '%Y:%m:%d %H:%M:%S']:
                                            try:
                                                return datetime.strptime(time_str, fmt)
                                            except ValueError:
                                                continue
                                except (ValueError, AttributeError):
                                    continue
                                    
        except Exception as e:
            print(f"读取视频元数据失败: {e}")
    
    # 如果pymediainfo失败，尝试EXIF（主要用于图片格式）
    if exifread:
        try:
            with open(video_path, 'rb') as f:
                tags = exifread.process_file(f)
                
                creation_tags = [
                    'EXIF DateTimeOriginal',
                    'EXIF DateTime', 
                    'Image DateTime',
                    'EXIF DateTimeDigitized'
                ]
                
                for tag_name in creation_tags:
                    if tag_name in tags:
                        time_str = str(tags[tag_name])
                        try:
                            return datetime.strptime(time_str, '%Y:%m:%d %H:%M:%S')
                        except ValueError:
                            continue
                            
        except Exception as e:
            print(f"读取EXIF数据失败: {e}")
        
    return None

def parse_creation_time(time_str: str) -> Optional[datetime]:
    """解析创建时间字符串"""
    if not time_str:
        return None
    try:
        # 尝试解析ISO格式时间
        return datetime.fromisoformat(time_str.replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        return None


def format_duration(seconds: Optional[float]) -> str:
    """格式化时长显示
    
    Args:
        seconds: 时长（秒）
        
    Returns:
        格式化的时长字符串，如 "1:23" 或 "12:34"
    """
    if seconds is None:
        return "--:--"
        
    try:
        total_seconds = int(seconds)
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes}:{seconds:02d}"
    except (ValueError, TypeError):
        return "--:--"