/**
 * 视频上传服务
 * 
 * 提供视频文件上传、进度跟踪、断点续传等功能
 */

import { apiService } from './api';

// 上传状态枚举
export enum UploadStatus {
  PENDING = 'pending',
  UPLOADING = 'uploading',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled',
  PAUSED = 'paused'
}

// 类型定义
export interface VideoFile {
  file: File;
  id: string;
  name: string;
  size: number;
  type: string;
}

export interface UploadSession {
  uploadSessionId: string;
  videoId: number;
  chunkSize: number;
  totalChunks: number;
  uploadedChunks: number[];
  uploadUrl: string;
}

export interface UploadProgress {
  videoId: number;
  uploadSessionId: string;
  status: UploadStatus;
  progress: number;
  uploadedChunks: number;
  totalChunks: number;
  uploadSpeed?: number;
  errorMessage?: string;
  estimatedTime?: number;
}

export interface UploadTask {
  id: string;
  file: VideoFile;
  session?: UploadSession;
  progress: UploadProgress;
  status: UploadStatus;
  error?: string;
  startTime?: number;
  pausedAt?: number;
  uploadedBytes: number;
  totalBytes: number;
  speed: number;
  estimatedTime: number;
  chunks: Map<number, boolean>; // 分片上传状态
  activeUploads: Set<number>; // 正在上传的分片
}

class VideoUploadService {
  private uploadTasks: Map<string, UploadTask> = new Map();
  private maxConcurrentUploads = 3;
  private chunkSize = 1024 * 1024; // 1MB
  private progressCallbacks: Map<string, (progress: UploadProgress) => void> = new Map();
  private speedCalculationInterval = 1000; // 1秒

  /**
   * 添加上传任务
   */
  async addUploadTask(file: File, title?: string, description?: string): Promise<string> {
    const taskId = this.generateTaskId();
    
    const videoFile: VideoFile = {
      file,
      id: taskId,
      name: file.name,
      size: file.size,
      type: file.type
    };

    const uploadTask: UploadTask = {
      id: taskId,
      file: videoFile,
      progress: {
        videoId: 0,
        uploadSessionId: taskId,
        status: UploadStatus.PENDING,
        progress: 0,
        uploadedChunks: 0,
        totalChunks: 1
      },
      status: UploadStatus.PENDING,
      uploadedBytes: 0,
      totalBytes: file.size,
      speed: 0,
      estimatedTime: 0,
      chunks: new Map([[0, false]]),
      activeUploads: new Set()
    };

    this.uploadTasks.set(taskId, uploadTask);
    return taskId;
  }

  /**
   * 初始化上传会话
   */
  private async initializeUpload(taskId: string, title?: string, description?: string): Promise<void> {
    const task = this.uploadTasks.get(taskId);
    if (!task) throw new Error('Upload task not found');

    try {
      const response = await apiService.post('/upload/init', {
        filename: task.file.name,
        file_size: task.file.size,
        chunk_size: this.chunkSize,
        title,
        description
      });

      // 检查响应数据结构
      if (!response || typeof response !== 'object') {
        throw new Error('Invalid response format');
      }

      if (response.code === 200 && response.data) {
        const sessionData = response.data;
        
        // 验证必要字段
        if (!sessionData.upload_session_id || !sessionData.video_id || !sessionData.total_chunks) {
          throw new Error('Missing required session data');
        }
        
        task.session = {
          uploadSessionId: sessionData.upload_session_id,
          videoId: sessionData.video_id,
          chunkSize: sessionData.chunk_size || this.chunkSize,
          totalChunks: sessionData.total_chunks,
          uploadedChunks: sessionData.uploaded_chunks || [],
          uploadUrl: sessionData.upload_url || '/api/v1/upload/chunk'
        };

        task.progress.videoId = sessionData.video_id;
        task.progress.uploadSessionId = sessionData.upload_session_id;
        task.progress.totalChunks = sessionData.total_chunks;

        // 初始化分片状态
        const uploadedChunks = sessionData.uploaded_chunks || [];
        for (let i = 0; i < sessionData.total_chunks; i++) {
          task.chunks.set(i, uploadedChunks.includes(i));
        }

        this.updateTaskProgress(taskId);
      } else {
        const errorMessage = response.message || 'Failed to initialize upload';
        throw new Error(errorMessage);
      }
    } catch (error: any) {
      task.status = UploadStatus.FAILED;
      task.error = error.message || 'Failed to initialize upload';
      this.updateTaskProgress(taskId);
      throw error;
    }
  }

