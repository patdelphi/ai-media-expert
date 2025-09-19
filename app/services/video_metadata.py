"""视频元数据提取服务

提供高级视频元数据提取功能，包括视频标题、描述、标签等信息。
"""

import os
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from app.core.config import settings
from app.core.app_logging import api_logger


class VideoMetadataExtractor:
    """视频元数据提取器"""
    
    def __init__(self):
        self.ffprobe_path = getattr(settings, 'ffprobe_path', 'ffprobe')
    
    def extract_comprehensive_metadata(self, file_path: str) -> Dict[str, Any]:
        """提取全面的视频元数据
        
        Args:
            file_path: 视频文件路径
            
        Returns:
            包含详细元数据的字典
        """
        try:
            # 使用ffprobe获取详细信息
            cmd = [
                self.ffprobe_path,
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                '-show_chapters',
                '-show_programs',
                file_path
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            probe_data = json.loads(result.stdout)
            
            # 解析元数据
            metadata = self._parse_comprehensive_metadata(probe_data, file_path)
            
            api_logger.info(
                "Comprehensive metadata extraction completed",
                file_path=file_path,
                metadata_keys=list(metadata.keys())
            )
            
            return metadata
            
        except subprocess.CalledProcessError as e:
            api_logger.error(
                "FFprobe command failed for metadata extraction",
                file_path=file_path,
                error=e.stderr
            )
            raise Exception(f"Failed to extract metadata: {e.stderr}")
        
        except json.JSONDecodeError as e:
            api_logger.error(
                "Failed to parse FFprobe metadata output",
                file_path=file_path,
                error=str(e)
            )
            raise Exception(f"Failed to parse metadata: {str(e)}")
        
        except Exception as e:
            api_logger.error(
                "Metadata extraction failed",
                file_path=file_path,
                error=str(e)
            )
            raise
    
    def _parse_comprehensive_metadata(self, probe_data: Dict, file_path: str) -> Dict[str, Any]:
        """解析全面的元数据信息"""
        metadata = {
            'file_info': self._extract_file_info(file_path),
            'format_info': self._extract_format_info(probe_data.get('format', {})),
            'video_streams': [],
            'audio_streams': [],
            'subtitle_streams': [],
            'chapters': [],
            'embedded_metadata': {},
            'technical_analysis': {}
        }
        
        # 解析流信息
        if 'streams' in probe_data:
            for stream in probe_data['streams']:
                stream_type = stream.get('codec_type')
                if stream_type == 'video':
                    metadata['video_streams'].append(self._extract_video_stream_info(stream))
                elif stream_type == 'audio':
                    metadata['audio_streams'].append(self._extract_audio_stream_info(stream))
                elif stream_type == 'subtitle':
                    metadata['subtitle_streams'].append(self._extract_subtitle_stream_info(stream))
        
        # 解析章节信息
        if 'chapters' in probe_data:
            for chapter in probe_data['chapters']:
                metadata['chapters'].append(self._extract_chapter_info(chapter))
        
        # 提取嵌入的元数据
        if 'format' in probe_data and 'tags' in probe_data['format']:
            metadata['embedded_metadata'] = self._extract_embedded_metadata(probe_data['format']['tags'])
        
        # 技术分析
        metadata['technical_analysis'] = self._perform_technical_analysis(metadata)
        
        return metadata
    
    def _extract_file_info(self, file_path: str) -> Dict[str, Any]:
        """提取文件基本信息"""
        file_stat = os.stat(file_path)
        file_obj = Path(file_path)
        
        return {
            'filename': file_obj.name,
            'extension': file_obj.suffix.lower(),
            'size_bytes': file_stat.st_size,
            'size_mb': round(file_stat.st_size / (1024 * 1024), 2),
            'created_time': datetime.fromtimestamp(file_stat.st_ctime).isoformat(),
            'modified_time': datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
            'absolute_path': str(file_obj.absolute())
        }
    
    def _extract_format_info(self, format_data: Dict) -> Dict[str, Any]:
        """提取格式信息"""
        return {
            'format_name': format_data.get('format_name', ''),
            'format_long_name': format_data.get('format_long_name', ''),
            'duration': float(format_data.get('duration', 0)),
            'size': int(format_data.get('size', 0)),
            'bit_rate': int(format_data.get('bit_rate', 0)),
            'probe_score': format_data.get('probe_score', 0),
            'nb_streams': format_data.get('nb_streams', 0),
            'nb_programs': format_data.get('nb_programs', 0)
        }
    
    def _extract_video_stream_info(self, stream: Dict) -> Dict[str, Any]:
        """提取视频流信息"""
        return {
            'index': stream.get('index', 0),
            'codec_name': stream.get('codec_name', ''),
            'codec_long_name': stream.get('codec_long_name', ''),
            'profile': stream.get('profile', ''),
            'codec_type': stream.get('codec_type', ''),
            'width': stream.get('width', 0),
            'height': stream.get('height', 0),
            'coded_width': stream.get('coded_width', 0),
            'coded_height': stream.get('coded_height', 0),
            'closed_captions': stream.get('closed_captions', 0),
            'film_grain': stream.get('film_grain', 0),
            'has_b_frames': stream.get('has_b_frames', 0),
            'sample_aspect_ratio': stream.get('sample_aspect_ratio', ''),
            'display_aspect_ratio': stream.get('display_aspect_ratio', ''),
            'pix_fmt': stream.get('pix_fmt', ''),
            'level': stream.get('level', 0),
            'color_range': stream.get('color_range', ''),
            'color_space': stream.get('color_space', ''),
            'color_transfer': stream.get('color_transfer', ''),
            'color_primaries': stream.get('color_primaries', ''),
            'chroma_location': stream.get('chroma_location', ''),
            'field_order': stream.get('field_order', ''),
            'refs': stream.get('refs', 0),
            'r_frame_rate': stream.get('r_frame_rate', ''),
            'avg_frame_rate': stream.get('avg_frame_rate', ''),
            'time_base': stream.get('time_base', ''),
            'start_pts': stream.get('start_pts', 0),
            'start_time': stream.get('start_time', '0'),
            'duration_ts': stream.get('duration_ts', 0),
            'duration': stream.get('duration', '0'),
            'bit_rate': stream.get('bit_rate', '0'),
            'max_bit_rate': stream.get('max_bit_rate', '0'),
            'bits_per_raw_sample': stream.get('bits_per_raw_sample', '0'),
            'nb_frames': stream.get('nb_frames', '0'),
            'extradata_size': stream.get('extradata_size', 0),
            'tags': stream.get('tags', {})
        }
    
    def _extract_audio_stream_info(self, stream: Dict) -> Dict[str, Any]:
        """提取音频流信息"""
        return {
            'index': stream.get('index', 0),
            'codec_name': stream.get('codec_name', ''),
            'codec_long_name': stream.get('codec_long_name', ''),
            'profile': stream.get('profile', ''),
            'codec_type': stream.get('codec_type', ''),
            'sample_fmt': stream.get('sample_fmt', ''),
            'sample_rate': stream.get('sample_rate', '0'),
            'channels': stream.get('channels', 0),
            'channel_layout': stream.get('channel_layout', ''),
            'bits_per_sample': stream.get('bits_per_sample', 0),
            'r_frame_rate': stream.get('r_frame_rate', ''),
            'avg_frame_rate': stream.get('avg_frame_rate', ''),
            'time_base': stream.get('time_base', ''),
            'start_pts': stream.get('start_pts', 0),
            'start_time': stream.get('start_time', '0'),
            'duration_ts': stream.get('duration_ts', 0),
            'duration': stream.get('duration', '0'),
            'bit_rate': stream.get('bit_rate', '0'),
            'max_bit_rate': stream.get('max_bit_rate', '0'),
            'nb_frames': stream.get('nb_frames', '0'),
            'extradata_size': stream.get('extradata_size', 0),
            'tags': stream.get('tags', {})
        }
    
    def _extract_subtitle_stream_info(self, stream: Dict) -> Dict[str, Any]:
        """提取字幕流信息"""
        return {
            'index': stream.get('index', 0),
            'codec_name': stream.get('codec_name', ''),
            'codec_long_name': stream.get('codec_long_name', ''),
            'codec_type': stream.get('codec_type', ''),
            'r_frame_rate': stream.get('r_frame_rate', ''),
            'avg_frame_rate': stream.get('avg_frame_rate', ''),
            'time_base': stream.get('time_base', ''),
            'start_pts': stream.get('start_pts', 0),
            'start_time': stream.get('start_time', '0'),
            'duration_ts': stream.get('duration_ts', 0),
            'duration': stream.get('duration', '0'),
            'extradata_size': stream.get('extradata_size', 0),
            'tags': stream.get('tags', {})
        }
    
    def _extract_chapter_info(self, chapter: Dict) -> Dict[str, Any]:
        """提取章节信息"""
        return {
            'id': chapter.get('id', 0),
            'time_base': chapter.get('time_base', ''),
            'start': chapter.get('start', 0),
            'start_time': chapter.get('start_time', '0'),
            'end': chapter.get('end', 0),
            'end_time': chapter.get('end_time', '0'),
            'tags': chapter.get('tags', {})
        }
    
    def _extract_embedded_metadata(self, tags: Dict) -> Dict[str, Any]:
        """提取嵌入的元数据标签"""
        # 常见的元数据标签映射
        metadata_mapping = {
            'title': ['title', 'Title', 'TITLE'],
            'artist': ['artist', 'Artist', 'ARTIST', 'author', 'Author', 'AUTHOR'],
            'album': ['album', 'Album', 'ALBUM'],
            'date': ['date', 'Date', 'DATE', 'year', 'Year', 'YEAR'],
            'genre': ['genre', 'Genre', 'GENRE'],
            'comment': ['comment', 'Comment', 'COMMENT', 'description', 'Description', 'DESCRIPTION'],
            'track': ['track', 'Track', 'TRACK'],
            'encoder': ['encoder', 'Encoder', 'ENCODER'],
            'copyright': ['copyright', 'Copyright', 'COPYRIGHT'],
            'creation_time': ['creation_time', 'Creation_time', 'CREATION_TIME'],
            'language': ['language', 'Language', 'LANGUAGE']
        }
        
        extracted_metadata = {}
        
        # 提取标准化的元数据
        for key, possible_tags in metadata_mapping.items():
            for tag in possible_tags:
                if tag in tags:
                    extracted_metadata[key] = tags[tag]
                    break
        
        # 保留所有原始标签
        extracted_metadata['raw_tags'] = tags
        
        return extracted_metadata
    
    def _perform_technical_analysis(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """执行技术分析"""
        analysis = {
            'video_quality_score': 0,
            'audio_quality_score': 0,
            'overall_quality_score': 0,
            'compression_efficiency': 0,
            'streaming_suitability': 'unknown',
            'mobile_compatibility': 'unknown',
            'recommendations': []
        }
        
        # 分析视频质量
        if metadata['video_streams']:
            video_stream = metadata['video_streams'][0]  # 主视频流
            width = video_stream.get('width', 0)
            height = video_stream.get('height', 0)
            bit_rate = int(video_stream.get('bit_rate', 0))
            
            # 基于分辨率和比特率评分
            if width >= 1920 and height >= 1080:
                analysis['video_quality_score'] = 90 if bit_rate > 5000000 else 75
            elif width >= 1280 and height >= 720:
                analysis['video_quality_score'] = 80 if bit_rate > 2500000 else 65
            else:
                analysis['video_quality_score'] = 60 if bit_rate > 1000000 else 40
        
        # 分析音频质量
        if metadata['audio_streams']:
            audio_stream = metadata['audio_streams'][0]  # 主音频流
            sample_rate = int(audio_stream.get('sample_rate', 0))
            bit_rate = int(audio_stream.get('bit_rate', 0))
            channels = audio_stream.get('channels', 0)
            
            # 基于采样率、比特率和声道数评分
            if sample_rate >= 44100 and bit_rate >= 128000:
                analysis['audio_quality_score'] = 90 if channels >= 2 else 80
            elif sample_rate >= 22050 and bit_rate >= 64000:
                analysis['audio_quality_score'] = 70
            else:
                analysis['audio_quality_score'] = 50
        
        # 计算总体质量分数
        if metadata['video_streams'] and metadata['audio_streams']:
            analysis['overall_quality_score'] = int(
                (analysis['video_quality_score'] * 0.7 + analysis['audio_quality_score'] * 0.3)
            )
        elif metadata['video_streams']:
            analysis['overall_quality_score'] = analysis['video_quality_score']
        elif metadata['audio_streams']:
            analysis['overall_quality_score'] = analysis['audio_quality_score']
        
        # 分析压缩效率
        file_size_mb = metadata['file_info']['size_mb']
        duration_minutes = metadata['format_info']['duration'] / 60
        if duration_minutes > 0:
            mb_per_minute = file_size_mb / duration_minutes
            if mb_per_minute < 10:
                analysis['compression_efficiency'] = 90
            elif mb_per_minute < 20:
                analysis['compression_efficiency'] = 75
            elif mb_per_minute < 50:
                analysis['compression_efficiency'] = 60
            else:
                analysis['compression_efficiency'] = 40
        
        # 流媒体适用性分析
        if metadata['video_streams']:
            video_codec = metadata['video_streams'][0].get('codec_name', '')
            if video_codec in ['h264', 'h265', 'vp9']:
                analysis['streaming_suitability'] = 'excellent'
            elif video_codec in ['vp8', 'mpeg4']:
                analysis['streaming_suitability'] = 'good'
            else:
                analysis['streaming_suitability'] = 'poor'
        
        # 移动设备兼容性分析
        if metadata['video_streams']:
            video_stream = metadata['video_streams'][0]
            codec = video_stream.get('codec_name', '')
            profile = video_stream.get('profile', '')
            
            if codec == 'h264' and 'baseline' in profile.lower():
                analysis['mobile_compatibility'] = 'excellent'
            elif codec in ['h264', 'h265']:
                analysis['mobile_compatibility'] = 'good'
            else:
                analysis['mobile_compatibility'] = 'limited'
        
        # 生成建议
        recommendations = []
        if analysis['video_quality_score'] < 70:
            recommendations.append('考虑提高视频比特率以改善画质')
        if analysis['audio_quality_score'] < 70:
            recommendations.append('考虑提高音频比特率或采样率')
        if analysis['compression_efficiency'] < 60:
            recommendations.append('文件大小较大，建议优化压缩设置')
        if analysis['streaming_suitability'] == 'poor':
            recommendations.append('建议转换为H.264或H.265格式以提高流媒体兼容性')
        if analysis['mobile_compatibility'] == 'limited':
            recommendations.append('建议使用H.264 Baseline Profile以提高移动设备兼容性')
        
        analysis['recommendations'] = recommendations
        
        return analysis
    
    def extract_smart_title_and_tags(self, file_path: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """智能提取标题和标签
        
        基于文件名、嵌入元数据和内容分析生成智能标题和标签。
        """
        result = {
            'suggested_title': '',
            'suggested_tags': [],
            'confidence_score': 0
        }
        
        # 从嵌入元数据获取标题
        embedded_title = metadata.get('embedded_metadata', {}).get('title', '')
        
        # 从文件名提取标题
        filename = Path(file_path).stem
        filename_title = self._clean_filename_for_title(filename)
        
        # 选择最佳标题
        if embedded_title and len(embedded_title.strip()) > 3:
            result['suggested_title'] = embedded_title.strip()
            result['confidence_score'] += 40
        elif filename_title and len(filename_title.strip()) > 3:
            result['suggested_title'] = filename_title
            result['confidence_score'] += 20
        else:
            result['suggested_title'] = f"视频_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            result['confidence_score'] += 10
        
        # 生成标签
        tags = set()
        
        # 基于技术参数的标签
        if metadata.get('video_streams'):
            video_stream = metadata['video_streams'][0]
            width = video_stream.get('width', 0)
            height = video_stream.get('height', 0)
            
            if width >= 3840 and height >= 2160:
                tags.add('4K')
                tags.add('超高清')
            elif width >= 1920 and height >= 1080:
                tags.add('1080p')
                tags.add('高清')
            elif width >= 1280 and height >= 720:
                tags.add('720p')
                tags.add('标清')
            
            codec = video_stream.get('codec_name', '')
            if codec:
                tags.add(codec.upper())
        
        # 基于音频参数的标签
        if metadata.get('audio_streams'):
            audio_stream = metadata['audio_streams'][0]
            channels = audio_stream.get('channels', 0)
            if channels >= 6:
                tags.add('环绕声')
            elif channels == 2:
                tags.add('立体声')
            elif channels == 1:
                tags.add('单声道')
        
        # 基于时长的标签
        duration = metadata.get('format_info', {}).get('duration', 0)
        if duration > 3600:  # 超过1小时
            tags.add('长视频')
        elif duration < 60:  # 少于1分钟
            tags.add('短视频')
        
        # 基于文件大小的标签
        file_size_mb = metadata.get('file_info', {}).get('size_mb', 0)
        if file_size_mb > 1000:  # 大于1GB
            tags.add('大文件')
        elif file_size_mb < 10:  # 小于10MB
            tags.add('小文件')
        
        # 基于质量分析的标签
        quality_score = metadata.get('technical_analysis', {}).get('overall_quality_score', 0)
        if quality_score >= 80:
            tags.add('高质量')
        elif quality_score < 50:
            tags.add('低质量')
        
        result['suggested_tags'] = list(tags)
        result['confidence_score'] = min(100, result['confidence_score'] + len(tags) * 5)
        
        return result
    
    def _clean_filename_for_title(self, filename: str) -> str:
        """清理文件名作为标题"""
        # 移除常见的文件名模式
        import re
        
        # 移除日期时间模式
        filename = re.sub(r'\d{4}[-_]\d{2}[-_]\d{2}', '', filename)
        filename = re.sub(r'\d{2}[-_]\d{2}[-_]\d{4}', '', filename)
        filename = re.sub(r'\d{8}', '', filename)
        
        # 移除时间模式
        filename = re.sub(r'\d{2}[-_:]\d{2}[-_:]\d{2}', '', filename)
        filename = re.sub(r'\d{6}', '', filename)
        
        # 移除常见的后缀
        filename = re.sub(r'[-_](copy|副本|备份|final|最终|v\d+)$', '', filename, flags=re.IGNORECASE)
        
        # 替换分隔符为空格
        filename = re.sub(r'[-_]+', ' ', filename)
        
        # 清理多余空格
        filename = ' '.join(filename.split())
        
        return filename.strip()


# 全局实例
video_metadata_extractor = VideoMetadataExtractor()