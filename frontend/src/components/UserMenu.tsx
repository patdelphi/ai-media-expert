import React, { useState, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useClickOutside } from '../hooks';

const UserMenu: React.FC = () => {
  const { user, isAuthenticated, logout } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  useClickOutside(menuRef, () => setIsOpen(false));

  const handleLogout = async () => {
    try {
      await logout();
      navigate('/login');
    } catch (error) {
      console.error('Logout error:', error);
    }
  };

  if (!isAuthenticated) {
    return (
      <div className="flex items-center space-x-4">
        <a
          href="https://github.com"
          target="_blank"
          rel="noopener noreferrer"
          className="text-gray-600 hover:text-gray-900"
        >
          <i className="fab fa-github text-xl"></i>
        </a>
        <Link
          to="/login"
          className="text-sm font-medium text-gray-700 hover:text-gray-900"
        >
          登录
        </Link>
        <Link
          to="/register"
          className="btn-primary text-sm"
        >
          注册
        </Link>
      </div>
    );
  }

  return (
    <div className="flex items-center space-x-4">
      <a
        href="https://github.com"
        target="_blank"
        rel="noopener noreferrer"
        className="text-gray-600 hover:text-gray-900"
      >
        <i className="fab fa-github text-xl"></i>
      </a>
      
      {/* 用户菜单 */}
      <div className="relative" ref={menuRef}>
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="flex items-center space-x-2 text-sm font-medium text-gray-700 hover:text-gray-900 focus:outline-none"
        >
          <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
            {user?.avatar_url ? (
              <img
                src={user.avatar_url}
                alt={user.full_name || user.username || 'User'}
                className="w-8 h-8 rounded-full object-cover"
              />
            ) : (
              <i className="fas fa-user text-white text-sm"></i>
            )}
          </div>
          <span className="hidden md:block">
            {user?.full_name || user?.username || user?.email}
          </span>
          <i className={`fas fa-chevron-down transition-transform ${isOpen ? 'rotate-180' : ''}`}></i>
        </button>

        {/* 下拉菜单 */}
        {isOpen && (
          <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg py-1 z-50 border border-gray-200">
            <div className="px-4 py-2 border-b border-gray-100">
              <p className="text-sm font-medium text-gray-900">
                {user?.full_name || user?.username}
              </p>
              <p className="text-sm text-gray-500">{user?.email}</p>
              <span className={`inline-block px-2 py-1 text-xs rounded-full mt-1 ${
                user?.role === 'admin' 
                  ? 'bg-red-100 text-red-800' 
                  : 'bg-blue-100 text-blue-800'
              }`}>
                {user?.role === 'admin' ? '管理员' : '用户'}
              </span>
            </div>
            
            <Link
              to="/profile"
              className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
              onClick={() => setIsOpen(false)}
            >
              <i className="fas fa-user mr-2"></i>
              个人资料
            </Link>
            
            <Link
              to="/settings"
              className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
              onClick={() => setIsOpen(false)}
            >
              <i className="fas fa-cog mr-2"></i>
              账户设置
            </Link>
            
            {user?.role === 'admin' && (
              <Link
                to="/system/config"
                className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                onClick={() => setIsOpen(false)}
              >
                <i className="fas fa-tools mr-2"></i>
                系统管理
              </Link>
            )}
            
            <div className="border-t border-gray-100 mt-1">
              <button
                onClick={handleLogout}
                className="block w-full text-left px-4 py-2 text-sm text-red-700 hover:bg-red-50"
              >
                <i className="fas fa-sign-out-alt mr-2"></i>
                退出登录
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default UserMenu;