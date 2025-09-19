import React, { useState, useEffect, useRef } from 'react';
import { DownloadTask } from '../types';
import { detectPlatform, isValidUrl, generateId } from '../utils';
import { SUPPORTED_PLATFORMS } from '../config';
import { videoDownloadApi, VideoInfo, SupportedPlatform } from '../services/videoDownloadApi';
import { websocketService, TaskUpdateData, DownloadCompleteData, DownloadFailedData } from '../services/websocketService';

const VideoDownload: React.FC = () => {
  const [videoUrl, setVideoUrl] = useState('');
  const [platform, setPlatform] = useState('');
  const [videoInfo, setVideoInfo] = useState<any>(null);
  const [downloadOptions, setDownloadOptions] = useState({
    format: 'MP4',
    quality: '1080p',
    content: ['video'],
    subtitles: false,
    danmaku: false
  });
  const [downloadQueue, setDownloadQueue] = useState<DownloadTask[]>([]);
  const [currentDownload, setCurrentDownload] = useState<DownloadTask | null>(null);
  const [downloadProgress, setDownloadProgress] = useState(0);
  const [downloadSpeed, setDownloadSpeed] = useState('0 KB/s');
  const [remainingTime, setRemainingTime] = useState('--');
  const [history, setHistory] = useState<any[]>([]);
  const [activeTab, setActiveTab] = useState('info');
  const [notification, setNotification] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [settings, setSettings] = useState({
    downloadPath: '~/Downloads',
    maxConcurrent: 3,
    notifications: true,
    retryCount: 3
  });
  const [supportedPlatforms, setSupportedPlatforms] = useState<SupportedPlatform[]>([]);
  
  const videoRef = useRef<HTMLVideoElement>(null);
  const [wsConnected, setWsConnected] = useState(false);
  const [currentUser, setCurrentUser] = useState<any>(null);

  const formats = ['MP4', 'WebM', 'MKV', 'AVI', 'MOV'];
  const qualities = ['144p', '240p', '360p', '480p', '720p', '1080p', '2K', '4K'];
  
  // 加载支持的平台列表
  useEffect(() => {
    const loadSupportedPlatforms = async () => {
      try {
        const response = await videoDownloadApi.getSupportedPlatforms();
        setSupportedPlatforms(response.platforms);
      } catch (error) {
        console.error('Failed to load supported platforms:', error);
        // 使用默认平台列表作为备选
        setSupportedPlatforms([
          { name: 'douyin', display_name: '抖音', icon: 'fab fa-tiktok', color: 'text-red-500', supported_features: ['video', 'image'] },
          { name: 'tiktok', display_name: 'TikTok', icon: 'fab fa-tiktok', color: 'text-black', supported_features: ['video'] },
          { name: 'bilibili', display_name: 'B站', icon: 'fas fa-video', color: 'text-blue-500', supported_features: ['video'] },
          { name: 'xiaohongshu', display_name: '小红书', icon: 'fas fa-book', color: 'text-pink-500', supported_features: ['video', 'image'] },
          { name: 'kuaishou', display_name: '快手', icon: 'fas fa-play', color: 'text-yellow-500', supported_features: ['video'] },
          { name: 'weixin', display_name: '微信视频号', icon: 'fab fa-weixin', color: 'text-green-500', supported_features: ['video'] }
        ]);
      }
    };
    
    loadSupportedPlatforms();
  }, []);
  
  // 单独的useEffect处理WebSocket连接
  useEffect(() => {
    // 初始化WebSocket连接
    initWebSocket();
    
    // 清理函数
    return () => {
      websocketService.disconnect();
    };
  }, []); // 空依赖数组，只在组件挂载时执行一次
  
  // 获取当前用户信息（临时实现）
  const getCurrentUser = () => {
    // 临时模拟用户数据，实际应该从认证系统获取
    // 使用现有的测试用户ID
    return {
      id: '2', // 使用现有测试用户的ID
      username: 'testuser',
      email: 'test@example.com'
    };
  };
  
  // 初始化WebSocket连接
  const initWebSocket = async () => {
    try {
      // 获取当前用户信息
      const user = getCurrentUser();
      if (!user) {
        console.warn('用户未登录，跳过WebSocket连接');
        return;
      }
      
      setCurrentUser(user);
      
      // 建立WebSocket连接
      await websocketService.connect(user.id);
      setWsConnected(true);
      
      // 设置事件监听器
      setupWebSocketListeners();
      
    } catch (error) {
      console.error('WebSocket连接失败:', error);
      setWsConnected(false);
      // WebSocket连接失败不应该阻止页面使用，继续使用轮询模式
    }
  };
  
  // 设置WebSocket事件监听器
  const setupWebSocketListeners = () => {
    // 连接建立
    websocketService.on('connected', (data) => {
      console.log('WebSocket连接已建立:', data);
      setWsConnected(true);
    });
    
    // 连接断开
    websocketService.on('disconnected', (data) => {
      console.log('WebSocket连接已断开:', data);
      setWsConnected(false);
    });
    
    // 任务更新
    websocketService.on('task_update', (data: TaskUpdateData) => {
      console.log('收到任务更新:', data);
      
      // 更新下载队列中的任务状态
      setDownloadQueue(prev => prev.map(task => 
        task.id === data.task_id ? {
          ...task,
          status: data.status as any,
          progress: data.progress,
          updated_at: data.updated_at
        } : task
      ));
      
      // 更新当前下载任务
      if (currentDownload && currentDownload.id === data.task_id) {
        setCurrentDownload({
          ...currentDownload,
          status: data.status as any,
          progress: data.progress
        });
        setDownloadProgress(data.progress);
      }
    });
    
    // 下载完成
    websocketService.on('download_complete', (data: DownloadCompleteData) => {
      console.log('下载完成:', data);
      
      setNotification(`${data.title} 下载完成`);
      
      // 添加到历史记录
      setHistory(prev => [{
        id: data.task_id,
        title: data.title,
        platform: data.platform,
        thumbnail: videoInfo?.thumbnail || '',
        downloadTime: new Date(data.completed_at).toLocaleString(),
        path: data.file_path
      }, ...prev]);
      
      // 清除当前下载任务
      if (currentDownload && currentDownload.id === data.task_id) {
        setCurrentDownload(null);
        setDownloadProgress(0);
      }
    });
    
    // 下载失败
    websocketService.on('download_failed', (data: DownloadFailedData) => {
      console.log('下载失败:', data);
      
      setNotification(`${data.title} 下载失败: ${data.error_message}`);
      
      // 清除当前下载任务
      if (currentDownload && currentDownload.id === data.task_id) {
        setCurrentDownload(null);
        setDownloadProgress(0);
      }
    });
    
    // 订阅确认
    websocketService.on('subscription_confirmed', (data) => {
      console.log('任务订阅确认:', data);
    });
    
    // 错误处理
    websocketService.on('error', (data) => {
      console.error('WebSocket错误:', data);
      setNotification('WebSocket连接出现错误');
    });
  };
  
  const parseVideo = async () => {
    if (!videoUrl) {
      setNotification('请输入视频链接');
      return;
    }

    if (!isValidUrl(videoUrl)) {
      setNotification('请输入有效的视频链接');
      return;
    }

    const detectedPlatform = detectPlatform(videoUrl);
    setPlatform(detectedPlatform);
    setIsAnalyzing(true);
    setNotification(`正在解析 ${detectedPlatform} 视频...`);

    try {
      const videoInfo = await videoDownloadApi.parseVideo({
        url: videoUrl,
        minimal: false
      });
      
      // 转换API响应为组件所需格式
      setVideoInfo({
        title: videoInfo.title,
        subtitle: videoInfo.type === 'video' ? '视频内容' : '图片内容',
        author: {
          name: videoInfo.author.name,
          avatar: videoInfo.author.avatar || 'https://via.placeholder.com/40x40',
          followers: videoInfo.author.followers || '未知'
        },
        publishTime: videoInfo.create_time || videoInfo.publish_time || new Date().toISOString(),
        duration: videoInfo.duration ? `${Math.floor(videoInfo.duration / 60)}:${(videoInfo.duration % 60).toString().padStart(2, '0')}` : '未知',
        views: videoInfo.statistics?.play_count?.toString() || videoInfo.statistics?.views || '未知',
        keywords: videoInfo.keywords || [videoInfo.platform],
        thumbnail: videoInfo.thumbnail,
        videoUrl: videoInfo.video_url || videoUrl,
        platform: videoInfo.platform,
        type: videoInfo.type,
        images: videoInfo.images
      });
      
      setNotification('视频解析成功');
      setActiveTab('info');
    } catch (error: any) {
      console.error('Video parsing failed:', error);
      setNotification(`解析失败: ${error.message || '未知错误'}`);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const startDownload = async () => {
    if (!videoInfo) return;

    try {
      setNotification('正在创建下载任务...');
      
      const response = await videoDownloadApi.createDownloadTask({
        url: videoUrl,
        format: downloadOptions.format.toLowerCase(),
        quality: downloadOptions.quality,
        download_video: downloadOptions.content.includes('video'),
        download_audio: downloadOptions.content.includes('audio') || downloadOptions.content.includes('videoAndAudio'),
        download_subtitles: downloadOptions.subtitles,
        download_thumbnail: true
      });
      
      const newDownload: DownloadTask = {
        id: response.task_id,
        url: videoUrl,
        title: response.title,
        platform: response.platform as any,
        status: 'pending',
        progress: 0,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      };

      setDownloadQueue([...downloadQueue, newDownload]);
      setNotification('下载任务创建成功');
      
      // 订阅WebSocket任务更新
      if (wsConnected) {
        websocketService.subscribeTask(response.task_id);
      } else {
        // 如果WebSocket未连接，使用轮询方式监控进度
        monitorDownloadProgress(response.task_id);
      }
      
    } catch (error: any) {
      console.error('Failed to create download task:', error);
      setNotification(`创建下载任务失败: ${error.message || '未知错误'}`);
    }
  };
  
  const monitorDownloadProgress = async (taskId: string) => {
    const interval = setInterval(async () => {
      try {
        const task = await videoDownloadApi.getDownloadTask(taskId);
        
        // 更新队列中的任务状态
        setDownloadQueue(prev => prev.map(t => 
          t.id === taskId ? {
            ...t,
            status: task.status,
            progress: task.progress,
            updated_at: task.updated_at
          } : t
        ));
        
        // 如果任务完成或失败，停止监控
        if (['completed', 'failed', 'cancelled'].includes(task.status)) {
          clearInterval(interval);
          
          if (task.status === 'completed') {
            setNotification(`${task.title} 下载完成`);
            // 添加到历史记录
            setHistory(prev => [{
              id: task.id,
              title: task.title,
              platform: task.platform,
              thumbnail: videoInfo?.thumbnail || '',
              downloadTime: new Date().toLocaleString(),
              path: task.file_path || ''
            }, ...prev]);
          } else if (task.status === 'failed') {
            setNotification(`${task.title} 下载失败: ${task.error_message || '未知错误'}`);
          }
        }
        
      } catch (error) {
        console.error('Failed to get task status:', error);
        clearInterval(interval);
      }
    }, 1000);
  };

  const processDownloadQueue = (queue: DownloadTask[]) => {
    const waitingTasks = queue.filter(task => task.status === 'pending');
    if (waitingTasks.length === 0) return;

    const task = waitingTasks[0];
    const updatedTask = { ...task, status: 'downloading' as const };
    setCurrentDownload(updatedTask);
    setDownloadQueue(queue.map(t => t.id === task.id ? updatedTask : t));

    let progress = 0;
    const interval = setInterval(() => {
      progress += Math.random() * 5;
      if (progress >= 100) {
        progress = 100;
        clearInterval(interval);
        
        const completedTask = { ...updatedTask, status: 'completed' as const, progress: 100 };
        const updatedQueue = queue.map(t => t.id === task.id ? completedTask : t);
        
        setDownloadQueue(updatedQueue);
        setCurrentDownload(null);
        setDownloadProgress(0);
        setNotification(`${task.title} 下载完成`);
        
        // 添加到历史记录
        setHistory([{
          id: task.id,
          title: task.title,
          platform: task.platform,
          thumbnail: videoInfo?.thumbnail,
          downloadTime: new Date().toLocaleString(),
          path: `~/Downloads/${task.title}.${downloadOptions.format.toLowerCase()}`
        }, ...history]);
        
        // 处理下一个任务
        processDownloadQueue(updatedQueue);
      } else {
        setDownloadProgress(progress);
        setDownloadSpeed(`${Math.floor(Math.random() * 2000) + 500} KB/s`);
        setRemainingTime(`${Math.floor((100 - progress) / 5)}秒`);
        
        setDownloadQueue(queue.map(t => 
          t.id === task.id ? { ...t, progress } : t
        ));
      }
    }, 500);
  };

  const handlePause = async (id: string) => {
    try {
      await videoDownloadApi.cancelDownloadTask(id);
      setDownloadQueue(downloadQueue.map(task =>
        task.id === id ? { ...task, status: 'cancelled' } : task
      ));
      setNotification('任务已暂停');
    } catch (error: any) {
      console.error('Failed to pause task:', error);
      setNotification(`暂停失败: ${error.message || '未知错误'}`);
    }
  };

  const handleResume = async (id: string) => {
    try {
      await videoDownloadApi.retryDownloadTask(id);
      setDownloadQueue(downloadQueue.map(task =>
        task.id === id ? { ...task, status: 'pending', progress: 0 } : task
      ));
      // 重新开始监控进度
      monitorDownloadProgress(id);
      setNotification('任务已恢复');
    } catch (error: any) {
      console.error('Failed to resume task:', error);
      setNotification(`恢复失败: ${error.message || '未知错误'}`);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await videoDownloadApi.deleteDownloadTask(id);
      const newQueue = downloadQueue.filter(task => task.id !== id);
      setDownloadQueue(newQueue);
      if (currentDownload && currentDownload.id === id) {
        setCurrentDownload(null);
        setDownloadProgress(0);
      }
      setNotification('任务已删除');
    } catch (error: any) {
      console.error('Failed to delete task:', error);
      setNotification(`删除失败: ${error.message || '未知错误'}`);
    }
  };

  const handleRetry = async (id: string) => {
    try {
      await videoDownloadApi.retryDownloadTask(id);
      setDownloadQueue(downloadQueue.map(task =>
        task.id === id ? { ...task, status: 'pending', progress: 0 } : task
      ));
      // 重新开始监控进度
      monitorDownloadProgress(id);
      setNotification('任务已重新开始');
    } catch (error: any) {
      console.error('Failed to retry task:', error);
      setNotification(`重试失败: ${error.message || '未知错误'}`);
    }
  };

  const handlePaste = async () => {
    try {
      const text = await navigator.clipboard.readText();
      setVideoUrl(text);
    } catch (err) {
      setNotification('无法访问剪贴板');
    }
  };

  const handleClear = () => {
    setVideoUrl('');
    setPlatform('');
    setVideoInfo(null);
    setActiveTab('info');
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div className="flex items-center space-x-4">
          <h1 className="text-2xl font-bold text-gray-800">视频下载助手</h1>
          
          {/* WebSocket连接状态指示器 */}
          <div className="flex items-center space-x-2">
            <div className={`w-2 h-2 rounded-full ${wsConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
            <span className={`text-sm ${wsConnected ? 'text-green-600' : 'text-red-600'}`}>
              {wsConnected ? '实时连接' : '离线模式'}
            </span>
            {currentUser && (
              <span className="text-sm text-gray-500 ml-2">
                用户: {currentUser.username}
              </span>
            )}
          </div>
        </div>
        <div className="text-sm text-gray-500">
          支持平台：抖音、快手、B站、小红书、视频号、TikTok等
        </div>
      </div>

      {/* 通知栏 */}
      {notification && (
        <div className="p-3 bg-blue-100 text-blue-800 rounded-lg flex justify-between items-center">
          <span>{notification}</span>
          <button onClick={() => setNotification('')} className="text-blue-800 hover:text-blue-900">
            <i className="fas fa-times"></i>
          </button>
        </div>
      )}

      {/* 视频链接输入区 */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="flex items-center space-x-2 mb-4">
          <i className="fas fa-link text-blue-600"></i>
          <h2 className="text-lg font-semibold">视频链接</h2>
        </div>
        <div className="flex space-x-2 mb-4">
          <div className="flex-1 relative">
            <input
              type="text"
              value={videoUrl}
              onChange={(e) => setVideoUrl(e.target.value)}
              placeholder="粘贴视频链接 (抖音/快手/B站/小红书/视频号/TikTok等)"
              className="input-field pr-20"
            />
            {videoUrl && (
              <button
                onClick={handleClear}
                className="absolute right-12 top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-gray-700"
              >
                <i className="fas fa-times"></i>
              </button>
            )}
            <button
              onClick={handlePaste}
              className="absolute right-3 top-1/2 transform -translate-y-1/2 text-blue-600 hover:text-blue-800"
            >
              <i className="fas fa-paste"></i>
            </button>
          </div>
          <button
            onClick={parseVideo}
            disabled={isAnalyzing}
            className="btn-primary"
          >
            {isAnalyzing ? (
              <>
                <i className="fas fa-spinner fa-spin mr-2"></i>
                解析中...
              </>
            ) : (
              <>
                <i className="fas fa-search mr-2"></i>
                开始解析
              </>
            )}
          </button>
        </div>
        
        {/* 平台图标 */}
        <div className="flex justify-center space-x-4">
          {supportedPlatforms.map((p) => (
            <div
              key={p.name}
              className={`flex flex-col items-center p-2 rounded-lg transition-colors ${
                platform === p.name ? 'bg-blue-100' : 'hover:bg-gray-100'
              }`}
            >
              <i className={`${p.icon} ${p.color} text-2xl mb-1`}></i>
              <span className="text-xs">{p.display_name}</span>
            </div>
          ))}
        </div>
      </div>

      {/* 视频信息和下载选项 */}
      {videoInfo && (
        <div className="bg-white rounded-lg shadow-sm overflow-hidden">
          {/* 标签页导航 */}
          <div className="border-b border-gray-200">
            <nav className="flex -mb-px">
              <button
                onClick={() => setActiveTab('info')}
                className={`py-4 px-6 text-center border-b-2 font-medium text-sm ${
                  activeTab === 'info'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <i className="fas fa-info-circle mr-2"></i>视频信息
              </button>
              <button
                onClick={() => setActiveTab('options')}
                className={`py-4 px-6 text-center border-b-2 font-medium text-sm ${
                  activeTab === 'options'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <i className="fas fa-cog mr-2"></i>下载选项
              </button>
            </nav>
          </div>

          <div className="p-6">
            {activeTab === 'info' && (
              <div className="flex space-x-6">
                <img
                  src={videoInfo.thumbnail}
                  alt={videoInfo.title}
                  className="w-48 h-32 object-cover rounded-lg"
                />
                <div className="flex-1">
                  <h3 className="text-lg font-semibold mb-2">{videoInfo.title}</h3>
                  <p className="text-gray-600 mb-3">{videoInfo.subtitle}</p>
                  <div className="grid grid-cols-2 gap-4 text-sm text-gray-500">
                    <div>作者：{videoInfo.author.name}</div>
                    <div>时长：{videoInfo.duration}</div>
                    <div>发布时间：{videoInfo.publishTime}</div>
                    <div>播放量：{videoInfo.views}</div>
                  </div>
                  <div className="mt-4">
                    <div className="flex flex-wrap gap-2">
                      {videoInfo.keywords.map((keyword: string, index: number) => (
                        <span key={index} className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded">
                          {keyword}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'options' && (
              <div className="space-y-6">
                <div className="grid grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">视频格式</label>
                    <select
                      value={downloadOptions.format}
                      onChange={(e) => setDownloadOptions({...downloadOptions, format: e.target.value})}
                      className="input-field"
                    >
                      {formats.map(format => (
                        <option key={format} value={format}>{format}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">视频质量</label>
                    <select
                      value={downloadOptions.quality}
                      onChange={(e) => setDownloadOptions({...downloadOptions, quality: e.target.value})}
                      className="input-field"
                    >
                      {qualities.map(quality => (
                        <option key={quality} value={quality}>{quality}</option>
                      ))}
                    </select>
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">下载内容</label>
                  <div className="space-y-2">
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={downloadOptions.content.includes('video')}
                        onChange={(e) => {
                          const content = e.target.checked
                            ? [...downloadOptions.content, 'video']
                            : downloadOptions.content.filter(c => c !== 'video');
                          setDownloadOptions({...downloadOptions, content});
                        }}
                        className="mr-2"
                      />
                      视频
                    </label>
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={downloadOptions.subtitles}
                        onChange={(e) => setDownloadOptions({...downloadOptions, subtitles: e.target.checked})}
                        className="mr-2"
                      />
                      字幕
                    </label>
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={downloadOptions.danmaku}
                        onChange={(e) => setDownloadOptions({...downloadOptions, danmaku: e.target.checked})}
                        className="mr-2"
                      />
                      弹幕
                    </label>
                  </div>
                </div>
              </div>
            )}
          </div>

          <div className="px-6 py-4 bg-gray-50 border-t border-gray-200">
            <button
              onClick={startDownload}
              className="btn-primary"
            >
              <i className="fas fa-download mr-2"></i>
              开始下载
            </button>
          </div>
        </div>
      )}

      {/* 下载队列 */}
      {downloadQueue.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-800">
              下载队列 ({downloadQueue.length} 个任务)
            </h3>
          </div>
          <div className="divide-y divide-gray-200">
            {downloadQueue.map(task => (
              <div key={task.id} className="p-6">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <h4 className="font-medium text-gray-800 truncate">{task.title}</h4>
                    <p className="text-sm text-gray-500">{task.platform} • {task.created_at}</p>
                    <div className="mt-2">
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className={`h-2 rounded-full transition-all duration-300 ${
                            task.status === 'completed'
                              ? 'bg-green-500'
                              : task.status === 'failed'
                              ? 'bg-red-500'
                              : 'bg-blue-500'
                          }`}
                          style={{ width: `${task.progress}%` }}
                        ></div>
                      </div>
                      <div className="flex justify-between text-xs text-gray-500 mt-1">
                        <span>{task.progress}%</span>
                        <span>
                          {task.status === 'completed' && '下载完成'}
                          {task.status === 'downloading' && `${downloadSpeed} • ${remainingTime}`}
                          {task.status === 'pending' && '等待中'}
                          {task.status === 'failed' && '下载失败'}
                        </span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2 ml-4">
                    {task.status === 'downloading' && (
                      <button
                        onClick={() => handlePause(task.id)}
                        className="text-yellow-600 hover:text-yellow-800"
                      >
                        <i className="fas fa-pause"></i>
                      </button>
                    )}
                    {task.status === 'failed' && (
                      <button
                        onClick={() => handleRetry(task.id)}
                        className="text-blue-600 hover:text-blue-800"
                      >
                        <i className="fas fa-redo"></i>
                      </button>
                    )}
                    <button
                      onClick={() => handleDelete(task.id)}
                      className="text-red-600 hover:text-red-800"
                    >
                      <i className="fas fa-trash"></i>
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default VideoDownload;