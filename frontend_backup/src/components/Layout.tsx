import React, { useState, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import * as echarts from 'echarts';
import { BreadcrumbItem } from '@/types';

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const [activeMenu, setActiveMenu] = useState<string | null>(null);
  const [currentPath, setCurrentPath] = useState<BreadcrumbItem[]>([]);

  // 根据当前路径更新面包屑
  useEffect(() => {
    const pathMap: { [key: string]: BreadcrumbItem[] } = {
      '/': [{ label: '首页', path: '/' }, { label: '数据看板', path: '/dashboard' }],
      '/dashboard': [{ label: '首页', path: '/' }, { label: '数据看板', path: '/dashboard' }],
      '/upload': [{ label: '首页', path: '/' }, { label: '视频管理', path: '/videos' }, { label: '视频上传', path: '/upload' }],
      '/download': [{ label: '首页', path: '/' }, { label: '视频管理', path: '/videos' }, { label: '视频下载', path: '/download' }],
      '/videos': [{ label: '首页', path: '/' }, { label: '视频管理', path: '/videos' }, { label: '视频列表', path: '/videos' }],
      '/analysis': [{ label: '首页', path: '/' }, { label: '视频管理', path: '/videos' }, { label: '视频解析', path: '/analysis' }],
      '/settings': [{ label: '首页', path: '/' }, { label: '系统管理', path: '/settings' }, { label: '系统配置', path: '/settings' }],
    };
    
    const currentPathKey = location.pathname.startsWith('/analysis') ? '/analysis' : location.pathname;
    setCurrentPath(pathMap[currentPathKey] || [{ label: '首页', path: '/' }]);
  }, [location.pathname]);



  const handleMenuHover = (menu: string) => {
    setActiveMenu(menu);
  };

  const handleMenuLeave = () => {
    setActiveMenu(null);
  };

  const getSubMenuItems = (menu: string): { label: string; path: string }[] => {
    switch (menu) {
      case '数据看板':
        return [
          { label: '概览仪表盘', path: '/dashboard' },
          { label: '数据统计', path: '/dashboard/stats' },
          { label: '实时监控', path: '/dashboard/monitor' }
        ];
      case '视频管理':
        return [
          { label: '视频上传', path: '/upload' },
          { label: '视频下载', path: '/download' },
          { label: '视频列表', path: '/videos' },
          { label: '视频解析', path: '/analysis' }
        ];
      case '系统管理':
        return [
          { label: '系统配置', path: '/settings' },
          { label: '用户管理', path: '/users' },
          { label: '日志管理', path: '/settings/logs' }
        ];
      case '帮助中心':
        return [
          { label: '使用文档', path: '/help/docs' },
          { label: '常见问题', path: '/help/faq' },
          { label: '联系我们', path: '/help/contact' }
        ];
      default:
        return [];
    }
  };



  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        {/* 简化的头部导航 */}
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          {/* Logo 和网站名称 */}
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
              <i className="fas fa-video text-white text-sm"></i>
            </div>
            <h1 className="text-xl font-semibold text-gray-900">AI Media Expert</h1>
          </div>
          
          {/* 右侧功能区 */}
          <div className="flex items-center space-x-6">
            <div className="flex items-center space-x-2 text-gray-600 hover:text-gray-900 cursor-pointer">
              <div className="w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center">
                <i className="fas fa-user text-gray-600 text-sm"></i>
              </div>
              <span className="text-sm font-medium">管理员</span>
            </div>
          </div>
        </div>
        
        {/* 简化的导航菜单 */}
            <div className="bg-gray-50 border-b border-gray-200">
              <div className="max-w-7xl mx-auto px-6 h-12 flex items-center">
             <nav className="flex items-center space-x-8">
              {[
                { label: '数据看板', path: '/dashboard' },
                { label: '视频管理', submenu: [
                  { label: '视频上传', path: '/upload' },
                  { label: '视频下载', path: '/download' },
                  { label: '视频列表', path: '/videos' },
                  { label: '视频解析', path: '/analysis' }
                ]},
                { label: '系统管理', submenu: [
                  { label: '系统配置', path: '/settings' },
                  { label: '用户管理', path: '/users' }
                ]}
              ].map((menu) => (
                <div
                  key={menu.label}
                  className="relative"
                  onMouseEnter={() => handleMenuHover(menu.label)}
                  onMouseLeave={handleMenuLeave}
                >
                  {menu.submenu ? (
                    <>
                      <button className={`px-3 py-2 text-sm font-medium text-gray-700 hover:text-blue-600 whitespace-nowrap ${
                        activeMenu === menu.label ? 'text-blue-600' : ''
                      }`}>
                        {menu.label}
                        <i className="fas fa-chevron-down ml-1 text-xs"></i>
                      </button>
                      {activeMenu === menu.label && (
                        <div className="absolute left-0 mt-1 w-40 bg-white shadow-lg rounded-lg border border-gray-200 z-10">
                          {menu.submenu.map((item) => (
                            <Link
                              key={item.path}
                              to={item.path}
                              className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 first:rounded-t-lg last:rounded-b-lg"
                            >
                              {item.label}
                            </Link>
                          ))}
                        </div>
                      )}
                    </>
                  ) : (
                    <Link
                      to={menu.path!}
                      className="px-3 py-2 text-sm font-medium text-gray-700 hover:text-blue-600 whitespace-nowrap"
                    >
                      {menu.label}
                    </Link>
                  )}
                </div>
              ))}
            </nav>
          </div>
        </div>
      </header>

      {/* 主体内容 */}
      <main className="flex-1 w-full px-6 py-6">
        {/* 主内容区 */}
        <div className="max-w-7xl mx-auto w-full">
          {/* 面包屑导航 */}
          <nav className="mb-6 flex items-center text-sm text-gray-600">
            <Link to="/dashboard" className="hover:text-blue-600 flex items-center">
              <i className="fas fa-home mr-1"></i>
              首页
            </Link>
            {currentPath.map((item, index) => (
              <React.Fragment key={index}>
                <i className="fas fa-chevron-right mx-2 text-gray-400"></i>
                {item.path ? (
                  <Link to={item.path} className="hover:text-blue-600 flex items-center">
                    {item.label}
                  </Link>
                ) : (
                  <span className="text-gray-900 font-medium flex items-center">{item.label}</span>
                )}
              </React.Fragment>
            ))}
          </nav>

          {/* 页面内容 */}
          {children}
        </div>
      </main>

      {/* 简化的底部信息栏 */}
         <footer className="bg-white border-t border-gray-200 py-4">
           <div className="max-w-7xl mx-auto px-6">
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 rounded-full bg-green-500"></div>
                <span className="text-sm text-gray-600">系统运行正常</span>
              </div>
              <span className="text-sm text-gray-500">© 2024 AI Media Expert</span>
            </div>
            <div className="text-sm text-gray-500">
              v1.0.0
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Layout;