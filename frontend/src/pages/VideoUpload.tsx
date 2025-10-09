import React, { useState, useRef, useEffect } from 'react';
import { FileItem } from '../types';
import { formatFileSize, generateId } from '../utils';
import { useAuth } from '../contexts/AuthContext';
import VideoPlayer from '../components/VideoPlayer';

const VideoUpload: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuth();
  const [files, setFiles] = useState<FileItem[]>([]);
  // 移除不再需要的uploadTasks状态
  const [isDragging, setIsDragging] = useState(false);
  const [totalProgress, setTotalProgress] = useState(0);
  const [uploadSpeed, setUploadSpeed] = useState('0 KB/s');
  const [remainingTime, setRemainingTime] = useState('--');
  const [isUploading, setIsUploading] = useState(false);
  const [notification, setNotification] = useState<{type: 'success' | 'error' | 'info', message: string} | null>(null);
  const [recentFiles, setRecentFiles] = useState<any[]>([]);
  const [isPlayerOpen, setIsPlayerOpen] = useState(false);
  const [currentVideo, setCurrentVideo] = useState<{url: string, title: string} | null>(null);
  const [showTimeEditor, setShowTimeEditor] = useState(false);
  const [editingFile, setEditingFile] = useState<FileItem | null>(null);
  const [customTime, setCustomTime] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  // 检查认证状态
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg">加载中...</div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <h2 className="text-xl font-semibold mb-4">请先登录</h2>
          <p className="text-gray-600 mb-4">您需要登录后才能上传视频</p>
          <a href="/login" className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600">
            前往登录
          </a>
        </div>
      </div>
    );
  }

  // 显示通知
  const showNotification = (type: 'success' | 'error' | 'info', message: string) => {
    setNotification({ type, message });
    setTimeout(() => setNotification(null), 5000); // 5秒后自动消失
  };

  // 加载最近上传的文件
  const loadRecentFiles = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/files/files', {
        method: 'GET',
        mode: 'cors',
        credentials: 'omit'
      });
      
      if (response.ok) {
        const result = await response.json();
        if (result.success) {
          // 只显示最近10个文件，并正确映射字段
          const recent = result.files.slice(0, 10).map((file: any) => ({
            id: file.id || `file-${Date.now()}-${Math.random()}`,
            name: file.name, // API返回的是name字段
            size: file.size,
            uploadTime: new Date(file.upload_time * 1000).toLocaleString('zh-CN'), // Unix时间戳转换
            created_at: file.upload_time,
            path: file.path,
            saved_name: file.saved_name, // API返回的存储文件名
            original_filename: file.name,
            saved_filename: file.saved_name,
            
            // 视频基本信息
            duration: file.duration,
            format_name: file.format_name,
            bit_rate: file.bit_rate,
            
            // 视频流信息
            width: file.width,
            height: file.height,
            video_codec: file.video_codec,
            frame_rate: file.frame_rate,
            aspect_ratio: file.aspect_ratio,
            
            // 音频流信息
            audio_codec: file.audio_codec,
            sample_rate: file.sample_rate,
            channels: file.channels,
            
            // 文件时间信息
            file_created_at: file.file_created_at,
            upload_time: file.upload_time
          }));
          setRecentFiles(recent);
          console.log('加载的文件数据:', recent); // 调试日志
        }
      }
    } catch (error) {
      console.error('加载最近文件失败:', error);
    }
  };

  // 简化的上传函数 - 参考file_manager.html的实现
  const uploadFile = async (fileItem: FileItem) => {
    try {
      console.log('开始上传文件:', fileItem.name, '大小:', fileItem.file.size, '类型:', fileItem.file.type);
      
      // 更新状态为上传中
      setFiles(prevFiles =>
        prevFiles.map(item =>
          item.id === fileItem.id ? { ...item, status: 'uploading', progress: 0 } : item
        )
      );
      
      const formData = new FormData();
      formData.append('file', fileItem.file);
      formData.append('title', fileItem.name);
      formData.append('description', '通过视频上传页面上传');

      console.log('发送请求到:', 'http://localhost:8000/api/v1/minimal/upload');
      
      const response = await fetch('http://localhost:8000/api/v1/minimal/upload', {
        method: 'POST',
        body: formData,
        mode: 'cors',
        credentials: 'omit'
      });

      console.log('响应状态:', response.status, response.statusText);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('HTTP错误响应:', errorText);
        throw new Error(`HTTP ${response.status}: ${response.statusText}\n${errorText}`);
      }

      const result = await response.json();
      console.log('上传响应:', result);
      
      if (!result.success) {
        throw new Error(result.error || result.message || '上传失败');
      }

      // 上传成功
      setFiles(prevFiles =>
        prevFiles.map(item =>
          item.id === fileItem.id 
            ? { ...item, status: 'completed', progress: 100 }
            : item
        )
      );
      
      showNotification('success', `${fileItem.name} 上传完成`);
      
      // 刷新最近文件列表
      await loadRecentFiles();
      
    } catch (error: any) {
      console.error('上传过程中发生错误:', error);
      const errorMessage = error.message || '上传失败，请重试';
      showNotification('error', `${fileItem.name} 上传失败: ${errorMessage}`);
      
      setFiles(prevFiles =>
        prevFiles.map(item =>
          item.id === fileItem.id 
            ? { ...item, status: 'failed', error: errorMessage, progress: 0 }
            : item
        )
      );
    }
  };

  // 更新总体进度
  const updateOverallProgress = () => {
    if (files.length === 0) {
      setTotalProgress(0);
      return;
    }
    
    const totalProgress = files.reduce((sum, file) => sum + file.progress, 0) / files.length;
    setTotalProgress(Math.round(totalProgress));
    
    // 简化速度和时间显示
    const uploadingFiles = files.filter(f => f.status === 'uploading');
    if (uploadingFiles.length > 0) {
      setUploadSpeed('上传中...');
      setRemainingTime('计算中...');
    } else {
      setUploadSpeed('0 KB/s');
      setRemainingTime('--');
    }
  };

  const handleUpload = async () => {
    if (files.length === 0) return;
    
    setIsUploading(true);
    setTotalProgress(0);
    
    // 逐个上传文件（避免并发问题）
    const waitingFiles = files.filter(file => file.status === 'waiting');
    
    for (let i = 0; i < waitingFiles.length; i++) {
      const fileItem = waitingFiles[i];
      try {
        await uploadFile(fileItem);
        // 更新总进度
        const progress = Math.round(((i + 1) / waitingFiles.length) * 100);
        setTotalProgress(progress);
      } catch (error) {
        console.error('Upload failed for file:', fileItem.name, error);
        // 继续上传其他文件
      }
    }
    
    setIsUploading(false);
    updateOverallProgress();
    
    // 上传完成后，延迟2秒自动清除已完成的文件
    setTimeout(() => {
      setFiles(prevFiles => prevFiles.filter(file => file.status !== 'completed'));
      showNotification('info', '已完成的文件已自动清除');
    }, 2000);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      addFiles(Array.from(e.target.files));
    }
  };

  // 文件验证
  const validateFile = (file: File): { valid: boolean; error?: string } => {
    // 检查文件类型
    const allowedTypes = ['video/mp4', 'video/avi', 'video/mov', 'video/mkv', 'video/webm', 'video/flv', 'video/wmv'];
    if (!allowedTypes.includes(file.type) && !file.name.match(/\.(mp4|avi|mov|mkv|webm|flv|wmv)$/i)) {
      return { valid: false, error: '不支持的文件格式，请选择视频文件' };
    }
    
    // 检查文件大小 (500MB)
    const maxSize = 500 * 1024 * 1024;
    if (file.size > maxSize) {
      return { valid: false, error: '文件大小超过500MB限制' };
    }
    
    // 检查文件名长度
    if (file.name.length > 255) {
      return { valid: false, error: '文件名过长，请重命名后重试' };
    }
    
    return { valid: true };
  };

  const addFiles = (newFiles: File[]) => {
    const validFiles: File[] = [];
    const errors: string[] = [];
    
    // 验证每个文件
    newFiles.forEach(file => {
      const validation = validateFile(file);
      if (validation.valid) {
        // 检查是否已存在同名文件
        const exists = files.some(existingFile => existingFile.name === file.name);
        if (exists) {
          errors.push(`${file.name} 已存在，请选择不同的文件`);
        } else {
          validFiles.push(file);
        }
      } else {
        errors.push(`${file.name}: ${validation.error}`);
      }
    });
    
    // 显示错误信息
    if (errors.length > 0) {
      showNotification('error', errors.join('; '));
    }
    
    // 添加有效文件
    if (validFiles.length > 0) {
      const newItems = validFiles.map(file => ({
        id: generateId(),
        name: file.name,
        size: formatFileSize(file.size),
        progress: 0,
        status: 'waiting' as const,
        previewUrl: URL.createObjectURL(file),
        file,
      }));

      setFiles(prev => [...prev, ...newItems]);
      showNotification('success', `成功添加 ${validFiles.length} 个文件`);
    }
  };

  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    
    if (e.dataTransfer.files) {
      addFiles(Array.from(e.dataTransfer.files));
    }
  };

  const removeFile = (id: string) => {
    // 如果文件正在上传，先取消上传
    const file = files.find(f => f.id === id);
    if (file && file.status === 'uploading') {
      const task = uploadTasks.find(t => t.file.name === file.name);
      if (task) {
        videoUploadService.cancelUpload(task.id);
      }
    }
    setFiles(prevFiles => prevFiles.filter(file => file.id !== id));
  };

  // 重试上传
  const retryUpload = async (fileId: string) => {
    const file = files.find(f => f.id === fileId);
    if (!file) return;
    
    // 重置文件状态为等待上传
    setFiles(prevFiles =>
      prevFiles.map(item =>
        item.id === fileId ? { ...item, status: 'waiting', progress: 0, error: undefined } : item
      )
    );
    
    // 重新上传
    await uploadFile(file);
  };

  // 播放视频
  const playVideo = (filename: string, originalName?: string) => {
    // 使用后端静态文件服务
    const videoUrl = `http://localhost:8000/uploads/videos/${filename}`;
    setCurrentVideo({
      url: videoUrl,
      title: originalName || filename
    });
    setIsPlayerOpen(true);
  };

  // 关闭播放器
  const closePlayer = () => {
    setIsPlayerOpen(false);
    setCurrentVideo(null);
  };
  
  // 编辑文件创建时间
  const editFileTime = (file: any) => {
    setEditingFile(file);
    // 如果文件有创建时间，设置为默认值
    if (file.file_created_at) {
      const date = new Date(file.file_created_at * 1000);
      const localDateTime = date.toISOString().slice(0, 16);
      setCustomTime(localDateTime);
    } else {
      // 默认设置为当前时间
      const now = new Date();
      const localDateTime = now.toISOString().slice(0, 16);
      setCustomTime(localDateTime);
    }
    setShowTimeEditor(true);
  };
  
  // 保存自定义创建时间
  const saveCustomTime = async () => {
    if (!editingFile || !customTime) return;
    
    try {
      const customDate = new Date(customTime);
      const timestamp = Math.floor(customDate.getTime() / 1000);
      
      // 调用API更新文件创建时间
      const response = await fetch(`http://localhost:8000/api/v1/files/update-time/${editingFile.saved_name}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          file_created_at: timestamp
        })
      });
      
      if (response.ok) {
        showNotification('文件创建时间已更新', 'success');
        // 刷新文件列表
        fetchRecentFiles();
      } else {
        showNotification('更新失败', 'error');
      }
    } catch (error) {
      console.error('更新文件时间失败:', error);
      showNotification('更新失败', 'error');
    }
    
    setShowTimeEditor(false);
    setEditingFile(null);
  };
  
  // 取消编辑
  const cancelTimeEdit = () => {
    setShowTimeEditor(false);
    setEditingFile(null);
    setCustomTime('');
  };

  // 删除文件
  const deleteRecentFile = async (filename: string) => {
    if (!confirm(`确定要删除文件 "${filename}" 吗？`)) {
      return;
    }
    
    try {
      const response = await fetch(`/api/v1/files/files/${encodeURIComponent(filename)}`, {
        method: 'DELETE',
        mode: 'cors',
        credentials: 'omit'
      });
      
      if (response.ok) {
        showNotification('success', `文件 "${filename}" 已删除`);
        await loadRecentFiles(); // 刷新列表
      } else {
        throw new Error('删除失败');
      }
    } catch (error) {
      console.error('删除文件失败:', error);
      showNotification('error', `删除文件失败: ${filename}`);
    }
  };

  // 分析视频
  const analyzeVideo = (filename: string) => {
    showNotification('info', `开始分析视频: ${filename}`);
    // TODO: 实现视频分析功能
    console.log('分析视频:', filename);
  };

  const triggerFileInput = () => {
    fileInputRef.current?.click();
  };

  useEffect(() => {
    // 页面加载时获取最近文件列表
    loadRecentFiles();
  }, []);

  useEffect(() => {
    // 计算上传速度和剩余时间
    if (isUploading) {
      const interval = setInterval(() => {
        const uploadingFiles = files.filter(f => f.status === 'uploading');
        if (uploadingFiles.length > 0) {
          const avgSpeed = uploadingFiles.reduce((sum, file) => sum + file.progress, 0) / uploadingFiles.length;
          setUploadSpeed(`${Math.round(avgSpeed * 10)} KB/s`);
          
          const remaining = 100 - avgSpeed;
          setRemainingTime(`${Math.round(remaining / 10)}秒`);
        }
      }, 1000);
      
      return () => clearInterval(interval);
    }
  }, [isUploading, files]);

  return (
    <div className="space-y-6">
      {/* 通知栏 */}
      {notification && (
        <div className={`fixed top-4 right-4 z-50 p-4 rounded-lg shadow-lg max-w-md ${
          notification.type === 'success' ? 'bg-green-100 border border-green-400 text-green-700' :
          notification.type === 'error' ? 'bg-red-100 border border-red-400 text-red-700' :
          'bg-blue-100 border border-blue-400 text-blue-700'
        }`}>
          <div className="flex items-center">
            <i className={`fas ${
              notification.type === 'success' ? 'fa-check-circle' :
              notification.type === 'error' ? 'fa-exclamation-circle' :
              'fa-info-circle'
            } mr-2`}></i>
            <span className="text-sm">{notification.message}</span>
            <button 
              onClick={() => setNotification(null)}
              className="ml-auto text-gray-500 hover:text-gray-700"
            >
              <i className="fas fa-times"></i>
            </button>
          </div>
        </div>
      )}
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-800">视频上传中心</h1>
        <div className="text-sm text-gray-500">
          支持格式：MP4, AVI, MOV, WMV, FLV, WebM, MKV
        </div>
      </div>
      
      {/* 上传区域 */}
      <div
        className={`border-2 border-dashed rounded-lg p-12 text-center transition-colors ${
          isDragging ? 'border-blue-500 bg-blue-50' : 'border-gray-300 bg-white'
        }`}
        onDragEnter={handleDragEnter}
        onDragOver={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <i className="fas fa-cloud-upload-alt text-5xl text-blue-500 mb-4"></i>
        <p className="text-lg text-gray-600 mb-4">
          拖拽文件到此处或点击选择文件
        </p>
        <p className="text-sm text-gray-500 mb-6">
          最大文件大小：500MB，支持批量上传
        </p>
        <button
          className="btn-primary"
          onClick={triggerFileInput}
        >
          <i className="fas fa-plus mr-2"></i>
          选择文件
        </button>
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileChange}
          className="hidden"
          multiple
          accept="video/*"
        />
      </div>
      
      {/* 上传控制区域 */}
      {files.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex justify-between items-center mb-4">
            <div className="flex items-center space-x-6">
              <span className="text-gray-700">总进度: {totalProgress}%</span>
              <span className="text-gray-500">速度: {uploadSpeed}</span>
              <span className="text-gray-500">剩余时间: {remainingTime}</span>
            </div>
            <div className="flex space-x-2">
              <button
                className="btn-primary"
                onClick={handleUpload}
                disabled={isUploading || files.length === 0}
              >
                {isUploading ? (
                  <>
                    <i className="fas fa-spinner fa-spin mr-2"></i>
                    上传中...
                  </>
                ) : (
                  <>
                    <i className="fas fa-upload mr-2"></i>
                    开始上传
                  </>
                )}
              </button>
              {/* 移除暂停上传按钮 */}
              <button
                className="px-4 py-2 text-red-600 border border-red-300 rounded-button hover:bg-red-50"
                onClick={() => setFiles([])}
                disabled={isUploading}
              >
                <i className="fas fa-trash mr-2"></i>
                清空列表
              </button>
            </div>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2.5">
            <div
              className="bg-blue-600 h-2.5 rounded-full transition-all duration-300"
              style={{ width: `${totalProgress}%` }}
            ></div>
          </div>
        </div>
      )}
      
      {/* 文件列表 */}
      <div className="bg-white rounded-lg shadow-sm overflow-hidden">
        {files.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <i className="fas fa-folder-open text-4xl mb-4"></i>
            <p className="text-lg">暂无待上传文件</p>
            <p className="text-sm mt-2">请选择或拖拽视频文件到上方区域</p>
          </div>
        ) : (
          <>
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-800">
                文件列表 ({files.length} 个文件)
              </h3>
            </div>
            <ul className="divide-y divide-gray-200">
              {files.map(file => (
                <li key={file.id} className="p-6 hover:bg-gray-50 transition-colors">
                  <div className="flex items-center">
                    {/* 缩略图 */}
                    <div className="relative w-24 h-16 bg-gray-200 rounded overflow-hidden mr-4 flex-shrink-0">
                      <video className="w-full h-full object-cover">
                        <source src={file.previewUrl} type="video/mp4" />
                      </video>
                      <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-30">
                        <i className="fas fa-play text-white text-xl"></i>
                      </div>
                    </div>
                    
                    {/* 文件信息 */}
                    <div className="flex-1 min-w-0 mr-4">
                      <p className="text-sm font-medium text-gray-900 truncate">{file.name}</p>
                      <p className="text-sm text-gray-500">{file.size}</p>
                      <div className="mt-2">
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div
                            className={`h-2 rounded-full transition-all duration-300 ${
                              file.status === 'completed'
                                ? 'bg-green-500'
                                : file.status === 'failed'
                                ? 'bg-red-500'
                                : 'bg-blue-500'
                            }`}
                            style={{ width: `${file.progress}%` }}
                          ></div>
                        </div>
                        <div className="text-xs text-gray-500 mt-1 flex justify-between">
                          <span>{file.progress}%</span>
                          <span>
                            {file.status === 'completed' ? (
                              <span className="text-green-600">
                                <i className="fas fa-check-circle mr-1"></i> 上传完成
                              </span>
                            ) : file.status === 'failed' ? (
                              <span className="text-red-600">
                                <i className="fas fa-exclamation-circle mr-1"></i> 上传失败
                              </span>
                            ) : file.status === 'uploading' ? (
                              <span className="text-blue-600">
                                <i className="fas fa-spinner fa-spin mr-1"></i> 上传中...
                              </span>
                            ) : (
                              <span className="text-gray-500">
                                <i className="fas fa-clock mr-1"></i> 等待上传
                              </span>
                            )}
                          </span>
                        </div>
                      </div>
                    </div>
                    
                    {/* 操作按钮 */}
                    <div className="flex items-center space-x-2">
                      {file.status === 'failed' && (
                        <button
                          className="text-blue-600 hover:text-blue-800 text-sm px-2 py-1 rounded"
                          onClick={() => retryUpload(file.id)}
                        >
                          <i className="fas fa-redo mr-1"></i>
                          重试
                        </button>
                      )}
                      
                      <button
                        className="text-red-500 hover:text-red-700 transition-colors p-1"
                        onClick={() => removeFile(file.id)}
                        disabled={file.status === 'uploading'}
                        title="删除文件"
                      >
                        <i className="fas fa-trash"></i>
                      </button>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          </>
        )}
      </div>
      
      {/* 最近上传文件列表 */}
      {recentFiles.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm overflow-hidden mt-6">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-800">
              <i className="fas fa-history mr-2"></i>
              最近上传的文件 ({recentFiles.length})
            </h3>
          </div>
          <div className="divide-y divide-gray-200">
            {recentFiles.map((file, index) => (
              <div key={index} className="p-4 hover:bg-gray-50 transition-colors">
                <div className="flex items-center justify-between">
                  <div className="flex items-center flex-1">
                    <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mr-4">
                      <i className="fas fa-video text-blue-600 text-lg"></i>
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {file.name}
                      </p>
                      <p className="text-sm text-gray-500">
                         {file.duration && (
                           <span>时长: {Math.floor(file.duration / 60)}:{Math.floor(file.duration % 60).toString().padStart(2, '0')}</span>
                         )}
                         {formatFileSize(file.size) && (
                           <span> • 尺寸: {formatFileSize(file.size)}</span>
                         )}
                         {file.width && file.height && (
                           <span> • 分辨率: {file.width}×{file.height}</span>
                         )}
                         {file.format_name && (
                           <span> • 格式: {file.format_name.toUpperCase()}</span>
                         )}
                         {file.aspect_ratio && (
                           <span> • 宽高比: {file.aspect_ratio}</span>
                         )}
                         {file.video_ratio && (
                           <span> • 比例: {file.video_ratio}</span>
                         )}
                         {file.frame_rate && (
                           <span> • 帧率: {file.frame_rate}</span>
                         )}
                         {file.bit_rate && (
                           <span> • 比特率: {(file.bit_rate / 1000000).toFixed(1)} Mbps</span>
                         )}
                         {file.channels && (
                           <span> • 音频: {file.channels}声道</span>
                         )}
                         {file.sample_rate && (
                           <span> • 采样率: {(file.sample_rate / 1000).toFixed(1)}kHz</span>
                         )}
                       </p>
                       {file.file_created_at && (
                          <p className="text-xs text-gray-400 mt-1">
                            文件创建时间: {new Date(file.file_created_at * 1000).toLocaleString('zh-CN', {
                              year: 'numeric',
                              month: '2-digit', 
                              day: '2-digit',
                              hour: '2-digit',
                              minute: '2-digit',
                              second: '2-digit',
                              hour12: false
                            }).replace(/\//g, '/').replace(/,/g, '')}
                          </p>
                        )}
                        {file.upload_time && (
                          <p className="text-xs text-gray-400 mt-1">
                            文件上传时间: {new Date(file.upload_time * 1000).toLocaleString('zh-CN', {
                              year: 'numeric',
                              month: '2-digit',
                              day: '2-digit', 
                              hour: '2-digit',
                              minute: '2-digit',
                              second: '2-digit',
                              hour12: false
                            }).replace(/\//g, '/').replace(/,/g, '')}
                          </p>
                        )}
                    </div>
                  </div>
                  <div className="flex items-center space-x-2 ml-4">
                    <button
                       className="text-green-600 hover:text-green-800 text-sm px-3 py-1 rounded border border-green-300 hover:bg-green-50"
                       onClick={() => playVideo(file.saved_name || file.saved_filename, file.name)}
                       title="播放视频"
                     >
                       <i className="fas fa-play mr-1"></i>
                       播放
                     </button>
                    <button
                      className="text-blue-600 hover:text-blue-800 text-sm px-3 py-1 rounded border border-blue-300 hover:bg-blue-50"
                      onClick={() => analyzeVideo(file.name)}
                      title="分析视频"
                    >
                      <i className="fas fa-chart-line mr-1"></i>
                      分析
                    </button>

                    <button
                      className="text-red-600 hover:text-red-800 text-sm px-3 py-1 rounded border border-red-300 hover:bg-red-50"
                      onClick={() => deleteRecentFile(file.name)}
                      title="删除文件"
                    >
                      <i className="fas fa-trash mr-1"></i>
                      删除
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {/* 视频播放器弹窗 */}
      {currentVideo && (
        <VideoPlayer
          isOpen={isPlayerOpen}
          onClose={closePlayer}
          videoUrl={currentVideo.url}
          videoTitle={currentVideo.title}
        />
      )}
      
      {/* 时间编辑弹窗 */}
      {showTimeEditor && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-96 max-w-full mx-4">
            <h3 className="text-lg font-semibold mb-4">编辑文件创建时间</h3>
            
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                文件名: {editingFile?.name}
              </label>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                创建时间:
              </label>
              <input
                type="datetime-local"
                value={customTime}
                onChange={(e) => setCustomTime(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            
            <div className="flex justify-end space-x-3">
              <button
                onClick={cancelTimeEdit}
                className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
              >
                取消
              </button>
              <button
                onClick={saveCustomTime}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                保存
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default VideoUpload;