  /**
   * 开始上传
   */
  async startUpload(taskId: string): Promise<void> {
    const task = this.uploadTasks.get(taskId);
    if (!task) {
      throw new Error('Upload task not found');
    }

    if (task.status === UploadStatus.UPLOADING) {
      return; // 已在上传中
    }

    task.status = UploadStatus.UPLOADING;
    task.startTime = Date.now();
    this.updateTaskProgress(taskId);

    // 开始速度计算
    this.startSpeedCalculation(taskId);

    // 使用简单上传
    await this.simpleUpload(taskId);
  }

  /**
   * 简单文件上传
   */
  private async simpleUpload(taskId: string): Promise<void> {
    const task = this.uploadTasks.get(taskId);
    if (!task) return;

    const { file } = task;

    try {
      // 创建FormData
      const formData = new FormData();
      formData.append('file', file.file);
      formData.append('title', file.name);
      formData.append('description', '视频上传');

      const response = await apiService.postForm('/simple-upload/simple', formData);

      if (response.code === 200 && response.data) {
        task.status = UploadStatus.COMPLETED;
        task.progress.status = UploadStatus.COMPLETED;
        task.progress.progress = 100;
        task.progress.videoId = 0;
        task.uploadedBytes = task.totalBytes;
        task.chunks.set(0, true);
        task.progress.uploadedChunks = 1;

        const filePath = (response.data as any).file_path;
        if (filePath) {
          console.log('文件已保存到:', filePath);
        }

        this.updateTaskProgress(taskId);
      } else {
        throw new Error(response.message || 'Upload failed');
      }
    } catch (error: any) {
      task.status = UploadStatus.FAILED;
      task.error = error.message || 'Upload failed';
      this.updateTaskProgress(taskId);
      throw error;
    }
  }

  /**
   * 上传分片（已弃用，保留用于兼容性）
   */
  private async uploadChunks(taskId: string): Promise<void> {
    const task = this.uploadTasks.get(taskId);
    if (!task || !task.session) return;

    const { session } = task; // 移除未使用的 file 变量
    const uploadPromises: Promise<void>[] = [];

    // 找出未上传的分片
    const pendingChunks: number[] = [];
    for (let i = 0; i < session.totalChunks; i++) {
      if (!task.chunks.get(i)) {
        pendingChunks.push(i);
      }
    }

    // 并发上传分片
    let chunkIndex = 0;
    const uploadNextChunk = async (): Promise<void> => {
      while (chunkIndex < pendingChunks.length && task.status === UploadStatus.UPLOADING) {
        const currentChunk = pendingChunks[chunkIndex++];
        task.activeUploads.add(currentChunk);
        
        try {
          await this.uploadChunk(taskId, currentChunk);
        } catch (error) {
          console.error(`Chunk ${currentChunk} failed:`, error);
          throw error;
        } finally {
          task.activeUploads.delete(currentChunk);
        }
      }
    };

    // 启动并发上传
    const concurrentUploads = Math.min(this.maxConcurrentUploads, pendingChunks.length);
    for (let i = 0; i < concurrentUploads; i++) {
      uploadPromises.push(uploadNextChunk());
    }

    // 等待所有分片上传完成
    try {
      await Promise.all(uploadPromises);
      
      if (task.status === UploadStatus.UPLOADING) {
        // 检查是否所有分片都已上传
        const allUploaded = Array.from(task.chunks.values()).every(uploaded => uploaded);
        if (allUploaded) {
          task.status = UploadStatus.COMPLETED;
          task.progress.status = UploadStatus.COMPLETED;
          task.progress.progress = 100;
          this.updateTaskProgress(taskId);
        }
      }
    } catch (error: any) {
      if (task.status === UploadStatus.UPLOADING) {
        task.status = UploadStatus.FAILED;
        task.error = error.message || 'Upload failed';
        this.updateTaskProgress(taskId);
      }
    }
  }

