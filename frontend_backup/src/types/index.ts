// 用户相关类型
export interface User {
  id: number;
  username: string;
  email: string;
  role: string;
  active: boolean;
  avatar?: string;
}

// 视频相关类型
export interface VideoInfo {
  id: string | number;
  title: string;
  subtitle?: string;
  platform: string;
  author: {
    name: string;
    avatar?: string;
    followers?: string;
  } | string;
  tags: string[];
  duration: string;
  size: string;
  createTime: string;
  uploadTime: string;
  status: 'waiting' | 'uploading' | 'completed' | 'failed' | '已解析' | '未解析' | '解析中';
  parsedTime?: string;
  parseTime?: string;
  thumbnail: string;
  videoUrl?: string;
  views?: string;
  keywords?: string[];
  publishTime?: string;
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

// 下载选项类型
export interface DownloadOptions {
  format: string;
  quality: string;
  content: string[];
  subtitles: boolean;
  danmaku: boolean;
}

// 下载任务类型
export interface DownloadTask {
  id: number;
  title: string;
  platform: string;
  thumbnail: string;
  status: 'waiting' | 'downloading' | 'completed' | 'paused' | 'failed';
  progress: number;
  options: DownloadOptions;
}

// AI API配置类型
export interface AIApiConfig {
  id: string;
  name?: string;
  provider: string;
  apiKey: string;
  endpoint?: string;
  model?: string;
  enabled: boolean;
}

// 提示词模板类型
export interface PromptTemplate {
  id: string;
  name?: string;
  title: string;
  content: string;
}

// 标签组类型
export interface TagGroup {
  id: string;
  name: string;
  tags: string[];
}

// AI参数类型
export interface AIParams {
  temperature: number;
  thinkMode: boolean;
  otherParam?: string;
}

// 面包屑导航类型
export interface BreadcrumbItem {
  label: string;
  path: string;
}

// 排序配置类型
export interface SortConfig {
  key: string;
  direction: 'ascending' | 'descending';
}

// 列宽配置类型
export interface ColumnWidths {
  [key: string]: number;
}

// 系统设置类型
export interface SystemSettings {
  downloadPath: string;
  maxConcurrent: number;
  notifications: boolean;
  retryCount: number;
}

// 通用响应类型
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
}

// 分页参数类型
export interface PaginationParams {
  page: number;
  pageSize: number;
  total?: number;
}

// 搜索参数类型
export interface SearchParams {
  keyword?: string;
  platform?: string;
  status?: string;
  dateRange?: [string, string];
}