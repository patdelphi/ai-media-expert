/**
 * 视频上传页面类型定义
 *
 * 先抽离页面内的纯类型，降低主页面复杂度，便于后续继续拆分组件。
 */

export type UploadNotificationType = 'success' | 'error' | 'info';

export interface UploadNotification {
  type: UploadNotificationType;
  message: string;
}

export interface RecentFileApiItem {
  id?: number | string;
  name: string;
  size: number;
  upload_time: number;
  path: string;
  saved_name: string;
  duration?: number;
  format_name?: string;
  bit_rate?: number;
  width?: number;
  height?: number;
  video_codec?: string;
  frame_rate?: string;
  aspect_ratio?: string;
  video_ratio?: string;
  audio_codec?: string;
  sample_rate?: number;
  channels?: number;
  file_created_at?: number;
}

export interface RecentFileItem {
  id: number | string;
  name: string;
  size: number;
  uploadTime: string;
  created_at: number;
  path: string;
  saved_name: string;
  original_filename: string;
  saved_filename: string;
  duration?: number;
  format_name?: string;
  bit_rate?: number;
  width?: number;
  height?: number;
  video_codec?: string;
  frame_rate?: string;
  aspect_ratio?: string;
  video_ratio?: string;
  audio_codec?: string;
  sample_rate?: number;
  channels?: number;
  file_created_at?: number;
  upload_time: number;
}
