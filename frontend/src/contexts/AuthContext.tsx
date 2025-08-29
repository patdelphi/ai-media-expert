import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { authService, User } from '../services/auth';

// 认证状态类型
interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

// 认证上下文类型
interface AuthContextType extends AuthState {
  login: (username: string, password: string) => Promise<void>;
  register: (email: string, username: string, password: string, fullName?: string) => Promise<void>;
  logout: () => Promise<void>;
  updateUser: (data: Partial<User>) => Promise<void>;
  clearError: () => void;
  refreshUser: () => Promise<void>;
}

// 创建认证上下文
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// 认证提供者组件
export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [state, setState] = useState<AuthState>({
    user: null,
    isAuthenticated: false,
    isLoading: true,
    error: null,
  });

  // 初始化认证状态
  useEffect(() => {
    initializeAuth();
  }, []);

  // 自动刷新token
  useEffect(() => {
    if (state.isAuthenticated) {
      const interval = setInterval(() => {
        if (authService.shouldRefreshToken()) {
          authService.autoRefreshToken().catch(() => {
            // 刷新失败，登出用户
            handleLogout();
          });
        }
      }, 60000); // 每分钟检查一次

      return () => clearInterval(interval);
    }
  }, [state.isAuthenticated]);

  // 初始化认证状态
  const initializeAuth = async () => {
    try {
      if (authService.isAuthenticated()) {
        const user = authService.getCurrentUserFromStorage();
        if (user) {
          setState({
            user,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          });

          // 验证token是否有效
          try {
            const response = await authService.getCurrentUser();
            if (response.code === 200) {
              setState(prev => ({
                ...prev,
                user: response.data,
              }));
            }
          } catch (error) {
            // token无效，清除认证状态
            handleLogout();
          }
        } else {
          setState(prev => ({
            ...prev,
            isLoading: false,
          }));
        }
      } else {
        setState(prev => ({
          ...prev,
          isLoading: false,
        }));
      }
    } catch (error) {
      console.error('Initialize auth error:', error);
      setState({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        error: 'Authentication initialization failed',
      });
    }
  };

  // 登录
  const login = async (username: string, password: string) => {
    setState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      const response = await authService.login({ username, password });
      
      if (response.code === 200) {
        setState({
          user: response.data.user,
          isAuthenticated: true,
          isLoading: false,
          error: null,
        });
      } else {
        throw new Error(response.message || 'Login failed');
      }
    } catch (error: any) {
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: error.message || 'Login failed',
      }));
      throw error;
    }
  };

  // 注册
  const register = async (email: string, username: string, password: string, fullName?: string) => {
    setState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      const response = await authService.register({
        email,
        username,
        password,
        full_name: fullName,
      });

      if (response.code === 200) {
        // 注册成功后自动登录
        await login(username, password);
      } else {
        throw new Error(response.message || 'Registration failed');
      }
    } catch (error: any) {
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: error.message || 'Registration failed',
      }));
      throw error;
    }
  };

  // 登出
  const logout = async () => {
    setState(prev => ({ ...prev, isLoading: true }));

    try {
      await authService.logout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      handleLogout();
    }
  };

  // 处理登出状态更新
  const handleLogout = () => {
    authService.clearAuthData();
    setState({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
    });
  };

  // 更新用户信息
  const updateUser = async (data: Partial<User>) => {
    if (!state.user) return;

    setState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      const response = await authService.updateUser(data);
      
      if (response.code === 200) {
        const updatedUser = response.data;
        localStorage.setItem('user', JSON.stringify(updatedUser));
        
        setState(prev => ({
          ...prev,
          user: updatedUser,
          isLoading: false,
        }));
      } else {
        throw new Error(response.message || 'Update failed');
      }
    } catch (error: any) {
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: error.message || 'Update failed',
      }));
      throw error;
    }
  };

  // 刷新用户信息
  const refreshUser = async () => {
    if (!state.isAuthenticated) return;

    try {
      const response = await authService.getCurrentUser();
      if (response.code === 200) {
        const user = response.data;
        localStorage.setItem('user', JSON.stringify(user));
        setState(prev => ({
          ...prev,
          user,
        }));
      }
    } catch (error) {
      console.error('Refresh user error:', error);
      // 如果刷新失败，可能是token过期，尝试自动刷新
      const refreshSuccess = await authService.autoRefreshToken();
      if (!refreshSuccess) {
        handleLogout();
      }
    }
  };

  // 清除错误
  const clearError = () => {
    setState(prev => ({ ...prev, error: null }));
  };

  const contextValue: AuthContextType = {
    ...state,
    login,
    register,
    logout,
    updateUser,
    clearError,
    refreshUser,
  };

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
};

// 使用认证上下文的Hook
export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthContext;