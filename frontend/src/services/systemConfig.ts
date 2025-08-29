import { apiService, ApiResponse } from './api';

// 系统配置类型定义
export interface SystemConfig {
  id: number;
  key: string;
  value: string;
  description?: string;
  category: string;
  is_public: boolean;
  is_encrypted: boolean;
  is_active: boolean;
  data_type: string;
  validation_rule?: string;
  default_value?: string;
  created_at: string;
  updated_at: string;
}

// 公开配置类型（不包含敏感信息）
export interface PublicSystemConfig {
  id: number;
  key: string;
  value: string;
  description?: string;
  category: string;
  data_type: string;
  created_at: string;
  updated_at: string;
}

// 配置分类类型
export interface ConfigCategory {
  category: string;
  count: number;
  description?: string;
}

// 创建配置请求类型
export interface CreateConfigRequest {
  key: string;
  value: string;
  description?: string;
  category: string;
  is_public?: boolean;
  is_encrypted?: boolean;
  is_active?: boolean;
  data_type?: string;
  validation_rule?: string;
  default_value?: string;
}

// 更新配置请求类型
export interface UpdateConfigRequest {
  value?: string;
  description?: string;
  category?: string;
  is_public?: boolean;
  is_active?: boolean;
  data_type?: string;
  validation_rule?: string;
  default_value?: string;
  is_encrypted?: boolean;
}

// 批量更新请求类型
export interface BatchUpdateRequest {
  configs: Record<string, string>;
  category?: string;
}

// 导出请求类型
export interface ExportRequest {
  categories?: string[];
  include_encrypted?: boolean;
  format?: 'json' | 'yaml' | 'env';
}

// 导入请求类型
export interface ImportRequest {
  data: string;
  format?: 'json' | 'yaml' | 'env';
  overwrite?: boolean;
  category?: string;
}

class SystemConfigService {
  // 获取系统配置列表（需要管理员权限）
  async getConfigs(
    category?: string,
    isPublic?: boolean,
    includeInactive?: boolean
  ): Promise<ApiResponse<SystemConfig[]>> {
    const params: any = {};
    if (category) params.category = category;
    if (isPublic !== undefined) params.is_public = isPublic;
    if (includeInactive) params.include_inactive = includeInactive;

    return apiService.get('/system/config', params);
  }

  // 获取公开配置（不需要认证）
  async getPublicConfigs(
    category?: string
  ): Promise<ApiResponse<PublicSystemConfig[]>> {
    const params: any = {};
    if (category) params.category = category;

    return apiService.get('/system/config/public', params);
  }

  // 获取配置分类列表
  async getCategories(): Promise<ApiResponse<ConfigCategory[]>> {
    return apiService.get('/system/config/categories');
  }

  // 获取单个配置
  async getConfig(key: string): Promise<ApiResponse<SystemConfig>> {
    return apiService.get(`/system/config/${key}`);
  }

  // 创建配置
  async createConfig(data: CreateConfigRequest): Promise<ApiResponse<SystemConfig>> {
    return apiService.post('/system/config', data);
  }

  // 更新配置
  async updateConfig(
    key: string,
    data: UpdateConfigRequest
  ): Promise<ApiResponse<SystemConfig>> {
    return apiService.put(`/system/config/${key}`, data);
  }

  // 删除配置
  async deleteConfig(key: string): Promise<ApiResponse<any>> {
    return apiService.delete(`/system/config/${key}`);
  }

  // 批量更新配置
  async batchUpdateConfigs(
    data: BatchUpdateRequest
  ): Promise<ApiResponse<{ updated: string[]; errors: string[] }>> {
    return apiService.post('/system/config/batch-update', data);
  }

  // 导出配置
  async exportConfigs(
    data: ExportRequest
  ): Promise<ApiResponse<{ format: string; count: number; data: string }>> {
    return apiService.post('/system/config/export', data);
  }

  // 导入配置
  async importConfigs(
    data: ImportRequest
  ): Promise<ApiResponse<{ imported: string[]; errors: string[] }>> {
    return apiService.post('/system/config/import', data);
  }

  // 获取特定分类的配置（辅助方法）
  async getConfigsByCategory(category: string): Promise<SystemConfig[]> {
    try {
      const response = await this.getConfigs(category);
      return response.code === 200 ? response.data : [];
    } catch (error) {
      console.error(`Error fetching configs for category ${category}:`, error);
      return [];
    }
  }

  // 获取配置值（辅助方法）
  async getConfigValue(key: string, defaultValue?: string): Promise<string | undefined> {
    try {
      const response = await this.getConfig(key);
      if (response.code === 200) {
        return response.data.value;
      }
      return defaultValue;
    } catch (error) {
      console.error(`Error fetching config value for key ${key}:`, error);
      return defaultValue;
    }
  }

  // 设置配置值（辅助方法）
  async setConfigValue(
    key: string,
    value: string,
    description?: string
  ): Promise<boolean> {
    try {
      // 先尝试获取现有配置
      const existing = await this.getConfig(key);
      
      if (existing.code === 200) {
        // 更新现有配置
        const response = await this.updateConfig(key, { value, description });
        return response.code === 200;
      } else {
        // 创建新配置
        const response = await this.createConfig({
          key,
          value,
          description,
          category: 'general'
        });
        return response.code === 200;
      }
    } catch (error) {
      console.error(`Error setting config value for key ${key}:`, error);
      return false;
    }
  }

  // 获取AI配置（特定分类的辅助方法）
  async getAIConfigs(): Promise<SystemConfig[]> {
    return this.getConfigsByCategory('ai');
  }

  // 获取下载配置
  async getDownloadConfigs(): Promise<SystemConfig[]> {
    return this.getConfigsByCategory('download');
  }

  // 获取上传配置
  async getUploadConfigs(): Promise<SystemConfig[]> {
    return this.getConfigsByCategory('upload');
  }

  // 获取系统配置
  async getSystemConfigs(): Promise<SystemConfig[]> {
    return this.getConfigsByCategory('system');
  }

  // 获取用户界面配置
  async getUIConfigs(): Promise<SystemConfig[]> {
    return this.getConfigsByCategory('ui');
  }

  // 验证配置值格式（客户端验证）
  validateConfigValue(value: string, dataType: string, validationRule?: string): boolean {
    try {
      switch (dataType) {
        case 'integer':
          return !isNaN(parseInt(value)) && isFinite(parseInt(value));
        case 'float':
          return !isNaN(parseFloat(value)) && isFinite(parseFloat(value));
        case 'boolean':
          return ['true', 'false', '1', '0'].includes(value.toLowerCase());
        case 'json':
          JSON.parse(value);
          return true;
        case 'string':
        case 'text':
        default:
          // 如果有验证规则，使用正则表达式验证
          if (validationRule) {
            const regex = new RegExp(validationRule);
            return regex.test(value);
          }
          return true;
      }
    } catch (error) {
      return false;
    }
  }

  // 格式化配置值显示
  formatConfigValue(value: string, dataType: string): string {
    switch (dataType) {
      case 'boolean':
        return ['true', '1'].includes(value.toLowerCase()) ? '是' : '否';
      case 'json':
        try {
          return JSON.stringify(JSON.parse(value), null, 2);
        } catch {
          return value;
        }
      default:
        return value;
    }
  }
}

// 创建系统配置服务实例
export const systemConfigService = new SystemConfigService();
export default systemConfigService;