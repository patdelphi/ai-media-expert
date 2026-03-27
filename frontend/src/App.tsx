import React, { useState } from 'react';
import { Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import UserMenu from './components/UserMenu';
// import { BreadcrumbItem } from './types';

// 页面组件导入
import Dashboard from './pages/Dashboard';
import VideoUpload from './pages/VideoUpload';
import VideoDownload from './pages/VideoDownload';
import VideoList from './pages/VideoList';
import VideoAnalysis from './pages/VideoAnalysis';
import SystemConfig from './pages/SystemConfig';
import Profile from './pages/Profile';
import Settings from './pages/Settings';
import Login from './pages/Login';
import Register from './pages/Register';

const App: React.FC = () => {
  const location = useLocation();
  // 暂时屏蔽未使用的状态，避免 TS 报错
  // const [activeMenu, setActiveMenu] = useState<string | null>(null);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  // const [currentPath, setCurrentPath] = useState<BreadcrumbItem[]>([
  //   { label: '首页', path: '/' },
  //   { label: '数据看板', path: '/dashboard' },
  //   { label: '概览仪表盘', path: '/dashboard/overview' }
  // ]);

  // 检查是否为认证页面
  const isAuthPage = location.pathname === '/login' || location.pathname === '/register';

  const toggleSidebar = () => {
    setIsSidebarCollapsed(!isSidebarCollapsed);
  };

  // const handleMenuHover = (menu: string) => {
  //   setActiveMenu(menu);
  // };

  // const handleMenuLeave = () => {
  //   setActiveMenu(null);
  // };

  // const getSubMenuItems = (menu: string): string[] => {
  //   switch (menu) {
  //     case '数据看板':
  //       return ['概览仪表盘', '用户行为看板', '转化漏斗看板', '留存分析看板'];
  //     case '视频管理':
  //       return ['视频上传', '视频下载', '视频列表', '视频解析'];
  //     case '系统设置':
  //       return ['系统配置', '用户管理', '角色权限', '日志审计'];
  //     case '帮助中心':
  //       return ['文档中心', '常见问题', '视频教程', '联系我们'];
  //     default:
  //       return [];
  //   }
  // };

  // 如果是认证页面，只显示页面内容
  if (isAuthPage) {
    return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
      </Routes>
    </AuthProvider>
  );
  }

  return (
    <AuthProvider>
      <div className="min-h-screen flex flex-col bg-gray-50">
        {/* 顶部导航栏 */}
        <header className="bg-white shadow-sm">
          {/* 第一行导航 */}
          <div className="container mx-auto px-4 h-16 flex items-center justify-between">
            {/* Logo 和网站名称 */}
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-blue-600 rounded flex items-center justify-center">
                <i className="fas fa-video text-white"></i>
              </div>
              <h1 className="text-xl font-bold text-gray-800">AI媒体专家</h1>
            </div>

            {/* 搜索框 */}
            <div className="flex-1 max-w-xl mx-4">
              <div className="relative">
                <input
                  type="text"
                  placeholder="搜索功能、文档..."
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-button focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                <i className="fas fa-search absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400"></i>
              </div>
            </div>

            {/* 右侧功能区 */}
            <UserMenu />
          </div>
        </header>

      {/* 主体内容 */}
      <main className="flex-1 container mx-auto px-4 py-6 flex">
        {/* 左侧边栏 */}
        <aside
          className={`bg-white shadow-sm rounded-lg mr-6 transition-all duration-300 ${
            isSidebarCollapsed ? 'w-16' : 'w-64'
          }`}
        >
          <div className="p-4 border-b border-gray-200 flex justify-between items-center">
            <div className="flex justify-between items-center">
              <h2 className={`text-lg font-medium text-gray-800 ${isSidebarCollapsed ? 'hidden' : ''}`}>
                功能导航
              </h2>
              <button
                onClick={toggleSidebar}
                className={`text-gray-500 hover:text-gray-700 rounded-button ${
                  isSidebarCollapsed ? 'w-full flex justify-center' : ''
                }`}
              >
                <i className={`fas ${isSidebarCollapsed ? 'fa-chevron-right' : 'fa-chevron-left'}`}></i>
              </button>
            </div>
          </div>
          <nav className="p-2">
            {[
              { name: '数据概览', icon: 'fa-chart-pie', path: '/dashboard' },
              { name: '视频上传', icon: 'fa-upload', path: '/video/upload' },
              { name: '视频下载', icon: 'fa-download', path: '/video/download' },
              { name: '视频列表', icon: 'fa-list', path: '/video/list' },
              { name: '视频解析', icon: 'fa-search', path: '/video/analysis' },
              { name: '系统配置', icon: 'fa-cog', path: '/system/config' },
            ].map((item) => (
              <a
                key={item.name}
                href={item.path}
                className={`flex items-center px-3 py-2 text-sm rounded-md mb-1 ${
                  window.location.pathname === item.path
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-600 hover:bg-gray-100'
                } ${isSidebarCollapsed ? 'justify-center' : ''}`}
                onClick={isSidebarCollapsed ? toggleSidebar : undefined}
              >
                <i className={`fas ${item.icon} ${isSidebarCollapsed ? '' : 'mr-3'} text-gray-500`}></i>
                <span className={isSidebarCollapsed ? 'hidden' : ''}>{item.name}</span>
              </a>
            ))}
          </nav>
        </aside>

        {/* 右侧主内容区 */}
        <div className="flex-1">
          {/* 路由内容 */}
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            } />
            <Route path="/profile" element={
              <ProtectedRoute>
                <Profile />
              </ProtectedRoute>
            } />
            <Route path="/settings" element={
              <ProtectedRoute>
                <Settings />
              </ProtectedRoute>
            } />
            <Route path="/video/upload" element={
              <ProtectedRoute>
                <VideoUpload />
              </ProtectedRoute>
            } />
            <Route path="/video/download" element={
              <ProtectedRoute>
                <VideoDownload />
              </ProtectedRoute>
            } />
            <Route path="/video/list" element={
              <ProtectedRoute>
                <VideoList />
              </ProtectedRoute>
            } />
            <Route path="/video/analysis" element={
              <ProtectedRoute>
                <VideoAnalysis />
              </ProtectedRoute>
            } />
            <Route path="/system/config" element={
              <ProtectedRoute requireRoles={['admin']}>
                <SystemConfig />
              </ProtectedRoute>
            } />
          </Routes>
        </div>
      </main>
      </div>
    </AuthProvider>
  );
};

export default App;
