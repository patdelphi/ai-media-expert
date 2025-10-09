// 通用类型定义
export interface ApiResponse<T = any> {
  success: boolean;
  data: T;
  message: string;
  code: number;
}

// 用户相关类型
export interface User {
  id: string;
  username: string;
  email: string;
  avatar?: string;
  role: 'admin' | 'user';
  created_at: string;
  updated_at: string;
}

// 视频相关类型
export interface Video {
  id: string;
  title: string;
  description?: string;
  url: string;
  thumbnail?: string;
  duration?: number;
  size: number;
  format: string;
  status: 'uploading' | 'processing' | 'completed' | 'failed';
  progress?: number;
  created_at: string;
  updated_at: string;
  user_id: string;
}

// 文件上传相关类型
export interface FileItem {
  id: string;
  name: string;
  size: string;
  progress: number;
  status: 'waiting' | 'uploading' | 'completed' | 'failed' | 'paused' | 'cancelled';
  previewUrl: string;
  file: File;
  error?: string;
  
  // 文件基本信息
  file_size?: number;
  uploadTime?: string;
  created_at?: string;
  file_created_at?: string;
  path?: string;
  saved_name?: string;
  original_filename?: string;
  saved_filename?: string;
  
  // 视频基本信息
  duration?: number;
  format_name?: string;
  format_long_name?: string;
  bit_rate?: number;
  
  // 视频流信息
  width?: number;
  height?: number;
  video_codec?: string;
  video_codec_long?: string;
  frame_rate?: string;
  avg_frame_rate?: string;
  aspect_ratio?: string;
  pixel_format?: string;
  video_bit_rate?: number;
  nb_frames?: number;
  
  // 音频流信息
  audio_codec?: string;
  audio_codec_long?: string;
  sample_rate?: number;
  channels?: number;
  channel_layout?: string;
  audio_bit_rate?: number;
  
  // 颜色和质量信息
  color_space?: string;
  color_range?: string;
  color_transfer?: string;
  color_primaries?: string;
  profile?: string;
  level?: string;
  
  // 元数据
  encoder?: string;
  creation_time?: string;
}

// 下载任务相关类型
export interface DownloadTask {
  id: string;
  url: string;
  title: string;
  platform: 'youtube' | 'bilibili' | 'tiktok' | 'other';
  status: 'pending' | 'downloading' | 'completed' | 'failed';
  progress: number;
  file_size?: number;
  download_speed?: string;
  eta?: string;
  created_at: string;
  updated_at: string;
}

// 视频分析结果类型
export interface VideoAnalysis {
  id: string;
  video_id: string;
  analysis_type: 'content' | 'quality' | 'metadata' | 'subtitle';
  result: any;
  status: 'processing' | 'completed' | 'failed';
  created_at: string;
  updated_at: string;
}

// 系统配置类型
export interface SystemConfig {
  id: string;
  key: string;
  value: string;
  description?: string;
  category: string;
  updated_at: string;
}

// 面包屑导航类型
export interface BreadcrumbItem {
  label: string;
  path: string;
}

// 菜单项类型
export interface MenuItem {
  key: string;
  label: string;
  icon: string;
  path: string;
  children?: MenuItem[];
}