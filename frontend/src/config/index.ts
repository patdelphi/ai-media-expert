// API配置
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

// 应用配置
export const APP_CONFIG = {
  name: 'AI媒体专家',
  version: '1.0.0',
  description: '智能视频处理平台',
  author: 'AI Media Expert Team',
};

// 文件上传配置
export const UPLOAD_CONFIG = {
  maxFileSize: 500 * 1024 * 1024, // 500MB
  allowedTypes: [
    'video/mp4',
    'video/avi',
    'video/mov',
    'video/wmv',
    'video/flv',
    'video/webm',
    'video/mkv',
  ],
  chunkSize: 1024 * 1024, // 1MB chunks
};

// 支持的视频平台
export const SUPPORTED_PLATFORMS = [
  {
    name: 'YouTube',
    key: 'youtube',
    icon: 'fab fa-youtube',
    color: '#FF0000',
    domains: ['youtube.com', 'youtu.be'],
  },
  {
    name: 'Bilibili',
    key: 'bilibili',
    icon: 'fas fa-video',
    color: '#00A1D6',
    domains: ['bilibili.com'],
  },
  {
    name: 'TikTok',
    key: 'tiktok',
    icon: 'fab fa-tiktok',
    color: '#000000',
    domains: ['tiktok.com'],
  },
  {
    name: '其他',
    key: 'other',
    icon: 'fas fa-globe',
    color: '#6B7280',
    domains: [],
  },
];

// 菜单配置
export const MENU_CONFIG = [
  {
    key: 'dashboard',
    label: '数据看板',
    icon: 'fas fa-tachometer-alt',
    path: '/dashboard',
    children: [
      { key: 'overview', label: '概览仪表盘', icon: 'fas fa-chart-pie', path: '/dashboard/overview' },
      { key: 'analytics', label: '数据分析', icon: 'fas fa-chart-line', path: '/dashboard/analytics' },
    ],
  },
  {
    key: 'video',
    label: '视频管理',
    icon: 'fas fa-video',
    path: '/video',
    children: [
      { key: 'upload', label: '视频上传', icon: 'fas fa-upload', path: '/video/upload' },
      { key: 'download', label: '视频下载', icon: 'fas fa-download', path: '/video/download' },
      { key: 'list', label: '视频列表', icon: 'fas fa-list', path: '/video/list' },
      { key: 'analysis', label: '视频解析', icon: 'fas fa-search', path: '/video/analysis' },
    ],
  },
  {
    key: 'system',
    label: '系统设置',
    icon: 'fas fa-cog',
    path: '/system',
    children: [
      { key: 'config', label: '系统配置', icon: 'fas fa-sliders-h', path: '/system/config' },
      { key: 'users', label: '用户管理', icon: 'fas fa-users', path: '/system/users' },
    ],
  },
];

// 主题配置
export const THEME_CONFIG = {
  colors: {
    primary: '#3B82F6',
    secondary: '#6B7280',
    success: '#10B981',
    warning: '#F59E0B',
    error: '#EF4444',
    info: '#3B82F6',
  },
  borderRadius: {
    sm: '4px',
    md: '6px',
    lg: '8px',
    xl: '12px',
  },
};