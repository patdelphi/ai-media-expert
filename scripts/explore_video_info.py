#!/usr/bin/env python3
"""视频信息探查脚本

使用ffprobe探查视频文件的所有可用信息，帮助用户选择需要存储的字段。
"""

import subprocess
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional

def get_video_info(video_path: str) -> Optional[Dict[str, Any]]:
    """获取视频文件的完整信息
    
    Args:
        video_path: 视频文件路径
        
    Returns:
        视频信息字典，如果获取失败返回None
    """
    try:
        # 检查文件是否存在
        if not Path(video_path).exists():
            print(f"文件不存在: {video_path}")
            return None
            
        # 使用ffprobe获取详细信息
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            '-show_chapters',
            '-show_programs',
            str(video_path)
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            print(f"ffprobe执行失败: {result.stderr}")
            return None
            
        return json.loads(result.stdout)
        
    except Exception as e:
        print(f"获取视频信息失败: {e}")
        return None

def analyze_video_streams(streams: list) -> Dict[str, Any]:
    """分析视频流信息"""
    video_streams = [s for s in streams if s.get('codec_type') == 'video']
    audio_streams = [s for s in streams if s.get('codec_type') == 'audio']
    
    analysis = {
        'video_streams_count': len(video_streams),
        'audio_streams_count': len(audio_streams),
        'total_streams': len(streams)
    }
    
    if video_streams:
        video = video_streams[0]  # 主视频流
        analysis.update({
            'video_codec': video.get('codec_name'),
            'video_codec_long': video.get('codec_long_name'),
            'width': video.get('width'),
            'height': video.get('height'),
            'aspect_ratio': video.get('display_aspect_ratio'),
            'pixel_format': video.get('pix_fmt'),
            'frame_rate': video.get('r_frame_rate'),
            'avg_frame_rate': video.get('avg_frame_rate'),
            'bit_rate': video.get('bit_rate'),
            'duration': video.get('duration'),
            'nb_frames': video.get('nb_frames')
        })
    
    if audio_streams:
        audio = audio_streams[0]  # 主音频流
        analysis.update({
            'audio_codec': audio.get('codec_name'),
            'audio_codec_long': audio.get('codec_long_name'),
            'sample_rate': audio.get('sample_rate'),
            'channels': audio.get('channels'),
            'channel_layout': audio.get('channel_layout'),
            'audio_bit_rate': audio.get('bit_rate')
        })
    
    return analysis

def print_available_fields(info: Dict[str, Any]):
    """打印所有可用的字段信息"""
    print("\n=== 可用的视频信息字段 ===")
    
    # 格式信息
    if 'format' in info:
        print("\n📁 文件格式信息:")
        format_info = info['format']
        for key, value in format_info.items():
            if isinstance(value, (str, int, float)):
                print(f"  {key}: {value}")
    
    # 流信息分析
    if 'streams' in info:
        print("\n🎬 视频流信息:")
        analysis = analyze_video_streams(info['streams'])
        for key, value in analysis.items():
            if value is not None:
                print(f"  {key}: {value}")
        
        print("\n📊 详细流信息:")
        for i, stream in enumerate(info['streams']):
            print(f"\n  流 #{i} ({stream.get('codec_type', 'unknown')})：")
            for key, value in stream.items():
                if isinstance(value, (str, int, float)) and key not in ['disposition', 'tags']:
                    print(f"    {key}: {value}")
    
    # 章节信息
    if 'chapters' in info and info['chapters']:
        print("\n📖 章节信息:")
        for i, chapter in enumerate(info['chapters']):
            print(f"  章节 #{i}: {chapter}")

def suggest_useful_fields():
    """建议有用的字段"""
    print("\n\n🎯 建议存储的有用字段:")
    print("\n📊 基本信息:")
    print("  - duration (时长)")
    print("  - size (文件大小)")
    print("  - bit_rate (总比特率)")
    print("  - format_name (格式名称)")
    print("  - format_long_name (格式详细名称)")
    
    print("\n🎬 视频信息:")
    print("  - width (宽度)")
    print("  - height (高度)")
    print("  - video_codec (视频编码)")
    print("  - frame_rate (帧率)")
    print("  - aspect_ratio (宽高比)")
    print("  - pixel_format (像素格式)")
    
    print("\n🔊 音频信息:")
    print("  - audio_codec (音频编码)")
    print("  - sample_rate (采样率)")
    print("  - channels (声道数)")
    print("  - channel_layout (声道布局)")
    
    print("\n📈 质量信息:")
    print("  - video_bit_rate (视频比特率)")
    print("  - audio_bit_rate (音频比特率)")
    print("  - nb_frames (总帧数)")

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("使用方法: python explore_video_info.py <视频文件路径>")
        print("\n示例:")
        print('  python explore_video_info.py "uploads/videos/sample.mp4"')
        return
    
    video_path = sys.argv[1]
    print(f"正在分析视频文件: {video_path}")
    
    info = get_video_info(video_path)
    if not info:
        print("无法获取视频信息")
        return
    
    print_available_fields(info)
    suggest_useful_fields()
    
    print("\n\n💡 提示:")
    print("请查看上述信息，选择您希望存储在数据库中的字段。")
    print("建议选择对用户有用的字段，避免存储过多冗余信息。")

if __name__ == "__main__":
    main()