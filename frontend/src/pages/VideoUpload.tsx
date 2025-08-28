import React, { useState, useRef, useEffect } from 'react';
import { FileItem } from '@/types';

const VideoUpload: React.FC = () => {
  const [files, setFiles] = useState<FileItem[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [totalProgress, setTotalProgress] = useState(0);
  const [uploadSpeed, setUploadSpeed] = useState('0 KB/s');
  const [remainingTime, setRemainingTime] = useState('--');
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // 模拟上传函数
  const simulateUpload = (fileItem: FileItem) => {
    return new Promise<void>((resolve, reject) => {
      let progress = 0;
      const interval = setInterval(() => {
        progress += Math.random() * 10;
        if (progress >= 100) {
          progress = 100;
          clearInterval(interval);
          resolve();
        }
        setFiles(prevFiles =>
          prevFiles.map(item =>
            item.id === fileItem.id
              ? { ...item, progress, status: progress === 100 ? 'completed' : 'uploading' }
              : item
          )
        );
      }, 300);
    });
  };

  const handleUpload = async () => {
    if (files.length === 0) return;
    
    setIsUploading(true);
    setTotalProgress(0);
    
    const uploadPromises = files
      .filter(file => file.status === 'waiting')
      .map(async fileItem => {
        try {
          await simulateUpload(fileItem);
        } catch (error) {
          setFiles(prevFiles =>
            prevFiles.map(item =>
              item.id === fileItem.id ? { ...item, status: 'failed' } : item
            )
          );
        }
      });

    await Promise.all(uploadPromises);
    setIsUploading(false);
    
    // 更新总进度
    const completedCount = files.filter(f => f.status === 'completed').length;
    setTotalProgress(Math.round((completedCount / files.length) * 100));
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      addFiles(Array.from(e.target.files));
    }
  };

  const addFiles = (newFiles: File[]) => {
    const newItems = newFiles.map(file => ({
      id: `${file.name}-${file.size}-${Date.now()}`,
      name: file.name,
      size: formatFileSize(file.size),
      progress: 0,
      status: 'waiting' as const,
      previewUrl: URL.createObjectURL(file),
      file,
    }));

    setFiles(prev => [...prev, ...newItems]);
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
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
    setFiles(prevFiles => prevFiles.filter(file => file.id !== id));
  };

  const triggerFileInput = () => {
    fileInputRef.current?.click();
  };

  const clearCompleted = () => {
    setFiles(prevFiles => prevFiles.filter(file => file.status !== 'completed'));
  };

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
      <div className="bg-white shadow-sm rounded-lg p-6">
        <h1 className="text-2xl font-bold text-gray-800 mb-6">视频上传中心</h1>
        
        {/* 上传区域 */}
        <div
          className={`border-2 border-dashed rounded-lg p-12 mb-8 text-center transition-colors ${
            isDragging ? 'border-blue-500 bg-blue-50' : 'border-gray-300'
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
          <button
            className="rounded-button whitespace-nowrap bg-blue-600 text-white px-6 py-2 hover:bg-blue-700 transition-colors"
            onClick={triggerFileInput}
          >
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
          <p className="text-sm text-gray-500 mt-2">
            支持 MP4, AVI, MOV, WMV 等视频格式，单个文件最大 2GB
          </p>
        </div>
        
        {/* 上传控制区域 */}
        <div className="bg-gray-50 rounded-lg p-6 mb-6">
          <div className="flex justify-between items-center mb-4">
            <div className="flex items-center space-x-6">
              <span className="text-gray-700">总进度: {totalProgress}%</span>
              <span className="text-gray-500">速度: {uploadSpeed}</span>
              <span className="text-gray-500">剩余时间: {remainingTime}</span>
            </div>
            <div className="flex space-x-2">
              <button
                className="rounded-button whitespace-nowrap bg-green-600 text-white px-4 py-2 hover:bg-green-700 transition-colors disabled:opacity-50"
                onClick={handleUpload}
                disabled={isUploading || files.length === 0}
              >
                {isUploading ? (
                  <>
                    <i className="fas fa-spinner animate-spin mr-2"></i>
                    上传中...
                  </>
                ) : (
                  <>
                    <i className="fas fa-upload mr-2"></i>
                    开始上传
                  </>
                )}
              </button>
              <button
                className="rounded-button whitespace-nowrap bg-gray-600 text-white px-4 py-2 hover:bg-gray-700 transition-colors disabled:opacity-50"
                disabled={!isUploading}
              >
                <i className="fas fa-pause mr-2"></i>
                暂停上传
              </button>
              <button
                className="rounded-button whitespace-nowrap bg-red-600 text-white px-4 py-2 hover:bg-red-700 transition-colors"
                onClick={clearCompleted}
              >
                <i className="fas fa-trash mr-2"></i>
                清空已完成
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
        
        {/* 文件列表 */}
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          {files.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <i className="fas fa-folder-open text-4xl mb-4"></i>
              <p>暂无待上传文件</p>
            </div>
          ) : (
            <>
              <div className="bg-gray-50 px-6 py-3 border-b border-gray-200">
                <h3 className="text-sm font-medium text-gray-700">
                  文件列表 ({files.length} 个文件)
                </h3>
              </div>
              <ul className="divide-y divide-gray-200">
                {files.map(file => (
                  <li key={file.id} className="p-4 hover:bg-gray-50 transition-colors">
                    <div className="flex items-center">
                      {/* 缩略图 */}
                      <div className="relative w-24 h-16 bg-gray-200 rounded overflow-hidden mr-4 flex-shrink-0">
                        <video className="w-full h-full object-cover">
                          <source src={file.previewUrl} type="video/mp4" />
                        </video>
                        <div className="absolute inset-0 flex items-center justify-center">
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
                        </div>
                      </div>
                      
                      {/* 状态和操作 */}
                      <div className="flex items-center space-x-4">
                        <div className="text-right">
                          <div className="text-xs text-gray-500 mb-1">
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
                                <i className="fas fa-spinner animate-spin mr-1"></i> 上传中...
                              </span>
                            ) : (
                              <span className="text-gray-600">
                                <i className="fas fa-clock mr-1"></i> 等待上传
                              </span>
                            )}
                          </div>
                          <div className="text-xs text-gray-400">
                            {file.progress}%
                          </div>
                        </div>
                        
                        <button
                          className="text-red-500 hover:text-red-700 transition-colors p-2"
                          onClick={() => removeFile(file.id)}
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
      </div>
    </div>
  );
};

export default VideoUpload;