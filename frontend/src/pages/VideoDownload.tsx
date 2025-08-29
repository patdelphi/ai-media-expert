import React, { useState, useEffect } from 'react';
import { DownloadTask } from '../types';
import { detectPlatform, isValidUrl, generateId } from '../utils';
import { SUPPORTED_PLATFORMS } from '../config';

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

  const formats = ['MP4', 'WebM', 'MKV', 'AVI', 'MOV'];
  const qualities = ['144p', '240p', '360p', '480p', '720p', '1080p', '2K', '4K'];

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

    // 模拟API请求
    setTimeout(() => {
      setVideoInfo({
        title: '如何快速学会React开发 - 前端工程师必学框架',
        subtitle: '详细讲解React核心概念和实战技巧',
        author: {
          name: '前端开发指南',
          avatar: 'https://via.placeholder.com/40x40',
          followers: '12.8万'
        },
        publishTime: '2023-05-15 14:30',
        duration: '12:45',
        views: '256.3万',
        keywords: ['React', '前端开发', 'JavaScript', '教程'],
        thumbnail: 'https://via.placeholder.com/320x180',
        videoUrl: videoUrl
      });
      setNotification('视频解析成功');
      setActiveTab('info');
      setIsAnalyzing(false);
    }, 2000);
  };

  const startDownload = () => {
    if (!videoInfo) return;

    const newDownload: DownloadTask = {
      id: generateId(),
      url: videoUrl,
      title: videoInfo.title,
      platform: platform as any,
      status: 'pending',
      progress: 0,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };

    setDownloadQueue([...downloadQueue, newDownload]);
    setNotification('已添加到下载队列');

    // 模拟下载过程
    if (!currentDownload) {
      processDownloadQueue([...downloadQueue, newDownload]);
    }
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

  const handlePause = (id: string) => {
    setDownloadQueue(downloadQueue.map(task =>
      task.id === id ? { ...task, status: 'pending' } : task
    ));
    if (currentDownload && currentDownload.id === id) {
      setCurrentDownload(null);
      setDownloadProgress(0);
    }
    setNotification('下载已暂停');
  };

  const handleDelete = (id: string) => {
    const newQueue = downloadQueue.filter(task => task.id !== id);
    setDownloadQueue(newQueue);
    if (currentDownload && currentDownload.id === id) {
      setCurrentDownload(null);
      setDownloadProgress(0);
    }
    setNotification('任务已删除');
  };

  const handleRetry = (id: string) => {
    setDownloadQueue(downloadQueue.map(task =>
      task.id === id ? { ...task, status: 'pending', progress: 0 } : task
    ));
    processDownloadQueue(downloadQueue);
    setNotification('任务已重新开始');
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
        <h1 className="text-2xl font-bold text-gray-800">视频下载助手</h1>
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
          {SUPPORTED_PLATFORMS.map((p) => (
            <div
              key={p.key}
              className={`flex flex-col items-center p-2 rounded-lg transition-colors ${
                platform === p.name ? 'bg-blue-100' : 'hover:bg-gray-100'
              }`}
            >
              <i className={`${p.icon} text-2xl mb-1`} style={{ color: p.color }}></i>
              <span className="text-xs">{p.name}</span>
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