#!/usr/bin/env python3
"""
视频Base64编码工具

提供视频文件的Base64编码功能，支持使用ffmpeg进行视频压缩以减小文件大小。
用于解决GLM-4.5V视频分析中URL访问失败的问题。
"""

import os
import base64
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Optional, Tuple

from app.core.app_logging import api_logger



class VideoBase64Encoder:
    """视频Base64编码器"""
    
    def __init__(self):
        self.max_file_size = 10 * 1024 * 1024  # 10MB限制
        self.ffmpeg_path = "ffmpeg"  # 假设ffmpeg在PATH中
    
    def check_ffmpeg_available(self) -> bool:
        """检查ffmpeg是否可用"""
        try:
            result = subprocess.run(
                [self.ffmpeg_path, "-version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except Exception as e:
            api_logger.warning(f"FFmpeg不可用: {e}")
            return False
    
    def get_video_info(self, video_path: str) -> Optional[dict]:
        """获取视频基本信息"""
        try:
            cmd = [
                self.ffmpeg_path, "-i", video_path,
                "-f", "null", "-",
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams"
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                # 从stderr中提取信息（ffmpeg输出到stderr）
                return {"available": True}
            return None
            
        except Exception as e:
            api_logger.error(f"获取视频信息失败: {e}")
            return None
    
    def compress_video(self, input_path: str, target_size_mb: float = 5.0) -> Optional[str]:
        """压缩视频文件
        
        Args:
            input_path: 输入视频路径
            target_size_mb: 目标文件大小（MB）
            
        Returns:
            压缩后的临时文件路径，失败返回None
        """
        if not self.check_ffmpeg_available():
            api_logger.warning("FFmpeg不可用，无法压缩视频")
            return None
        
        try:
            # 创建临时文件
            temp_dir = tempfile.gettempdir()
            temp_filename = f"compressed_{int(time.time())}.mp4"
            output_path = os.path.join(temp_dir, temp_filename)
            
            # 获取原始文件大小
            original_size = os.path.getsize(input_path) / (1024 * 1024)  # MB
            
            if original_size <= target_size_mb:
                api_logger.info(f"视频文件已经足够小: {original_size:.2f}MB")
                return input_path
            
            # 计算压缩比例
            compression_ratio = target_size_mb / original_size
            
            # 构建ffmpeg命令
            cmd = [
                self.ffmpeg_path,
                "-i", input_path,
                "-c:v", "libx264",  # 使用H.264编码
                "-crf", "28",       # 质量参数，28是较好的平衡点
                "-preset", "fast",  # 编码速度
                "-c:a", "aac",      # 音频编码
                "-b:a", "64k",      # 音频比特率
                "-movflags", "+faststart",  # 优化网络播放
                "-y",               # 覆盖输出文件
                output_path
            ]
            
            # 如果压缩比例很大，调整更激进的参数
            if compression_ratio < 0.3:
                cmd[cmd.index("-crf") + 1] = "32"  # 更高压缩
                cmd.extend(["-vf", "scale=iw*0.8:ih*0.8"])  # 缩小分辨率
            
            api_logger.info(f"开始压缩视频: {original_size:.2f}MB -> {target_size_mb:.2f}MB")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
            
            if result.returncode == 0 and os.path.exists(output_path):
                compressed_size = os.path.getsize(output_path) / (1024 * 1024)
                api_logger.info(f"视频压缩完成: {compressed_size:.2f}MB")
                return output_path
            else:
                api_logger.error(f"视频压缩失败: {result.stderr}")
                return None
                
        except Exception as e:
            api_logger.error(f"视频压缩异常: {e}")
            return None
    
    def encode_video_to_base64(self, video_path: str, compress: bool = True) -> Optional[str]:
        """将视频文件编码为Base64
        
        Args:
            video_path: 视频文件路径
            compress: 是否先压缩视频
            
        Returns:
            Base64编码字符串，失败返回None
        """
        try:
            # 检查文件是否存在
            if not os.path.exists(video_path):
                api_logger.error(f"视频文件不存在: {video_path}")
                return None
            
            # 检查文件大小
            file_size = os.path.getsize(video_path)
            file_size_mb = file_size / (1024 * 1024)
            
            api_logger.info(f"原始视频文件大小: {file_size_mb:.2f}MB")
            
            # 决定是否需要压缩
            final_video_path = video_path
            temp_file_created = False
            
            if file_size > self.max_file_size and compress:
                api_logger.info("文件过大，尝试压缩...")
                compressed_path = self.compress_video(video_path, target_size_mb=8.0)
                
                if compressed_path and compressed_path != video_path:
                    final_video_path = compressed_path
                    temp_file_created = True
                    
                    # 重新检查压缩后的文件大小
                    compressed_size = os.path.getsize(final_video_path)
                    if compressed_size > self.max_file_size:
                        api_logger.warning(f"压缩后文件仍然过大: {compressed_size / (1024 * 1024):.2f}MB")
                        # 可以选择继续或者返回None
            
            # 读取文件并编码
            with open(final_video_path, 'rb') as video_file:
                video_data = video_file.read()
                base64_encoded = base64.b64encode(video_data).decode('utf-8')
            
            # 清理临时文件
            if temp_file_created and final_video_path != video_path:
                try:
                    os.remove(final_video_path)
                    api_logger.info(f"已清理临时文件: {final_video_path}")
                except Exception as e:
                    api_logger.warning(f"清理临时文件失败: {e}")
            
            api_logger.info(f"视频Base64编码完成，长度: {len(base64_encoded)} 字符")
            return base64_encoded
            
        except Exception as e:
            api_logger.error(f"视频Base64编码失败: {e}")
            return None
    
    def is_suitable_for_base64(self, video_path: str) -> Tuple[bool, str]:
        """判断视频是否适合Base64编码
        
        Returns:
            (是否适合, 原因说明)
        """
        try:
            if not os.path.exists(video_path):
                return False, "文件不存在"
            
            file_size = os.path.getsize(video_path)
            file_size_mb = file_size / (1024 * 1024)
            
            if file_size_mb <= 5:
                return True, f"文件大小适中: {file_size_mb:.2f}MB"
            elif file_size_mb <= 20 and self.check_ffmpeg_available():
                return True, f"文件较大但可压缩: {file_size_mb:.2f}MB"
            else:
                return False, f"文件过大: {file_size_mb:.2f}MB"
                
        except Exception as e:
            return False, f"检查失败: {e}"


# 全局实例
video_base64_encoder = VideoBase64Encoder()