import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { VideoInfo, SortConfig, ColumnWidths } from '@/types';

const VideoList: React.FC = () => {
  const [videos, setVideos] = useState<VideoInfo[]>([
    {
      id: 1,
      thumbnail: 'https://ai-public.mastergo.com/ai/img_res/59da6e6387794fa1b1a34d47bb4a0583.jpg',
      title: '春日樱花盛开美景',
      platform: '抖音',
      author: '旅行摄影师王明',
      tags: ['自然风光', '樱花', '春天'],
      duration: '02:45',
      size: '45.6MB',
      createTime: '2023-03-15 14:30:22',
      uploadTime: '2023-03-16 09:15:30',
      status: '已解析',
      parsedTime: '2023-03-16 10:20:15'
    },
    {
      id: 2,
      thumbnail: 'https://ai-public.mastergo.com/ai/img_res/53f3363fd3b34467f8b9e6f7f25c5bfe.jpg',
      title: '都市夜景航拍',
      platform: 'B站',
      author: '航拍达人李强',
      tags: ['城市风光', '夜景', '航拍'],
      duration: '03:12',
      size: '78.2MB',
      createTime: '2023-04-05 20:15:45',
      uploadTime: '2023-04-06 11:30:20',
      status: '未解析',
      parsedTime: ''
    },
    {
      id: 3,
      thumbnail: 'https://ai-public.mastergo.com/ai/img_res/a4ff0cc0ba5c219eddce90c27fa673f6.jpg',
      title: '家常菜烹饪教程',
      platform: '小红书',
      author: '美食博主张丽',
      tags: ['美食', '烹饪', '教程'],
      duration: '05:30',
      size: '120.5MB',
      createTime: '2023-05-10 09:45:12',
      uploadTime: '2023-05-10 15:20:33',
      status: '已解析',
      parsedTime: '2023-05-10 16:05:44'
    },
    {
      id: 4,
      thumbnail: 'https://ai-public.mastergo.com/ai/img_res/9c66f4dc1e4bb8f77b9c974f74c2c39c.jpg',
      title: '30天健身挑战',
      platform: '快手',
      author: '健身教练赵刚',
      tags: ['健身', '运动', '挑战'],
      duration: '08:15',
      size: '156.8MB',
      createTime: '2023-06-20 13:10:25',
      uploadTime: '2023-06-21 08:45:18',
      status: '解析中',
      parsedTime: ''
    },
    {
      id: 5,
      thumbnail: 'https://ai-public.mastergo.com/ai/img_res/7a61d0ab9609e52deef72de46f7383e7.jpg',
      title: '最新手机评测',
      platform: '视频号',
      author: '科技达人陈伟',
      tags: ['科技', '评测', '手机'],
      duration: '12:45',
      size: '210.3MB',
      createTime: '2023-07-05 11:20:30',
      uploadTime: '2023-07-06 10:15:45',
      status: '已解析',
      parsedTime: '2023-07-06 11:30:22'
    }
  ]);

  const [selectedVideos, setSelectedVideos] = useState<(string | number)[]>([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(20);
  const [sortConfig, setSortConfig] = useState<SortConfig | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [playingVideo, setPlayingVideo] = useState<string | number | null>(null);
  const [columnWidths, setColumnWidths] = useState<ColumnWidths>({
    id: 80,
    thumbnail: 120,
    title: 200,
    platform: 100,
    author: 150,
    tags: 180,
    duration: 100,
    size: 100,
    createTime: 150,
    uploadTime: 150,
    status: 100
  });
  const [expandedRow, setExpandedRow] = useState<string | number | null>(null);

  const totalPages = Math.ceil(videos.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;

  const handleSelectVideo = (id: string | number) => {
    if (selectedVideos.includes(id)) {
      setSelectedVideos(selectedVideos.filter(videoId => videoId !== id));
    } else {
      setSelectedVideos([...selectedVideos, id]);
    }
  };

  const handleSelectAll = (e: React.ChangeEvent<HTMLInputElement>) => {
    const currentVideos = filteredVideos.slice(startIndex, endIndex);
    if (e.target.checked) {
      setSelectedVideos(currentVideos.map(video => video.id));
    } else {
      setSelectedVideos([]);
    }
  };

  const handleSort = (key: string) => {
    let direction: 'ascending' | 'descending' = 'ascending';
    if (sortConfig && sortConfig.key === key && sortConfig.direction === 'ascending') {
      direction = 'descending';
    }
    setSortConfig({ key, direction });
  };

  const handleColumnResize = (e: React.MouseEvent, column: string) => {
    e.stopPropagation();
    e.preventDefault();
    
    const startX = e.clientX;
    const startWidth = columnWidths[column];
    
    const handleMouseMove = (moveEvent: MouseEvent) => {
      moveEvent.preventDefault();
      const difference = moveEvent.clientX - startX;
      const newWidth = Math.max(50, startWidth + difference);
      
      setColumnWidths(prev => ({
        ...prev,
        [column]: newWidth
      }));
    };
    
    const handleMouseUp = () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = 'default';
    };

    document.body.style.cursor = 'col-resize';
    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);
  };

  const handlePlayVideo = (id: string | number) => {
    setPlayingVideo(playingVideo === id ? null : id);
  };

  const handleExpandRow = (id: string | number) => {
    setExpandedRow(expandedRow === id ? null : id);
  };

  const handleTagClick = (tag: string) => {
    setSearchTerm(tag);
  };

  const handleAnalyze = (id: string | number) => {
    // 这里可以导航到解析页面
    console.log('Analyze video:', id);
  };

  const handleDelete = (id: string | number) => {
    setVideos(videos.filter(video => video.id !== id));
  };

  const handleBatchAnalyze = () => {
    if (selectedVideos.length === 0) return;
    console.log('Batch analyze videos:', selectedVideos);
  };

  // 排序逻辑
  const sortedVideos = [...videos];
  if (sortConfig !== null) {
    sortedVideos.sort((a, b) => {
      const aValue = a[sortConfig.key as keyof VideoInfo];
      const bValue = b[sortConfig.key as keyof VideoInfo];
      
      if (aValue < bValue) {
        return sortConfig.direction === 'ascending' ? -1 : 1;
      }
      if (aValue > bValue) {
        return sortConfig.direction === 'ascending' ? 1 : -1;
      }
      return 0;
    });
  }

  // 过滤逻辑
  const filteredVideos = sortedVideos.filter(video => {
    const searchLower = searchTerm.toLowerCase();
    return (
      video.title.toLowerCase().includes(searchLower) ||
      (typeof video.author === 'string' ? video.author : video.author.name).toLowerCase().includes(searchLower) ||
      video.platform.toLowerCase().includes(searchLower) ||
      video.tags.some(tag => tag.toLowerCase().includes(searchLower))
    );
  });

  const currentVideos = filteredVideos.slice(startIndex, endIndex);

  const getPlatformColor = (platform: string) => {
    switch (platform) {
      case '抖音': return 'bg-pink-100 text-pink-800';
      case 'B站': return 'bg-blue-100 text-blue-800';
      case '小红书': return 'bg-red-100 text-red-800';
      case '快手': return 'bg-yellow-100 text-yellow-800';
      case '视频号': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case '已解析':
        return <i className="fas fa-check-circle text-green-500" title="已解析"></i>;
      case '未解析':
        return <i className="fas fa-times-circle text-red-500" title="未解析"></i>;
      case '解析中':
        return <i className="fas fa-spinner text-blue-500 animate-spin" title="解析中"></i>;
      default:
        return <i className="fas fa-question-circle text-gray-500" title="未知状态"></i>;
    }
  };

  return (
    <div className="space-y-6 w-full">
      {/* 简化的顶部操作区 */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <h1 className="text-xl font-semibold text-gray-900">视频列表</h1>
            <div className="relative">
              <input
                type="text"
                placeholder="搜索视频..."
                className="w-80 pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
              <i className="fas fa-search absolute left-3 top-3 text-gray-400"></i>
            </div>
          </div>
          <div className="flex items-center space-x-3">
            <button
              onClick={handleBatchAnalyze}
              disabled={selectedVideos.length === 0}
              className={`px-4 py-2 rounded-lg text-sm font-medium ${
                selectedVideos.length === 0
                  ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                  : 'bg-blue-600 text-white hover:bg-blue-700'
              }`}
            >
              批量解析 ({selectedVideos.length})
            </button>
          </div>
        </div>
      </div>

      {/* 视频列表 */}
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden w-full">
          <div className="overflow-x-auto overflow-y-auto" style={{ maxHeight: 'calc(100vh - 300px)', width: '100%' }}>
            <table className="divide-y divide-gray-200" style={{ minWidth: '1400px', width: 'max-content', tableLayout: 'fixed' }}>
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-12">
                  <input
                    type="checkbox"
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    onChange={handleSelectAll}
                    checked={selectedVideos.length === currentVideos.length && currentVideos.length > 0}
                  />
                </th>
                {[
                  { key: 'id', label: 'ID', sortable: true },
                  { key: 'thumbnail', label: '缩略图', sortable: false },
                  { key: 'title', label: '视频标题', sortable: true },
                  { key: 'platform', label: '平台', sortable: true },
                  { key: 'author', label: '作者', sortable: true },
                  { key: 'tags', label: '标签', sortable: false },
                  { key: 'duration', label: '时长', sortable: true },
                  { key: 'size', label: '大小', sortable: true },
                  { key: 'createTime', label: '创作时间', sortable: true },
                  { key: 'uploadTime', label: '上传时间', sortable: true },
                  { key: 'status', label: '状态', sortable: true }
                ].map((column) => (
                  <th
                    key={column.key}
                    className={`px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider relative ${
                      column.sortable ? 'cursor-pointer hover:bg-gray-100' : ''
                    }`}
                    style={{ width: columnWidths[column.key] }}
                    onClick={column.sortable ? () => handleSort(column.key) : undefined}
                  >
                    <div className="flex items-center justify-between">
                      {column.label}
                      {column.sortable && sortConfig?.key === column.key && (
                        <i className={`fas fa-sort-${sortConfig.direction === 'ascending' ? 'up' : 'down'} ml-1`}></i>
                      )}
                    </div>
                    <div
                      className="absolute right-0 top-0 h-full w-2 cursor-col-resize hover:bg-blue-500 transition-colors"
                      onMouseDown={(e) => handleColumnResize(e, column.key)}
                      style={{ touchAction: 'none', zIndex: 10 }}
                    ></div>
                  </th>
                ))}
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-32">
                  操作
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {currentVideos.map((video) => (
                <React.Fragment key={video.id}>
                  <tr
                    className={`hover:bg-gray-50 cursor-pointer ${
                      expandedRow === video.id ? 'bg-blue-50' : ''
                    }`}
                    onDoubleClick={() => handleExpandRow(video.id)}
                  >
                    <td className="px-4 py-4 whitespace-nowrap">
                      <input
                        type="checkbox"
                        className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                        checked={selectedVideos.includes(video.id)}
                        onChange={() => handleSelectVideo(video.id)}
                      />
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap" style={{ width: columnWidths.id }}>
                      {video.id}
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap" style={{ width: columnWidths.thumbnail }}>
                      <img
                        src={video.thumbnail}
                        alt="视频缩略图"
                        className="h-12 w-16 object-cover rounded"
                      />
                    </td>
                    <td className="px-4 py-4" style={{ width: columnWidths.title }}>
                      <div className="font-medium text-gray-900 text-ellipsis">{video.title}</div>
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap" style={{ width: columnWidths.platform }}>
                      <span className={`px-2 py-1 text-xs rounded-full ${getPlatformColor(video.platform)}`}>
                        {video.platform}
                      </span>
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap" style={{ width: columnWidths.author }}>
                      {typeof video.author === 'string' ? video.author : video.author.name}
                    </td>
                    <td className="px-4 py-4" style={{ width: columnWidths.tags }}>
                      <div className="flex flex-wrap gap-1">
                        {video.tags.map((tag, index) => (
                          <span
                            key={index}
                            className="px-2 py-1 text-xs bg-gray-100 text-gray-800 rounded-full cursor-pointer hover:bg-gray-200"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleTagClick(tag);
                            }}
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap" style={{ width: columnWidths.duration }}>
                      {video.duration}
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap" style={{ width: columnWidths.size }}>
                      {video.size}
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap" style={{ width: columnWidths.createTime }}>
                      {video.createTime}
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap" style={{ width: columnWidths.uploadTime }}>
                      {video.uploadTime}
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap" style={{ width: columnWidths.status }}>
                      <div className="flex items-center">
                        {getStatusIcon(video.status)}
                        <span className="ml-2 text-sm">{video.status}</span>
                      </div>
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <div className="flex space-x-2">
                        <button
                          className="text-blue-600 hover:text-blue-900"
                          onClick={(e) => {
                            e.stopPropagation();
                            handlePlayVideo(video.id);
                          }}
                          title="播放"
                        >
                          <i className="fas fa-play"></i>
                        </button>
                        {video.status !== '已解析' && (
                          <button
                            className="text-green-600 hover:text-green-900"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleAnalyze(video.id);
                            }}
                            title="解析"
                          >
                            <i className="fas fa-brain"></i>
                          </button>
                        )}
                        <Link
                          to={`/analysis/${video.id}`}
                          className="text-purple-600 hover:text-purple-900"
                          title="查看解析"
                        >
                          <i className="fas fa-eye"></i>
                        </Link>
                        <button
                          className="text-yellow-600 hover:text-yellow-900"
                          onClick={(e) => e.stopPropagation()}
                          title="编辑"
                        >
                          <i className="fas fa-edit"></i>
                        </button>
                        <button
                          className="text-red-600 hover:text-red-900"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDelete(video.id);
                          }}
                          title="删除"
                        >
                          <i className="fas fa-trash"></i>
                        </button>
                      </div>
                    </td>
                  </tr>
                  {expandedRow === video.id && (
                    <tr>
                      <td colSpan={13} className="px-4 py-4 bg-blue-50">
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <h4 className="font-medium text-gray-900 mb-2">视频详情</h4>
                            <p className="text-sm text-gray-600">
                              备注: 这是一个关于{video.tags.join(', ')}的视频，
                              由{typeof video.author === 'string' ? video.author : video.author.name}创作。
                            </p>
                          </div>
                          <div>
                            <h4 className="font-medium text-gray-900 mb-2">解析信息</h4>
                            {video.status === '已解析' ? (
                              <p className="text-sm text-gray-600">解析时间: {video.parsedTime}</p>
                            ) : video.status === '未解析' ? (
                              <p className="text-sm text-gray-600">尚未解析</p>
                            ) : (
                              <p className="text-sm text-gray-600">正在解析中...</p>
                            )}
                          </div>
                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              ))}
            </tbody>
          </table>
        </div>

        {/* 底部分页操作区 */}
        <div className="bg-gray-50 px-4 py-3 border-t border-gray-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="relative">
                <select
                  className="appearance-none bg-white border border-gray-300 rounded-md pl-3 pr-8 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={itemsPerPage}
                  onChange={(e) => setItemsPerPage(Number(e.target.value))}
                >
                  <option value={20}>每页 20 条</option>
                  <option value={50}>每页 50 条</option>
                  <option value={100}>每页 100 条</option>
                </select>
                <i className="fas fa-chevron-down absolute right-3 top-3 text-gray-400 pointer-events-none"></i>
              </div>
              <div className="flex items-center space-x-1">
                <button
                  className={`px-3 py-1 rounded-button ${
                    currentPage === 1
                      ? 'bg-gray-200 text-gray-500 cursor-not-allowed'
                      : 'bg-white text-gray-700 hover:bg-gray-100'
                  }`}
                  onClick={() => setCurrentPage(1)}
                  disabled={currentPage === 1}
                >
                  第一页
                </button>
                <button
                  className={`px-3 py-1 rounded-button ${
                    currentPage === 1
                      ? 'bg-gray-200 text-gray-500 cursor-not-allowed'
                      : 'bg-white text-gray-700 hover:bg-gray-100'
                  }`}
                  onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                  disabled={currentPage === 1}
                >
                  上一页
                </button>
                <span className="px-3 py-1 text-sm text-gray-700">
                  {currentPage} / {totalPages}
                </span>
                <button
                  className={`px-3 py-1 rounded-button ${
                    currentPage === totalPages
                      ? 'bg-gray-200 text-gray-500 cursor-not-allowed'
                      : 'bg-white text-gray-700 hover:bg-gray-100'
                  }`}
                  onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                  disabled={currentPage === totalPages}
                >
                  下一页
                </button>
                <button
                  className={`px-3 py-1 rounded-button ${
                    currentPage === totalPages
                      ? 'bg-gray-200 text-gray-500 cursor-not-allowed'
                      : 'bg-white text-gray-700 hover:bg-gray-100'
                  }`}
                  onClick={() => setCurrentPage(totalPages)}
                  disabled={currentPage === totalPages}
                >
                  最后一页
                </button>
              </div>
            </div>
            <div className="text-sm text-gray-700">
              共 {filteredVideos.length} 条视频
            </div>
          </div>
        </div>

        {/* 视频播放器 */}
        {playingVideo && (
          <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg shadow-lg overflow-hidden max-w-4xl w-full mx-4">
              <div className="relative" style={{ paddingTop: '56.25%' }}>
                <div className="absolute inset-0 flex items-center justify-center bg-gray-800">
                  <i className="fas fa-play-circle text-6xl text-white opacity-75"></i>
                </div>
              </div>
              <div className="p-4 bg-gray-800 flex items-center justify-between">
                <div className="text-white text-sm">
                  <span>00:00</span>
                  <span className="mx-2">/</span>
                  <span>{videos.find(v => v.id === playingVideo)?.duration}</span>
                </div>
                <div className="flex items-center space-x-4">
                  <button className="text-white hover:text-blue-400" title="播放/暂停">
                    <i className="fas fa-play"></i>
                  </button>
                  <button className="text-white hover:text-blue-400" title="音量">
                    <i className="fas fa-volume-up"></i>
                  </button>
                  <button className="text-white hover:text-blue-400" title="全屏">
                    <i className="fas fa-expand"></i>
                  </button>
                  <button
                    className="text-white hover:text-red-400"
                    onClick={() => setPlayingVideo(null)}
                    title="关闭"
                  >
                    <i className="fas fa-times"></i>
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default VideoList;