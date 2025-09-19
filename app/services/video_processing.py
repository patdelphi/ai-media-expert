"""视频处理服务

提供视频文件分析、格式转换、缩略图生成等功能。
"""

import os
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from app.core.config import settings
from app.core.app_logging import api_logger


class VideoProcessingService:
    """视频处理服务类"""
    
    def __init__(self):
        self.ffmpeg_path = getattr(settings, 'ffmpeg_path', 'ffmpeg')
        self.ffprobe_path = getattr(settings, 'ffprobe_path', 'ffprobe')
    
    def analyze_video(self, file_path: str) -> Dict:
        """分析视频文件信息
        
        Args:
            file_path: 视频文件路径
            
        Returns:
            包含视频信息的字典
        """
        try:
            # 使用ffprobe获取视频信息
            cmd = [
                self.ffprobe_path,
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                file_path
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            probe_data = json.loads(result.stdout)
            
            # 解析视频信息
            video_info = self._parse_video_info(probe_data)
            
            api_logger.info(
                "Video analysis completed",
                file_path=file_path,
                duration=video_info.get('duration'),
                resolution=video_info.get('resolution')
            )
            
            return video_info
            
        except subprocess.CalledProcessError as e:
            api_logger.error(
                "FFprobe command failed",
                file_path=file_path,
                error=e.stderr
            )
            raise Exception(f"Failed to analyze video: {e.stderr}")
        
        except json.JSONDecodeError as e:
            api_logger.error(
                "Failed to parse FFprobe output",
                file_path=file_path,
                error=str(e)
            )
            raise Exception(f"Failed to parse video analysis: {str(e)}")
        
        except Exception as e:
            api_logger.error(
                "Video analysis failed",
                file_path=file_path,
                error=str(e)
            )
            raise
    
    def _parse_video_info(self, probe_data: Dict) -> Dict:
        """解析ffprobe输出的视频信息"""
        video_info = {
            'duration': None,
            'resolution': None,
            'format': None,
            'fps': None,
            'bitrate': None,
            'video_codec': None,
            'audio_codec': None,
            'video_bitrate': None,
            'audio_bitrate': None,
            'file_size': None
        }
        
        # 解析格式信息
        if 'format' in probe_data:
            format_info = probe_data['format']
            
            # 时长
            if 'duration' in format_info:
                video_info['duration'] = int(float(format_info['duration']))
            
            # 比特率
            if 'bit_rate' in format_info:
                video_info['bitrate'] = int(format_info['bit_rate'])
            
            # 文件大小
            if 'size' in format_info:
                video_info['file_size'] = int(format_info['size'])
            
            # 格式名称
            if 'format_name' in format_info:
                video_info['format'] = format_info['format_name'].split(',')[0]
        
        # 解析流信息
        if 'streams' in probe_data:
            for stream in probe_data['streams']:
                if stream.get('codec_type') == 'video':
                    # 视频流信息
                    video_info['video_codec'] = stream.get('codec_name')
                    
                    # 分辨率
                    width = stream.get('width')
                    height = stream.get('height')
                    if width and height:
                        video_info['resolution'] = f"{width}x{height}"
                    
                    # 帧率
                    if 'r_frame_rate' in stream:
                        fps_str = stream['r_frame_rate']
                        if '/' in fps_str:
                            num, den = fps_str.split('/')
                            if int(den) != 0:
                                video_info['fps'] = round(int(num) / int(den), 2)
                    
                    # 视频比特率
                    if 'bit_rate' in stream:
                        video_info['video_bitrate'] = int(stream['bit_rate'])
                
                elif stream.get('codec_type') == 'audio':
                    # 音频流信息
                    video_info['audio_codec'] = stream.get('codec_name')
                    
                    # 音频比特率
                    if 'bit_rate' in stream:
                        video_info['audio_bitrate'] = int(stream['bit_rate'])
        
        return video_info
    
    def generate_thumbnail(self, file_path: str, output_path: str, timestamp: str = "00:00:01") -> bool:
        """生成视频缩略图
        
        Args:
            file_path: 视频文件路径
            output_path: 输出缩略图路径
            timestamp: 截取时间点
            
        Returns:
            是否成功生成缩略图
        """
        try:
            # 确保输出目录存在
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            cmd = [
                self.ffmpeg_path,
                '-i', file_path,
                '-ss', timestamp,
                '-vframes', '1',
                '-q:v', '2',
                '-y',  # 覆盖输出文件
                output_path
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            api_logger.info(
                "Thumbnail generated",
                file_path=file_path,
                output_path=output_path
            )
            
            return True
            
        except subprocess.CalledProcessError as e:
            api_logger.error(
                "Failed to generate thumbnail",
                file_path=file_path,
                output_path=output_path,
                error=e.stderr
            )
            return False
        
        except Exception as e:
            api_logger.error(
                "Thumbnail generation failed",
                file_path=file_path,
                error=str(e)
            )
            return False
    
    def generate_preview_images(self, file_path: str, output_dir: str, count: int = 6) -> List[str]:
        """生成视频预览图片
        
        Args:
            file_path: 视频文件路径
            output_dir: 输出目录
            count: 生成图片数量
            
        Returns:
            生成的图片路径列表
        """
        try:
            # 确保输出目录存在
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            
            # 获取视频时长
            video_info = self.analyze_video(file_path)
            duration = video_info.get('duration', 0)
            
            if duration <= 0:
                return []
            
            preview_images = []
            interval = duration / (count + 1)  # 均匀分布时间点
            
            for i in range(count):
                timestamp = int((i + 1) * interval)
                timestamp_str = f"{timestamp // 3600:02d}:{(timestamp % 3600) // 60:02d}:{timestamp % 60:02d}"
                
                output_path = Path(output_dir) / f"preview_{i+1:02d}.jpg"
                
                if self.generate_thumbnail(file_path, str(output_path), timestamp_str):
                    preview_images.append(str(output_path))
            
            api_logger.info(
                "Preview images generated",
                file_path=file_path,
                count=len(preview_images)
            )
            
            return preview_images
            
        except Exception as e:
            api_logger.error(
                "Failed to generate preview images",
                file_path=file_path,
                error=str(e)
            )
            return []
    
    def validate_video_file(self, file_path: str) -> Tuple[bool, Optional[str]]:
        """验证视频文件
        
        Args:
            file_path: 视频文件路径
            
        Returns:
            (是否有效, 错误信息)
        """
        try:
            if not os.path.exists(file_path):
                return False, "File does not exist"
            
            if os.path.getsize(file_path) == 0:
                return False, "File is empty"
            
            # 尝试分析视频
            video_info = self.analyze_video(file_path)
            
            # 检查是否有视频流
            if not video_info.get('video_codec'):
                return False, "No video stream found"
            
            # 检查时长
            duration = video_info.get('duration', 0)
            if duration <= 0:
                return False, "Invalid video duration"
            
            return True, None
            
        except Exception as e:
            return False, str(e)
    
    def get_supported_formats(self) -> List[str]:
        """获取支持的视频格式列表"""
        return [
            'mp4', 'avi', 'mov', 'wmv', 'flv', 'webm', 'mkv', 'm4v',
            'mpg', 'mpeg', '3gp', 'ogv', 'ts', 'mts', 'm2ts'
        ]
    
    def calculate_file_hash(self, file_path: str, algorithm: str = 'md5') -> str:
        """计算文件哈希值
        
        Args:
            file_path: 文件路径
            algorithm: 哈希算法 (md5, sha1, sha256)
            
        Returns:
            文件哈希值
        """
        import hashlib
        
        hash_func = getattr(hashlib, algorithm)()
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_func.update(chunk)
        
        return hash_func.hexdigest()


# 全局实例
video_processing_service = VideoProcessingService()