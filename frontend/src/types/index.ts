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
  status: 'waiting' | 'uploading' | 'completed' | 'failed';
  previewUrl: string;
  file: File;
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