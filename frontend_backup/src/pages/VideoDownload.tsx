import React, { useState, useEffect, useRef } from 'react';
import { VideoInfo, DownloadOptions, DownloadTask, SystemSettings } from '@/types';

const VideoDownload: React.FC = () => {
  const [videoUrl, setVideoUrl] = useState('');
  const [platform, setPlatform] = useState('');
  const [videoInfo, setVideoInfo] = useState<VideoInfo | null>(null);
  const [downloadOptions, setDownloadOptions] = useState<DownloadOptions>({
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
  const [settings, setSettings] = useState<SystemSettings>({
    downloadPath: '~/Downloads',
    maxConcurrent: 3,
    notifications: true,
    retryCount: 3
  });
  const [activeTab, setActiveTab] = useState('info');
  const [notification, setNotification] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);

  const platforms = [
    { name: '抖音', icon: 'fab fa-tiktok', color: 'text-red-500' },
    { name: '快手', icon: 'fas fa-play', color: 'text-yellow-500' },
    { name: '小红书', icon: 'fas fa-book', color: 'text-pink-500' },
    { name: '视频号', icon: 'fab fa-weixin', color: 'text-green-500' },
    { name: 'B站', icon: 'fas fa-b', color: 'text-blue-500' },
    { name: 'Tiktok', icon: 'fab fa-tiktok', color: 'text-black' },
    { name: '其他', icon: 'fas fa-globe', color: 'text-gray-500' }
  ];

  const formats = ['MP4', 'WebM', 'MKV', 'AVI', 'MOV'];
  const qualities = ['144p', '240p', '360p', '480p', '720p', '1080p', '2K', '4K'];

  const detectPlatform = (url: string) => {
    if (url.includes('douyin.com')) return '抖音';
    if (url.includes('kuaishou.com')) return '快手';
    if (url.includes('xiaohongshu.com')) return '小红书';
    if (url.includes('weixin.qq.com')) return '视频号';
    if (url.includes('bilibili.com')) return 'B站';
    if (url.includes('tiktok.com')) return 'Tiktok';
    return '其他';
  };

  const parseVideo = async () => {
    if (!videoUrl) {
      setNotification('请输入视频链接');
      return;
    }

    const detectedPlatform = detectPlatform(videoUrl);
    setPlatform(detectedPlatform);
    setIsLoading(true);
    setNotification(`正在解析 ${detectedPlatform} 视频...`);

    // 模拟API请求
    setTimeout(() => {
      setVideoInfo({
        id: 'V' + Date.now(),
        title: '如何快速学会React开发',
        subtitle: '前端工程师必学框架',
        author: {
          name: '前端开发指南',
          avatar: 'https://ai-public.mastergo.com/ai/img_res/78c9becbcdb331677f04bb7e7372d347.jpg',
          followers: '12.8万'
        },
        publishTime: '2023-05-15 14:30',
        duration: '12:45',
        views: '256.3万',
        keywords: ['React', '前端开发', 'JavaScript', '教程'],
        thumbnail: 'https://ai-public.mastergo.com/ai/img_res/e31c3756f3c91e1450581cb1a64ca3fb.jpg',
        videoUrl: 'https://example.com/video.mp4',
        platform: detectedPlatform,
        tags: ['React', '前端开发', 'JavaScript', '教程'],
        size: '156.8MB',
        createTime: '2023-05-15 14:30:00',
        uploadTime: '2023-05-15 15:45:00',
        status: '已解析'
      });
      setNotification('视频解析成功');
      setActiveTab('info');
      setIsLoading(false);
    }, 1500);
  };

  const startDownload = () => {
    if (!videoInfo) return;

    const newDownload: DownloadTask = {
      id: Date.now(),
      title: videoInfo.title,
      platform,
      thumbnail: videoInfo.thumbnail,
      status: 'waiting',
      progress: 0,
      options: downloadOptions
    };

    setDownloadQueue([...downloadQueue, newDownload]);
    setNotification('已添加到下载队列');

    // 模拟下载过程
    if (!currentDownload) {
      processDownloadQueue([...downloadQueue, newDownload]);
    }
  };

  const processDownloadQueue = (queue: DownloadTask[]) => {
    const waitingTasks = queue.filter(task => task.status === 'waiting');
    if (waitingTasks.length === 0) return;

    const task = waitingTasks[0];
    setCurrentDownload({ ...task, status: 'downloading' });
    let progress = 0;
    const interval = setInterval(() => {
      progress += Math.random() * 5;
      if (progress >= 100) {
        progress = 100;
        clearInterval(interval);
        const updatedQueue = queue.map(t =>
          t.id === task.id ? { ...t, status: 'completed' as const, progress: 100 } : t
        );
        setDownloadQueue(updatedQueue);
        setCurrentDownload(null);
        setDownloadProgress(0);
        setNotification(`${task.title} 下载完成`);
        
        // 添加到历史记录
        setHistory([{
          id: task.id,
          title: task.title,
          platform: task.platform,
          thumbnail: task.thumbnail,
          downloadTime: new Date().toLocaleString(),
          path: `${settings.downloadPath}/${task.title}.${task.options.format.toLowerCase()}`
        }, ...history]);
        
        // 处理下一个任务
        processDownloadQueue(updatedQueue);
      } else {
        setDownloadProgress(progress);
        setDownloadSpeed(`${Math.floor(Math.random() * 2000) + 500} KB/s`);
        setRemainingTime(`${Math.floor((100 - progress) / 5)}秒`);
      }
    }, 500);
  };

  const handlePause = (id: number) => {
    setDownloadQueue(downloadQueue.map(task =>
      task.id === id ? { ...task, status: 'paused' } : task
    ));
    if (currentDownload && currentDownload.id === id) {
      setCurrentDownload(null);
      setDownloadProgress(0);
    }
    setNotification('下载已暂停');
  };

  const handleResume = (id: number) => {
    setDownloadQueue(downloadQueue.map(task =>
      task.id === id ? { ...task, status: 'waiting' } : task
    ));
    processDownloadQueue(downloadQueue);
    setNotification('下载已恢复');
  };

  const handleDelete = (id: number) => {
    const newQueue = downloadQueue.filter(task => task.id !== id);
    setDownloadQueue(newQueue);
    if (currentDownload && currentDownload.id === id) {
      setCurrentDownload(null);
      setDownloadProgress(0);
    }
    setNotification('任务已删除');
  };

  const handleRetry = (id: number) => {
    setDownloadQueue(downloadQueue.map(task =>
      task.id === id ? { ...task, status: 'waiting', progress: 0 } : task
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
      {/* 通知栏 */}
      {notification && (
        <div className="bg-blue-100 border border-blue-400 text-blue-700 px-4 py-3 rounded flex justify-between items-center">
          <span>{notification}</span>
          <button onClick={() => setNotification('')} className="text-blue-700 hover:text-blue-900">
            <i className="fas fa-times"></i>
          </button>
        </div>
      )}

      {/* 视频链接输入区 */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="flex items-center space-x-2 mb-4">
          <i className="fas fa-link text-blue-600"></i>
          <h2 className="text-lg font-semibold">视频链接解析</h2>
        </div>
        <div className="flex space-x-2 mb-4">
          <div className="flex-1 relative">
            <input
              type="text"
              value={videoUrl}
              onChange={(e) => setVideoUrl(e.target.value)}
              placeholder="粘贴视频链接 (抖音/快手/B站/小红书/视频号/Tiktok等)"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
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
            disabled={isLoading}
            className="rounded-button whitespace-nowrap px-6 py-3 bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {isLoading ? (
              <>
                <i className="fas fa-spinner animate-spin mr-2"></i>解析中...
              </>
            ) : (
              <>
                <i className="fas fa-search mr-2"></i>开始解析
              </>
            )}
          </button>
        </div>
        <div className="flex justify-center space-x-4">
          {platforms.map((p) => (
            <div
              key={p.name}
              className={`flex flex-col items-center p-2 rounded-lg cursor-pointer transition-colors ${
                platform === p.name ? 'bg-blue-100' : 'hover:bg-gray-100'
              }`}
            >
              <i className={`${p.icon} ${p.color} text-2xl mb-1`}></i>
              <span className="text-xs">{p.name}</span>
            </div>
          ))}
        </div>
      </div>

      {videoInfo ? (
        <div className="bg-white rounded-lg shadow-sm overflow-hidden">
          {/* 标签页导航 */}
          <div className="border-b border-gray-200">
            <nav className="flex -mb-px">
              {[
                { id: 'info', label: '视频信息', icon: 'fa-info-circle' },
                { id: 'download', label: '下载选项', icon: 'fa-download' },
                { id: 'queue', label: '下载队列', icon: 'fa-tasks' }
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`py-4 px-6 text-center border-b-2 font-medium text-sm ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <i className={`fas ${tab.icon} mr-2`}></i>{tab.label}
                </button>
              ))}
            </nav>
          </div>

          {/* 标签页内容 */}
          <div className="p-6">
            {activeTab === 'info' && (
              <div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
                  {/* 视频信息 */}
                  <div className="md:col-span-2">
                    <h2 className="text-2xl font-bold mb-2">{videoInfo.title}</h2>
                    {typeof videoInfo.author === 'object' && (
                      <div className="flex items-center space-x-4 mb-6">
                        <img
                          src={videoInfo.author.avatar}
                          alt={videoInfo.author.name}
                          className="w-12 h-12 rounded-full object-cover"
                        />
                        <div>
                          <p className="font-medium">{videoInfo.author.name}</p>
                          <p className="text-sm text-gray-500">{videoInfo.author.followers} 粉丝</p>
                        </div>
                      </div>
                    )}
                    <div className="grid grid-cols-3 gap-4 mb-6">
                      <div>
                        <p className="text-sm text-gray-500">发布时间</p>
                        <p className="font-medium">{videoInfo.publishTime}</p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-500">视频时长</p>
                        <p className="font-medium">{videoInfo.duration}</p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-500">播放量</p>
                        <p className="font-medium">{videoInfo.views}</p>
                      </div>
                    </div>
                    <div className="mb-6">
                      <p className="text-sm text-gray-500 mb-2">关键词</p>
                      <div className="flex flex-wrap gap-2">
                        {videoInfo.keywords?.map((keyword, index) => (
                          <span key={index} className="px-3 py-1 bg-gray-100 rounded-full text-sm">
                            #{keyword}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                  
                  {/* 视频播放器 */}
                  <div className="md:col-span-1">
                    <div className="relative pt-[56.25%] bg-black rounded-lg overflow-hidden">
                      <img
                        src={videoInfo.thumbnail}
                        alt="视频缩略图"
                        className="absolute inset-0 w-full h-full object-cover"
                      />
                      <div className="absolute inset-0 flex items-center justify-center">
                        <button className="w-16 h-16 bg-black bg-opacity-50 rounded-full flex items-center justify-center hover:bg-opacity-70 transition-all">
                          <i className="fas fa-play text-white text-xl ml-1"></i>
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
                <div className="flex justify-end">
                  <button
                    onClick={() => setActiveTab('download')}
                    className="rounded-button whitespace-nowrap px-6 py-2 bg-blue-600 text-white hover:bg-blue-700"
                  >
                    下一步 <i className="fas fa-arrow-right ml-2"></i>
                  </button>
                </div>
              </div>
            )}

            {activeTab === 'download' && (
              <div>
                <h3 className="text-lg font-semibold mb-4">下载选项配置</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">格式选择</label>
                    <div className="flex flex-wrap gap-2">
                      {formats.map((format) => (
                        <button
                          key={format}
                          onClick={() => setDownloadOptions({...downloadOptions, format})}
                          className={`rounded-button whitespace-nowrap px-4 py-2 ${
                            downloadOptions.format === format
                              ? 'bg-blue-600 text-white'
                              : 'bg-gray-100 hover:bg-gray-200'
                          }`}
                        >
                          {format}
                        </button>
                      ))}
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">画质选择</label>
                    <div className="flex flex-wrap gap-2">
                      {qualities.map((quality) => (
                        <button
                          key={quality}
                          onClick={() => setDownloadOptions({...downloadOptions, quality})}
                          className={`rounded-button whitespace-nowrap px-4 py-2 ${
                            downloadOptions.quality === quality
                              ? 'bg-blue-600 text-white'
                              : 'bg-gray-100 hover:bg-gray-200'
                          }`}
                        >
                          {quality}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
                <div className="mb-6">
                  <label className="block text-sm font-medium text-gray-700 mb-2">下载内容</label>
                  <div className="space-y-2">
                    {[
                      { key: 'video', label: '仅视频' },
                      { key: 'audio', label: '仅音频' },
                      { key: 'videoAndAudio', label: '视频+音频' }
                    ].map((item) => (
                      <label key={item.key} className="flex items-center space-x-2">
                        <input
                          type="checkbox"
                          checked={downloadOptions.content.includes(item.key)}
                          onChange={(e) => {
                            const content = e.target.checked
                              ? [...downloadOptions.content, item.key]
                              : downloadOptions.content.filter((c) => c !== item.key);
                            setDownloadOptions({...downloadOptions, content});
                          }}
                          className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                        />
                        <span>{item.label}</span>
                      </label>
                    ))}
                    <label className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        checked={downloadOptions.subtitles}
                        onChange={(e) => setDownloadOptions({...downloadOptions, subtitles: e.target.checked})}
                        className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                      />
                      <span>字幕文件</span>
                    </label>
                    <label className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        checked={downloadOptions.danmaku}
                        onChange={(e) => setDownloadOptions({...downloadOptions, danmaku: e.target.checked})}
                        className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                      />
                      <span>弹幕文件</span>
                    </label>
                  </div>
                </div>
                <div className="flex justify-between">
                  <button
                    onClick={() => setActiveTab('info')}
                    className="rounded-button whitespace-nowrap px-6 py-2 bg-gray-200 hover:bg-gray-300"
                  >
                    <i className="fas fa-arrow-left mr-2"></i>上一步
                  </button>
                  <button
                    onClick={startDownload}
                    className="rounded-button whitespace-nowrap px-6 py-2 bg-blue-600 text-white hover:bg-blue-700"
                  >
                    <i className="fas fa-download mr-2"></i>开始下载
                  </button>
                </div>
              </div>
            )}

            {activeTab === 'queue' && (
              <div>
                {currentDownload && (
                  <div className="mb-6 bg-blue-50 p-4 rounded-lg">
                    <div className="flex justify-between items-center mb-2">
                      <h4 className="font-medium">正在下载: {currentDownload.title}</h4>
                      <span className="text-sm text-gray-600">{downloadSpeed} • 剩余 {remainingTime}</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2.5">
                      <div
                        className="bg-blue-600 h-2.5 rounded-full transition-all duration-300"
                        style={{ width: `${downloadProgress}%` }}
                      ></div>
                    </div>
                  </div>
                )}
                
                <div className="mb-4 flex justify-between items-center">
                  <h3 className="text-lg font-semibold">下载队列</h3>
                  <div className="flex space-x-2">
                    <button className="rounded-button whitespace-nowrap px-3 py-1 bg-gray-100 hover:bg-gray-200">
                      <i className="fas fa-pause mr-1"></i>全部暂停
                    </button>
                    <button className="rounded-button whitespace-nowrap px-3 py-1 bg-gray-100 hover:bg-gray-200">
                      <i className="fas fa-play mr-1"></i>全部开始
                    </button>
                    <button className="rounded-button whitespace-nowrap px-3 py-1 bg-gray-100 hover:bg-gray-200">
                      <i className="fas fa-trash mr-1"></i>清空已完成
                    </button>
                  </div>
                </div>
                
                <div className="space-y-3">
                  {downloadQueue.length === 0 ? (
                    <div className="text-center py-8 text-gray-500">
                      <i className="fas fa-inbox text-4xl mb-2"></i>
                      <p>暂无下载任务</p>
                    </div>
                  ) : (
                    downloadQueue.map((task) => (
                      <div
                        key={task.id}
                        className="flex items-center p-3 bg-gray-50 rounded-lg hover:bg-gray-100"
                      >
                        <img
                          src={task.thumbnail}
                          alt={task.title}
                          className="w-16 h-9 object-cover rounded mr-3"
                        />
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium truncate">{task.title}</p>
                          <div className="flex items-center text-xs text-gray-500 space-x-3">
                            <span>
                              <i className={`fas ${
                                task.platform === '抖音' ? 'fa-tiktok' :
                                task.platform === 'B站' ? 'fa-b' : 'fa-video'
                              } mr-1`}></i>
                              {task.platform}
                            </span>
                            <span>
                              <i className="fas fa-file-alt mr-1"></i>
                              {task.options.format} • {task.options.quality}
                            </span>
                          </div>
                        </div>
                        <div className="flex items-center space-x-2">
                          <span className={`text-xs px-2 py-1 rounded-full ${
                            task.status === 'waiting' ? 'bg-yellow-100 text-yellow-800' :
                            task.status === 'downloading' ? 'bg-blue-100 text-blue-800' :
                            task.status === 'completed' ? 'bg-green-100 text-green-800' :
                            'bg-gray-100 text-gray-800'
                          }`}>
                            {task.status === 'waiting' ? '等待中' :
                             task.status === 'downloading' ? '下载中' :
                             task.status === 'completed' ? '已完成' : '已暂停'}
                          </span>
                          {task.status === 'paused' ? (
                            <button
                              onClick={() => handleResume(task.id)}
                              className="rounded-button whitespace-nowrap px-2 py-1 text-green-600 hover:text-green-800"
                              title="继续"
                            >
                              <i className="fas fa-play"></i>
                            </button>
                          ) : task.status === 'downloading' ? (
                            <button
                              onClick={() => handlePause(task.id)}
                              className="rounded-button whitespace-nowrap px-2 py-1 text-yellow-600 hover:text-yellow-800"
                              title="暂停"
                            >
                              <i className="fas fa-pause"></i>
                            </button>
                          ) : task.status === 'completed' ? (
                            <button
                              onClick={() => handleRetry(task.id)}
                              className="rounded-button whitespace-nowrap px-2 py-1 text-blue-600 hover:text-blue-800"
                              title="重新下载"
                            >
                              <i className="fas fa-redo"></i>
                            </button>
                          ) : null}
                          <button
                            onClick={() => handleDelete(task.id)}
                            className="rounded-button whitespace-nowrap px-2 py-1 text-red-600 hover:text-red-800"
                            title="删除"
                          >
                            <i className="fas fa-trash"></i>
                          </button>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow-sm p-12 text-center">
          <i className="fas fa-film text-5xl text-gray-300 mb-4"></i>
          <h3 className="text-xl font-medium text-gray-700 mb-2">请输入视频链接并解析</h3>
          <p className="text-gray-500 mb-6">支持抖音、快手、B站、小红书、视频号、Tiktok等平台</p>
        </div>
      )}
    </div>
  );
};

export default VideoDownload;