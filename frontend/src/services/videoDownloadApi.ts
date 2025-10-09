/**
 * 视频下载API服务
 * 
 * 提供视频下载相关的API调用功能
 */

import { apiService } from './api';

// 视频解析请求接口
export interface VideoParseRequest {
  url: string;
  minimal?: boolean;
}

// 视频下载请求接口
export interface VideoDownloadRequest {
  url: string;
  format?: string;
  quality?: string;
  download_video?: boolean;
  download_audio?: boolean;
  download_subtitles?: boolean;
  download_thumbnail?: boolean;
}

// 下载任务接口
export interface DownloadTask {
  id: string;
  url: string;
  title: string;
  platform: string;
  status: 'pending' | 'downloading' | 'completed' | 'failed' | 'cancelled';
  progress: number;
  created_at: string;
  updated_at: string;
  file_path?: string;
  error_message?: string;
}

// 视频信息接口
export interface VideoInfo {
  platform: string;
  video_id: string;
  title: string;
  type: 'video' | 'image';
  video_url?: string;
  images?: string[];
  thumbnail: string;
  duration?: number;
  author: {
    name: string;
    unique_id?: string;
    avatar?: string;
    followers?: string;
  };
  statistics?: {
    digg_count?: number;
    comment_count?: number;
    share_count?: number;
    play_count?: number;
    views?: string;
  };
  create_time?: string;
  publish_time?: string;
  keywords?: string[];
  original_url: string;
}

// 支持的平台接口
export interface SupportedPlatform {
  name: string;
  display_name: string;
  icon: string;
  color: string;
  supported_features: string[];
}

class VideoDownloadApi {
  /**
   * 解析视频信息
   */
  async parseVideo(request: VideoParseRequest): Promise<VideoInfo> {
    const response = await apiService.post('/video-download/parse', request);
    return response.data;
  }

  /**
   * 创建下载任务
   */
  async createDownloadTask(request: VideoDownloadRequest): Promise<{
    task_id: string;
    status: string;
    title: string;
    platform: string;
  }> {
    const response = await apiService.post('/video-download/download', request);
    return response.data;
  }

  /**
   * 获取下载任务列表
   */
  async getDownloadTasks(params?: {
    status?: string;
    limit?: number;
    offset?: number;
  }): Promise<{
    tasks: DownloadTask[];
    total: number;
  }> {
    const response = await apiService.get('/video-download/tasks', params);
    return response.data;
  }

  /**
   * 获取下载任务详情
   */
  async getDownloadTask(taskId: string): Promise<DownloadTask> {
    const response = await apiService.get(`/video-download/tasks/${taskId}`);
    return response.data;
  }

  /**
   * 取消下载任务
   */
  async cancelDownloadTask(taskId: string): Promise<{ task_id: string }> {
    const response = await apiService.post(`/video-download/tasks/${taskId}/cancel`);
    return response.data;
  }

  /**
   * 重试下载任务
   */
  async retryDownloadTask(taskId: string): Promise<{ task_id: string }> {
    const response = await apiService.post(`/video-download/tasks/${taskId}/retry`);
    return response.data;
  }

  /**
   * 删除下载任务
   */
  async deleteDownloadTask(taskId: string): Promise<{ task_id: string }> {
    const response = await apiService.delete(`/video-download/tasks/${taskId}`);
    return response.data;
  }

  /**
   * 获取支持的平台列表
   */
  async getSupportedPlatforms(): Promise<{
    platforms: SupportedPlatform[];
    total: number;
  }> {
    const response = await apiService.get('/video-download/platforms');
    return response.data;
  }
}

// 创建并导出API实例
export const videoDownloadApi = new VideoDownloadApi();
export default videoDownloadApi;