import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requireAuth?: boolean;
  requireRoles?: string[];
  fallback?: React.ReactNode;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  requireAuth = true,
  requireRoles = [],
  fallback
}) => {
  const { isAuthenticated, isLoading, user } = useAuth();
  const location = useLocation();

  // 显示加载状态
  if (isLoading) {
    return (
      fallback || (
        <div className="min-h-screen flex items-center justify-center bg-gray-50">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">加载中...</p>
          </div>
        </div>
      )
    );
  }

  // 需要认证但未登录
  if (requireAuth && !isAuthenticated) {
    return (
      <Navigate 
        to="/login" 
        state={{ from: location.pathname }} 
        replace 
      />
    );
  }

  // 检查角色权限
  if (requireAuth && isAuthenticated && requireRoles.length > 0) {
    const userRole = user?.role;
    if (!userRole || !requireRoles.includes(userRole)) {
      // 直接重定向到dashboard，避免显示空白页面
      return <Navigate to="/dashboard" replace />;
    }
  }

  // 已认证或不需要认证，渲染子组件
  return <>{children}</>;
};

export default ProtectedRoute;