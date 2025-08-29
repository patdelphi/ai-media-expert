import React, { useState, useEffect } from 'react';
import { Video } from '../types';
import { formatFileSize, formatDate, formatRelativeTime } from '../utils';

const VideoList: React.FC = () => {
  const [videos, setVideos] = useState<Video[]>([
    {
      id: '1',
      title: '春日樱花盛开美景',
      description: '记录春天最美的樱花盛开时刻',
      url: 'https://example.com/video1.mp4',
      thumbnail: 'https://via.placeholder.com/160x90',
      duration: 165, // 2:45
      size: 47841280, // 45.6MB
      format: 'MP4',
      status: 'completed',
      created_at: '2023-03-15T14:30:00Z',
      updated_at: '2023-03-16T10:20:00Z',
      user_id: 'user1'
    },
    {
      id: '2',
      title: '都市夜景航拍',
      description: '城市夜晚的美丽航拍镜头',
      url: 'https://example.com/video2.mp4',
      thumbnail: 'https://via.placeholder.com/160x90',
      duration: 192, // 3:12
      size: 82010112, // 78.2MB
      format: 'MP4',
      status: 'processing',
      created_at: '2023-04-05T20:15:00Z',
      updated_at: '2023-04-06T11:30:00Z',
      user_id: 'user2'
    },
    {
      id: '3',
      title: '家常菜烹饪教程',
      description: '简单易学的家常菜制作方法',
      url: 'https://example.com/video3.mp4',
      thumbnail: 'https://via.placeholder.com/160x90',
      duration: 330, // 5:30
      size: 126353408, // 120.5MB
      format: 'MP4',
      status: 'completed',
      created_at: '2023-05-10T09:45:00Z',
      updated_at: '2023-05-10T16:05:00Z',
      user_id: 'user3'
    },
    {
      id: '4',
      title: '30天健身挑战',
      description: '跟着教练一起完成30天健身挑战',
      url: 'https://example.com/video4.mp4',
      thumbnail: 'https://via.placeholder.com/160x90',
      duration: 495, // 8:15
      size: 164499456, // 156.8MB
      format: 'MP4',
      status: 'uploading',
      progress: 75,
      created_at: '2023-06-20T13:10:00Z',
      updated_at: '2023-06-21T08:45:00Z',
      user_id: 'user4'
    },
    {
      id: '5',
      title: '最新手机评测',
      description: '详细评测最新发布的智能手机',
      url: 'https://example.com/video5.mp4',
      thumbnail: 'https://via.placeholder.com/160x90',
      duration: 765, // 12:45
      size: 220594176, // 210.3MB
      format: 'MP4',
      status: 'completed',
      created_at: '2023-07-05T11:20:00Z',
      updated_at: '2023-07-06T11:30:00Z',
      user_id: 'user5'
    }
  ]);

  const [selectedVideos, setSelectedVideos] = useState<string[]>([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(10);
  const [sortConfig, setSortConfig] = useState<{key: keyof Video; direction: 'asc' | 'desc'} | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('list');
  const [playingVideo, setPlayingVideo] = useState<string | null>(null);

  // 过滤和搜索
  const filteredVideos = videos.filter(video => {
    const matchesSearch = video.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         video.description?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = filterStatus === 'all' || video.status === filterStatus;
    return matchesSearch && matchesStatus;
  });

  // 排序
  const sortedVideos = React.useMemo(() => {
    if (!sortConfig) return filteredVideos;

    return [...filteredVideos].sort((a, b) => {
      const aValue = a[sortConfig.key];
      const bValue = b[sortConfig.key];

      if (aValue < bValue) {
        return sortConfig.direction === 'asc' ? -1 : 1;
      }
      if (aValue > bValue) {
        return sortConfig.direction === 'asc' ? 1 : -1;
      }
      return 0;
    });
  }, [filteredVideos, sortConfig]);

  // 分页
  const totalPages = Math.ceil(sortedVideos.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const paginatedVideos = sortedVideos.slice(startIndex, startIndex + itemsPerPage);

  const handleSort = (key: keyof Video) => {
    setSortConfig(current => {
      if (current?.key === key) {
        return {
          key,
          direction: current.direction === 'asc' ? 'desc' : 'asc'
        };
      }
      return { key, direction: 'asc' };
    });
  };

  const handleSelectVideo = (videoId: string) => {
    setSelectedVideos(current => 
      current.includes(videoId)
        ? current.filter(id => id !== videoId)
        : [...current, videoId]
    );
  };

  const handleSelectAll = () => {
    if (selectedVideos.length === paginatedVideos.length) {
      setSelectedVideos([]);
    } else {
      setSelectedVideos(paginatedVideos.map(video => video.id));
    }
  };

  const handleBatchDelete = () => {
    if (selectedVideos.length === 0) return;
    if (confirm(`确定要删除选中的 ${selectedVideos.length} 个视频吗？`)) {
      setVideos(current => current.filter(video => !selectedVideos.includes(video.id)));
      setSelectedVideos([]);
    }
  };

  const handleDeleteVideo = (videoId: string) => {
    if (confirm('确定要删除这个视频吗？')) {
      setVideos(current => current.filter(video => video.id !== videoId));
    }
  };

  const getStatusBadge = (status: string, progress?: number) => {
    switch (status) {
      case 'completed':
        return <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">已完成</span>;
      case 'processing':
        return <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full">处理中</span>;
      case 'uploading':
        return (
          <span className="px-2 py-1 bg-yellow-100 text-yellow-800 text-xs rounded-full">
            上传中 {progress}%
          </span>
        );
      case 'failed':
        return <span className="px-2 py-1 bg-red-100 text-red-800 text-xs rounded-full">失败</span>;
      default:
        return <span className="px-2 py-1 bg-gray-100 text-gray-800 text-xs rounded-full">未知</span>;
    }
  };

  const formatDuration = (seconds: number) => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-800">视频列表</h1>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setViewMode('list')}
            className={`p-2 rounded ${viewMode === 'list' ? 'bg-blue-100 text-blue-600' : 'text-gray-600 hover:bg-gray-100'}`}
          >
            <i className="fas fa-list"></i>
          </button>
          <button
            onClick={() => setViewMode('grid')}
            className={`p-2 rounded ${viewMode === 'grid' ? 'bg-blue-100 text-blue-600' : 'text-gray-600 hover:bg-gray-100'}`}
          >
            <i className="fas fa-th-large"></i>
          </button>
        </div>
      </div>

      {/* 搜索和过滤 */}
      <div className="bg-white rounded-lg shadow-sm p-4">
        <div className="flex flex-wrap gap-4 items-center">
          <div className="flex-1 min-w-64">
            <div className="relative">
              <input
                type="text"
                placeholder="搜索视频标题或描述..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="input-field pl-10"
              />
              <i className="fas fa-search absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400"></i>
            </div>
          </div>
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="input-field w-32"
          >
            <option value="all">全部状态</option>
            <option value="completed">已完成</option>
            <option value="processing">处理中</option>
            <option value="uploading">上传中</option>
            <option value="failed">失败</option>
          </select>
          <select
            value={itemsPerPage}
            onChange={(e) => setItemsPerPage(Number(e.target.value))}
            className="input-field w-24"
          >
            <option value={10}>10</option>
            <option value={20}>20</option>
            <option value={50}>50</option>
          </select>
        </div>
      </div>

      {/* 批量操作 */}
      {selectedVideos.length > 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <span className="text-blue-800">
              已选择 {selectedVideos.length} 个视频
            </span>
            <div className="flex space-x-2">
              <button className="btn-secondary text-sm">
                <i className="fas fa-download mr-1"></i>
                批量下载
              </button>
              <button 
                onClick={handleBatchDelete}
                className="px-3 py-1 bg-red-600 text-white text-sm rounded hover:bg-red-700"
              >
                <i className="fas fa-trash mr-1"></i>
                批量删除
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 视频列表 */}
      <div className="bg-white rounded-lg shadow-sm overflow-hidden">
        {viewMode === 'list' ? (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left">
                    <input
                      type="checkbox"
                      checked={selectedVideos.length === paginatedVideos.length && paginatedVideos.length > 0}
                      onChange={handleSelectAll}
                      className="rounded"
                    />
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    缩略图
                  </th>
                  <th 
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    onClick={() => handleSort('title')}
                  >
                    <div className="flex items-center">
                      标题
                      {sortConfig?.key === 'title' && (
                        <i className={`fas fa-chevron-${sortConfig.direction === 'asc' ? 'up' : 'down'} ml-1`}></i>
                      )}
                    </div>
                  </th>
                  <th 
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    onClick={() => handleSort('duration')}
                  >
                    <div className="flex items-center">
                      时长
                      {sortConfig?.key === 'duration' && (
                        <i className={`fas fa-chevron-${sortConfig.direction === 'asc' ? 'up' : 'down'} ml-1`}></i>
                      )}
                    </div>
                  </th>
                  <th 
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    onClick={() => handleSort('size')}
                  >
                    <div className="flex items-center">
                      大小
                      {sortConfig?.key === 'size' && (
                        <i className={`fas fa-chevron-${sortConfig.direction === 'asc' ? 'up' : 'down'} ml-1`}></i>
                      )}
                    </div>
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    状态
                  </th>
                  <th 
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    onClick={() => handleSort('created_at')}
                  >
                    <div className="flex items-center">
                      创建时间
                      {sortConfig?.key === 'created_at' && (
                        <i className={`fas fa-chevron-${sortConfig.direction === 'asc' ? 'up' : 'down'} ml-1`}></i>
                      )}
                    </div>
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    操作
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {paginatedVideos.map((video) => (
                  <tr key={video.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4">
                      <input
                        type="checkbox"
                        checked={selectedVideos.includes(video.id)}
                        onChange={() => handleSelectVideo(video.id)}
                        className="rounded"
                      />
                    </td>
                    <td className="px-6 py-4">
                      <div className="relative w-16 h-12 bg-gray-200 rounded overflow-hidden">
                        <img
                          src={video.thumbnail}
                          alt={video.title}
                          className="w-full h-full object-cover"
                        />
                        <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-30 opacity-0 hover:opacity-100 transition-opacity cursor-pointer"
                             onClick={() => setPlayingVideo(playingVideo === video.id ? null : video.id)}>
                          <i className="fas fa-play text-white"></i>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div>
                        <div className="text-sm font-medium text-gray-900 truncate max-w-xs">
                          {video.title}
                        </div>
                        <div className="text-sm text-gray-500 truncate max-w-xs">
                          {video.description}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900">
                      {formatDuration(video.duration || 0)}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900">
                      {formatFileSize(video.size)}
                    </td>
                    <td className="px-6 py-4">
                      {getStatusBadge(video.status, video.progress)}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">
                      {formatRelativeTime(video.created_at)}
                    </td>
                    <td className="px-6 py-4 text-sm font-medium">
                      <div className="flex space-x-2">
                        <button className="text-blue-600 hover:text-blue-900">
                          <i className="fas fa-eye"></i>
                        </button>
                        <button className="text-green-600 hover:text-green-900">
                          <i className="fas fa-download"></i>
                        </button>
                        <button className="text-yellow-600 hover:text-yellow-900">
                          <i className="fas fa-edit"></i>
                        </button>
                        <button 
                          onClick={() => handleDeleteVideo(video.id)}
                          className="text-red-600 hover:text-red-900"
                        >
                          <i className="fas fa-trash"></i>
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 p-6">
            {paginatedVideos.map((video) => (
              <div key={video.id} className="bg-white border border-gray-200 rounded-lg overflow-hidden hover:shadow-md transition-shadow">
                <div className="relative">
                  <img
                    src={video.thumbnail}
                    alt={video.title}
                    className="w-full h-32 object-cover"
                  />
                  <div className="absolute top-2 right-2">
                    <input
                      type="checkbox"
                      checked={selectedVideos.includes(video.id)}
                      onChange={() => handleSelectVideo(video.id)}
                      className="rounded"
                    />
                  </div>
                  <div className="absolute bottom-2 right-2 bg-black bg-opacity-75 text-white text-xs px-2 py-1 rounded">
                    {formatDuration(video.duration || 0)}
                  </div>
                </div>
                <div className="p-4">
                  <h3 className="font-medium text-gray-900 truncate mb-1">{video.title}</h3>
                  <p className="text-sm text-gray-500 truncate mb-2">{video.description}</p>
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-xs text-gray-500">{formatFileSize(video.size)}</span>
                    {getStatusBadge(video.status, video.progress)}
                  </div>
                  <div className="text-xs text-gray-500 mb-3">
                    {formatRelativeTime(video.created_at)}
                  </div>
                  <div className="flex justify-between">
                    <button className="text-blue-600 hover:text-blue-900 text-sm">
                      <i className="fas fa-eye mr-1"></i>预览
                    </button>
                    <button className="text-green-600 hover:text-green-900 text-sm">
                      <i className="fas fa-download mr-1"></i>下载
                    </button>
                    <button 
                      onClick={() => handleDeleteVideo(video.id)}
                      className="text-red-600 hover:text-red-900 text-sm"
                    >
                      <i className="fas fa-trash mr-1"></i>删除
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* 分页 */}
        {totalPages > 1 && (
          <div className="px-6 py-4 border-t border-gray-200 flex items-center justify-between">
            <div className="text-sm text-gray-700">
              显示 {startIndex + 1} 到 {Math.min(startIndex + itemsPerPage, sortedVideos.length)} 条，
              共 {sortedVideos.length} 条记录
            </div>
            <div className="flex space-x-1">
              <button
                onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                disabled={currentPage === 1}
                className="px-3 py-1 border border-gray-300 rounded text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
              >
                上一页
              </button>
              {Array.from({ length: totalPages }, (_, i) => i + 1)
                .filter(page => 
                  page === 1 || 
                  page === totalPages || 
                  (page >= currentPage - 2 && page <= currentPage + 2)
                )
                .map((page, index, array) => (
                  <React.Fragment key={page}>
                    {index > 0 && array[index - 1] !== page - 1 && (
                      <span className="px-3 py-1 text-gray-500">...</span>
                    )}
                    <button
                      onClick={() => setCurrentPage(page)}
                      className={`px-3 py-1 border text-sm rounded ${
                        currentPage === page
                          ? 'bg-blue-600 text-white border-blue-600'
                          : 'border-gray-300 hover:bg-gray-50'
                      }`}
                    >
                      {page}
                    </button>
                  </React.Fragment>
                ))
              }
              <button
                onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                disabled={currentPage === totalPages}
                className="px-3 py-1 border border-gray-300 rounded text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
              >
                下一页
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default VideoList;