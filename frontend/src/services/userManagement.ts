import { apiService, ApiResponse } from './api';

// 用户列表项类型
export interface UserListItem {
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
}

// 用户列表响应类型
export interface UserListResponse {
  items: UserListItem[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

// 用户搜索参数类型
export interface UserSearchParams {
  page?: number;
  size?: number;
  search?: string;
  role?: string;
  is_active?: boolean;
  is_verified?: boolean;
}

// 管理员创建用户请求类型
export interface AdminUserCreateRequest {
  email?: string;
  username?: string;
  full_name?: string;
  password?: string;
  role?: string;
  is_active?: boolean;
  is_verified?: boolean;
}

// 管理员更新用户请求类型
export interface AdminUserUpdateRequest {
  email?: string;
  username?: string;
  full_name?: string;
  password?: string;
  role?: string;
  is_active?: boolean;
  is_verified?: boolean;
}

// 用户状态更新请求类型
export interface UserStatusUpdateRequest {
  is_active: boolean;
  reason?: string;
}

// 用户详情响应类型
export interface UserDetailResponse {
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

class UserManagementService {
  /**
   * 获取用户列表
   */
  async getUsersList(params: UserSearchParams = {}): Promise<ApiResponse<UserListResponse>> {
    const queryParams = new URLSearchParams();
    
    if (params.page) queryParams.append('page', params.page.toString());
    if (params.size) queryParams.append('size', params.size.toString());
    if (params.search) queryParams.append('search', params.search);
    if (params.role) queryParams.append('role', params.role);
    if (params.is_active !== undefined) queryParams.append('is_active', params.is_active.toString());
    if (params.is_verified !== undefined) queryParams.append('is_verified', params.is_verified.toString());
    
    const url = `/users/list${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
    return apiService.get<UserListResponse>(url);
  }

  /**
   * 获取用户详情
   */
  async getUserById(userId: number): Promise<ApiResponse<UserDetailResponse>> {
    return apiService.get<UserDetailResponse>(`/users/${userId}`);
  }

  /**
   * 创建用户
   */
  async createUser(userData: AdminUserCreateRequest): Promise<ApiResponse<UserDetailResponse>> {
    return apiService.post<UserDetailResponse>('/users/create', userData);
  }

  /**
   * 更新用户信息
   */
  async updateUser(userId: number, userData: AdminUserUpdateRequest): Promise<ApiResponse<UserDetailResponse>> {
    return apiService.put<UserDetailResponse>(`/users/${userId}`, userData);
  }

  /**
   * 更新用户状态
   */
  async updateUserStatus(userId: number, statusData: UserStatusUpdateRequest): Promise<ApiResponse<UserDetailResponse>> {
    return apiService.put<UserDetailResponse>(`/users/${userId}/status`, statusData);
  }

  /**
   * 删除用户
   */
  async deleteUser(userId: number): Promise<ApiResponse<{ message: string }>> {
    return apiService.delete<{ message: string }>(`/users/${userId}`);
  }

  /**
   * 启用用户
   */
  async enableUser(userId: number, reason?: string): Promise<ApiResponse<UserDetailResponse>> {
    return this.updateUserStatus(userId, { is_active: true, reason });
  }

  /**
   * 禁用用户
   */
  async disableUser(userId: number, reason?: string): Promise<ApiResponse<UserDetailResponse>> {
    return this.updateUserStatus(userId, { is_active: false, reason });
  }
}

export const userManagementService = new UserManagementService();
export default userManagementService;