  /**
   * 上传单个分片
   */
  private async uploadChunk(taskId: string, chunkIndex: number): Promise<void> {
    const task = this.uploadTasks.get(taskId);
    if (!task || !task.session) return;

    const { session, file } = task;

    try {
      // 计算分片数据
      const start = chunkIndex * session.chunkSize;
      const end = Math.min(start + session.chunkSize, file.file.size);
      const chunkData = file.file.slice(start, end);

      // 创建FormData
      const formData = new FormData();
      formData.append('upload_session_id', session.uploadSessionId);
      formData.append('chunk_index', chunkIndex.toString());
      formData.append('total_chunks', session.totalChunks.toString());
      
      // 创建File对象而不是Blob
      const chunkFile = new File([chunkData], `chunk_${chunkIndex}`, {
        type: 'application/octet-stream'
      });
      formData.append('chunk_file', chunkFile);

      // 上传分片
      const response = await apiService.post('/upload/chunk', formData);

      if (response.code === 200) {
        // 标记分片为已上传
        task.chunks.set(chunkIndex, true);
        task.uploadedBytes += chunkData.size;
        
        // 更新进度
        const uploadedCount = Array.from(task.chunks.values()).filter(uploaded => uploaded).length;
        task.progress.uploadedChunks = uploadedCount;
        task.progress.progress = (uploadedCount / session.totalChunks) * 100;
        
        this.updateTaskProgress(taskId);
      } else {
        throw new Error(response.message || 'Chunk upload failed');
      }
    } catch (error: any) {
      // 分片上传失败，可以重试
      console.error(`Chunk ${chunkIndex} upload failed:`, error);
      throw error;
    }
  }

  /**
   * 暂停上传
   */
  async pauseUpload(taskId: string): Promise<void> {
    const task = this.uploadTasks.get(taskId);
    if (!task || !task.session) return;

    if (task.status === UploadStatus.UPLOADING) {
      task.status = UploadStatus.PAUSED;
      task.pausedAt = Date.now();
      
      // 通知后端暂停
      try {
        await apiService.post('/upload/control', {
          upload_session_id: task.session.uploadSessionId,
          action: 'pause'
        });
      } catch (error) {
        console.error('Failed to notify backend about pause:', error);
      }
      
      this.updateTaskProgress(taskId);
    }
  }

  /**
   * 恢复上传
   */
  async resumeUpload(taskId: string): Promise<void> {
    const task = this.uploadTasks.get(taskId);
    if (!task || !task.session) return;

    if (task.status === UploadStatus.PAUSED) {
      // 通知后端恢复
      try {
        await apiService.post('/upload/control', {
          upload_session_id: task.session.uploadSessionId,
          action: 'resume'
        });
        
        // 恢复上传
        await this.startUpload(taskId);
      } catch (error: any) {
        task.status = UploadStatus.FAILED;
        task.error = error.message || 'Failed to resume upload';
        this.updateTaskProgress(taskId);
      }
    }
  }

  /**
   * 取消上传
   */
  async cancelUpload(taskId: string): Promise<void> {
    const task = this.uploadTasks.get(taskId);
    if (!task) return;

    task.status = UploadStatus.CANCELLED;
    
    if (task.session) {
      // 通知后端取消
      try {
        await apiService.post('/upload/control', {
          upload_session_id: task.session.uploadSessionId,
          action: 'cancel'
        });
      } catch (error) {
        console.error('Failed to notify backend about cancellation:', error);
      }
    }
    
    this.updateTaskProgress(taskId);
  }

  /**
   * 重试上传
   */
  async retryUpload(taskId: string): Promise<void> {
    const task = this.uploadTasks.get(taskId);
    if (!task) return;

    if (task.status === UploadStatus.FAILED) {
      task.status = UploadStatus.PENDING;
      task.error = undefined;
      
      // 重新开始上传
      await this.startUpload(taskId);
    }
  }

