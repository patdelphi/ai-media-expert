import { apiService, ApiResponse } from './api';

// 用户类型定义
export interface User {
  id: number;
  email: string;
  username?: string;
  full_name?: string;
  avatar_url?: string;
  is_active: boolean;
  is_verified: boolean;
  role: string;
  last_login_at?: string;
  created_at: string;
  updated_at: string;
}

// 登录请求类型
export interface LoginRequest {
  username: string; // 可以是邮箱或用户名
  password: string;
}

// 注册请求类型
export interface RegisterRequest {
  email: string;
  username?: string;
  password: string;
  full_name?: string;
}

// Token响应类型
export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

// 密码修改请求类型
export interface PasswordChangeRequest {
  current_password: string;
  new_password: string;
}

// 用户更新请求类型
export interface UserUpdateRequest {
  username?: string;
  full_name?: string;
  avatar_url?: string;
}

class AuthService {
  // 用户注册
  async register(data: RegisterRequest): Promise<ApiResponse<User>> {
    return apiService.post('/auth/register', data);
  }

  // 用户登录
  async login(data: LoginRequest): Promise<ApiResponse<TokenResponse>> {
    // 后端使用OAuth2PasswordRequestForm，需要转换格式
    const formData = new FormData();
    formData.append('username', data.username);
    formData.append('password', data.password);

    const response = await fetch(`${apiService['api'].defaults.baseURL}/auth/login`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.message || 'Login failed');
    }

    const result = await response.json();
    
    // 保存tokens和用户信息
    if (result.code === 200) {
      const { access_token, refresh_token, user } = result.data;
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);
      localStorage.setItem('user', JSON.stringify(user));
    }

    return result;
  }

  // 用户登出
  async logout(): Promise<void> {
    try {
      await apiService.post('/auth/logout');
    } catch (error) {
      // 即使后端登出失败，也要清除本地tokens
      console.error('Logout error:', error);
    } finally {
      this.clearAuthData();
    }
  }

  // 刷新token
  async refreshToken(refreshToken: string): Promise<ApiResponse<TokenResponse>> {
    const response = await apiService.post('/auth/refresh', {
      refresh_token: refreshToken,
    });

    if (response.code === 200) {
      const { access_token, refresh_token, user } = response.data;
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);
      localStorage.setItem('user', JSON.stringify(user));
    }

    return response;
  }

  // 获取当前用户信息
  async getCurrentUser(): Promise<ApiResponse<User>> {
    return apiService.get('/auth/me');
  }

  // 更新用户信息
  async updateUser(data: UserUpdateRequest): Promise<ApiResponse<User>> {
    return apiService.put('/users/me', data);
  }

  // 修改密码
  async changePassword(data: PasswordChangeRequest): Promise<ApiResponse<any>> {
    return apiService.post('/users/change-password', data);
  }

  // 上传头像
  async uploadAvatar(
    file: File,
    onProgress?: (progress: number) => void
  ): Promise<ApiResponse<{ avatar_url: string }>> {
    return apiService.upload('/users/me/avatar', file, onProgress);
  }

  // 检查是否已登录
  isAuthenticated(): boolean {
    const token = localStorage.getItem('access_token');
    const user = localStorage.getItem('user');
    return !!(token && user);
  }

  // 获取当前用户（从localStorage）
  getCurrentUserFromStorage(): User | null {
    const userStr = localStorage.getItem('user');
    if (userStr) {
      try {
        return JSON.parse(userStr);
      } catch (error) {
        console.error('Error parsing user data:', error);
        this.clearAuthData();
      }
    }
    return null;
  }

  // 获取访问token
  getAccessToken(): string | null {
    return localStorage.getItem('access_token');
  }

  // 获取刷新token
  getRefreshToken(): string | null {
    return localStorage.getItem('refresh_token');
  }

  // 清除认证数据
  clearAuthData(): void {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
  }

  // 检查token是否即将过期（提前5分钟刷新）
  shouldRefreshToken(): boolean {
    const token = this.getAccessToken();
    if (!token) return false;

    try {
      // 解析JWT token（简单解析，不验证签名）
      const payload = JSON.parse(atob(token.split('.')[1]));
      const exp = payload.exp * 1000; // 转换为毫秒
      const now = Date.now();
      const fiveMinutes = 5 * 60 * 1000;

      return exp - now < fiveMinutes;
    } catch (error) {
      console.error('Error parsing token:', error);
      return true; // 解析失败，尝试刷新
    }
  }

  // 自动刷新token
  async autoRefreshToken(): Promise<boolean> {
    const refreshToken = this.getRefreshToken();
    if (!refreshToken) return false;

    try {
      await this.refreshToken(refreshToken);
      return true;
    } catch (error) {
      console.error('Auto refresh token failed:', error);
      this.clearAuthData();
      return false;
    }
  }
}

// 创建认证服务实例
export const authService = new AuthService();
export default authService;
