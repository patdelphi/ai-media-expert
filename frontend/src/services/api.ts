import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import { API_BASE_URL } from '../config';

// API响应类型
export interface ApiResponse<T = unknown> {
  code: number;
  message: string;
  data: T;
  timestamp?: string;
  request_id?: string;
}

// 错误响应类型
export interface ApiError {
  code: number;
  message: string;
  error?: {
    type: string;
    details: Array<{
      field: string;
      message: string;
    }>;
  };
  timestamp?: string;
  request_id?: string;
}

export interface TokenPayload {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user?: unknown;
}

interface RetryableAxiosRequestConfig extends AxiosRequestConfig {
  _retry?: boolean;
}

export class ApiService {
  private api: AxiosInstance;
  private refreshClient: AxiosInstance;
  private refreshPromise: Promise<TokenPayload> | null = null;
  readonly baseUrl: string;

  constructor() {
    this.baseUrl = API_BASE_URL;
    const defaultTimeoutMs = 120_000;
    this.api = axios.create({
      baseURL: this.baseUrl,
      timeout: defaultTimeoutMs,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.refreshClient = axios.create({
      baseURL: this.baseUrl,
      timeout: defaultTimeoutMs,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // 请求拦截器
    this.api.interceptors.request.use(
      (config) => {
        // 添加认证token
        const token = localStorage.getItem('access_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // 响应拦截器
    this.api.interceptors.response.use(
      (response: AxiosResponse<ApiResponse>) => {
        return response;
      },
      async (error) => {
        const originalRequest = error.config as RetryableAxiosRequestConfig | undefined;

        // 如果是 401，则尝试通过独立 refresh client 刷新 token，避免递归进入同一拦截器。
        if (error.response?.status === 401 && originalRequest && !originalRequest._retry) {
          originalRequest._retry = true;

          try {
            const refreshToken = localStorage.getItem('refresh_token');
            if (refreshToken) {
              const tokenPayload = await this.refreshAuthToken(refreshToken);
              const { access_token, refresh_token } = tokenPayload;
              
              localStorage.setItem('access_token', access_token);
              localStorage.setItem('refresh_token', refresh_token);
              if (tokenPayload.user) {
                localStorage.setItem('user', JSON.stringify(tokenPayload.user));
              }
              
              originalRequest.headers = {
                ...(originalRequest.headers || {}),
                Authorization: `Bearer ${access_token}`,
              };
              return this.api(originalRequest);
            }
          } catch (refreshError) {
            this.clearTokens();
            window.location.assign('/login');
            return Promise.reject(refreshError);
          }
        }

        return Promise.reject(error);
      }
    );
  }

  // 清除tokens
  private clearTokens() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
  }

  getBaseUrl(): string {
    return this.baseUrl;
  }

  async refreshAuthToken(refreshToken: string): Promise<TokenPayload> {
    if (!this.refreshPromise) {
      this.refreshPromise = this.refreshClient
        .post<ApiResponse<TokenPayload>>('/auth/refresh', {
          refresh_token: refreshToken,
        })
        .then((response) => response.data.data)
        .finally(() => {
          this.refreshPromise = null;
        });
    }

    return this.refreshPromise;
  }

  // GET请求
  async get<T = unknown>(url: string, params?: unknown): Promise<ApiResponse<T>> {
    const response = await this.api.get(url, { params });
    return response.data;
  }

  // POST请求
  async post<T = unknown>(url: string, data?: unknown): Promise<ApiResponse<T>> {
    const response = await this.api.post(url, data);
    return response.data;
  }

  // POST表单请求（multipart/form-data）
  async postForm<T = unknown>(url: string, formData: FormData): Promise<ApiResponse<T>> {
    const response = await this.api.post(url, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  // PUT请求
  async put<T = unknown>(url: string, data?: unknown): Promise<ApiResponse<T>> {
    const response = await this.api.put(url, data);
    return response.data;
  }

  // DELETE请求
  async delete<T = any>(url: string): Promise<ApiResponse<T>> {
    const response = await this.api.delete(url);
    return response.data;
  }

  // PATCH请求
  async patch<T = unknown>(url: string, data?: unknown): Promise<ApiResponse<T>> {
    const response = await this.api.patch(url, data);
    return response.data;
  }

  // 上传文件
  async upload<T = unknown>(
    url: string,
    file: File,
    onProgress?: (progress: number) => void
  ): Promise<ApiResponse<T>> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await this.api.post(url, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          onProgress(progress);
        }
      },
    });

    return response.data;
  }
}

// 创建API服务实例
export const apiService = new ApiService();
export default apiService;