  /**
   * 获取上传进度
   */
  async getUploadProgress(taskId: string): Promise<UploadProgress | null> {
    const task = this.uploadTasks.get(taskId);
    if (!task || !task.session) return null;

    try {
      const response = await apiService.get(`/upload/progress/${task.session.uploadSessionId}`);
      if (response.data.code === 200) {
        const progressData = response.data.data;
        task.progress = { ...task.progress, ...progressData };
        return task.progress;
      }
    } catch (error) {
      console.error('Failed to get upload progress:', error);
    }

    return task.progress;
  }

  /**
   * 获取所有上传任务
   */
  getAllTasks(): UploadTask[] {
    return Array.from(this.uploadTasks.values());
  }

  /**
   * 获取指定任务
   */
  getTask(taskId: string): UploadTask | undefined {
    return this.uploadTasks.get(taskId);
  }

  /**
   * 删除任务
   */
  removeTask(taskId: string): void {
    this.uploadTasks.delete(taskId);
    this.progressCallbacks.delete(taskId);
  }

  /**
   * 设置进度回调
   */
  onProgress(taskId: string, callback: (progress: UploadProgress) => void): void {
    this.progressCallbacks.set(taskId, callback);
  }

  /**
   * 移除进度回调
   */
  offProgress(taskId: string): void {
    this.progressCallbacks.delete(taskId);
  }

  /**
   * 更新任务进度
   */
  private updateTaskProgress(taskId: string): void {
    const task = this.uploadTasks.get(taskId);
    if (!task) return;

    const callback = this.progressCallbacks.get(taskId);
    if (callback) {
      callback(task.progress);
    }
  }

  /**
   * 开始速度计算
   */
  private startSpeedCalculation(taskId: string): void {
    const task = this.uploadTasks.get(taskId);
    if (!task) return;

    let lastBytes = task.uploadedBytes;
    let lastTime = Date.now();

    const calculateSpeed = () => {
      if (task.status !== UploadStatus.UPLOADING) {
        return;
      }

      const currentTime = Date.now();
      const currentBytes = task.uploadedBytes;
      const timeDiff = (currentTime - lastTime) / 1000; // 秒
      const bytesDiff = currentBytes - lastBytes;

      if (timeDiff > 0) {
        task.speed = bytesDiff / timeDiff; // bytes/s
        
        // 计算预计剩余时间
        const remainingBytes = task.totalBytes - currentBytes;
        if (task.speed > 0) {
          task.estimatedTime = Math.ceil(remainingBytes / task.speed);
        }

        task.progress.uploadSpeed = task.speed;
        task.progress.estimatedTime = task.estimatedTime;
        
        this.updateTaskProgress(taskId);
      }

      lastBytes = currentBytes;
      lastTime = currentTime;

      // 继续计算
      setTimeout(calculateSpeed, this.speedCalculationInterval);
    };

    // 开始计算
    setTimeout(calculateSpeed, this.speedCalculationInterval);
  }

  /**
   * 生成任务ID
   */
  private generateTaskId(): string {
    return `upload_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * 格式化文件大小
   */
  static formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  /**
   * 格式化上传速度
   */
  static formatSpeed(bytesPerSecond: number): string {
    return this.formatFileSize(bytesPerSecond) + '/s';
  }

  /**
   * 格式化时间
   */
  static formatTime(seconds: number): string {
    if (seconds < 60) {
      return `${Math.ceil(seconds)}秒`;
    } else if (seconds < 3600) {
      const minutes = Math.floor(seconds / 60);
      const remainingSeconds = Math.ceil(seconds % 60);
      return `${minutes}分${remainingSeconds}秒`;
    } else {
      const hours = Math.floor(seconds / 3600);
      const minutes = Math.floor((seconds % 3600) / 60);
      return `${hours}小时${minutes}分钟`;
    }
  }
}

// 导出类和单例
export { VideoUploadService };
export const videoUploadService = new VideoUploadService();
export default videoUploadService;
