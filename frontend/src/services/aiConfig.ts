import { apiService, ApiResponse } from './api';

// AI配置类型定义
export interface AIConfig {
  id: number;
  name: string;
  provider: string;
  api_key: string;
  api_base?: string;
  model: string;
  max_tokens?: number;
  temperature?: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// 公开AI配置类型（不包含敏感信息）
export interface PublicAIConfig {
  id: number;
  name: string;
  provider: string;
  model: string;
  is_active: boolean;
  created_at: string;
}

// 创建AI配置请求类型
export interface CreateAIConfigRequest {
  name: string;
  provider: string;
  api_key: string;
  api_base?: string;
  model: string;
  max_tokens?: number;
  temperature?: number;
  is_active?: boolean;
}

// 更新AI配置请求类型
export interface UpdateAIConfigRequest {
  name?: string;
  provider?: string;
  api_key?: string;
  api_base?: string;
  model?: string;
  max_tokens?: number;
  temperature?: number;
  is_active?: boolean;
}

// AI配置测试结果类型
export interface AIConfigTestResult {
  success: boolean;
  message: string;
  response_time?: string;
  model_info?: {
    provider: string;
    model: string;
    max_tokens: number;
  };
}

class AIConfigService {
  // 获取AI配置列表（公开信息，不包含API密钥）
  async getPublicConfigs(includeInactive?: boolean): Promise<ApiResponse<PublicAIConfig[]>> {
    const params: any = {};
    if (includeInactive) params.include_inactive = includeInactive;
    
    return apiService.get('/api/v1/ai-config', params);
  }

  // 获取AI配置完整信息（包含API密钥，仅管理员使用）
  async getFullConfigs(includeInactive?: boolean): Promise<ApiResponse<AIConfig[]>> {
    const params: any = {};
    if (includeInactive) params.include_inactive = includeInactive;
    
    return apiService.get('/api/v1/ai-config/full', params);
  }

  // 获取单个AI配置详情
  async getConfig(configId: number): Promise<ApiResponse<AIConfig>> {
    return apiService.get(`/api/v1/ai-config/${configId}`);
  }

  // 创建AI配置
  async createConfig(data: CreateAIConfigRequest): Promise<ApiResponse<AIConfig>> {
    return apiService.post('/api/v1/ai-config', data);
  }

  // 更新AI配置
  async updateConfig(
    configId: number,
    data: UpdateAIConfigRequest
  ): Promise<ApiResponse<AIConfig>> {
    return apiService.put(`/api/v1/ai-config/${configId}`, data);
  }

  // 删除AI配置
  async deleteConfig(configId: number): Promise<ApiResponse<any>> {
    return apiService.delete(`/api/v1/ai-config/${configId}`);
  }

  // 测试AI配置连接
  async testConfig(configId: number): Promise<ApiResponse<AIConfigTestResult>> {
    return apiService.post(`/api/v1/ai-config/${configId}/test`);
  }

  // 激活AI配置
  async activateConfig(configId: number): Promise<ApiResponse<any>> {
    return apiService.post(`/api/v1/ai-config/${configId}/activate`);
  }

  // 停用AI配置
  async deactivateConfig(configId: number): Promise<ApiResponse<any>> {
    return apiService.post(`/api/v1/ai-config/${configId}/deactivate`);
  }

  // 获取支持的AI提供商列表
  getSupportedProviders(): Array<{ value: string; label: string; models: string[] }> {
    return [
      {
        value: 'openai',
        label: 'OpenAI',
        models: ['gpt-4', 'gpt-4-turbo', 'gpt-3.5-turbo', 'gpt-3.5-turbo-16k']
      },
      {
        value: 'anthropic',
        label: 'Anthropic',
        models: ['claude-3-opus', 'claude-3-sonnet', 'claude-3-haiku', 'claude-2.1']
      },
      {
        value: 'google',
        label: 'Google',
        models: ['gemini-pro', 'gemini-pro-vision', 'gemini-1.5-pro']
      },
      {
        value: 'zhipu',
        label: '智谱AI',
        models: ['glm-4', 'glm-4v', 'glm-3-turbo']
      },
      {
        value: 'ollama',
        label: 'Ollama',
        models: ['llama2', 'codellama', 'mistral', 'qwen']
      },
      {
        value: 'custom',
        label: '自定义',
        models: []
      }
    ];
  }

  // 根据提供商获取默认API基础URL
  getDefaultApiBase(provider: string): string {
    const defaults: Record<string, string> = {
      openai: 'https://api.openai.com/v1',
      anthropic: 'https://api.anthropic.com',
      google: 'https://generativelanguage.googleapis.com/v1',
      zhipu: 'https://open.bigmodel.cn/api/paas/v4',
      ollama: 'http://localhost:11434/v1',
      custom: ''
    };
    
    return defaults[provider] || '';
  }

  // 验证AI配置数据
  validateConfig(data: CreateAIConfigRequest | UpdateAIConfigRequest): string[] {
    const errors: string[] = [];
    
    if ('name' in data && data.name && data.name.trim().length < 2) {
      errors.push('配置名称至少需要2个字符');
    }
    
    if ('api_key' in data && data.api_key && data.api_key.trim().length < 10) {
      errors.push('API密钥格式不正确');
    }
    
    if ('api_base' in data && data.api_base && !this.isValidUrl(data.api_base)) {
      errors.push('API基础URL格式不正确');
    }
    
    if ('max_tokens' in data && data.max_tokens && (data.max_tokens < 1 || data.max_tokens > 32000)) {
      errors.push('最大token数应在1-32000之间');
    }
    
    if ('temperature' in data && data.temperature && (data.temperature < 0 || data.temperature > 2)) {
      errors.push('温度参数应在0-2之间');
    }
    
    return errors;
  }

  // 验证URL格式
  private isValidUrl(url: string): boolean {
    try {
      new URL(url);
      return true;
    } catch {
      return false;
    }
  }

  // 格式化配置显示名称
  formatConfigName(config: AIConfig | PublicAIConfig): string {
    return `${config.name} (${config.provider}/${config.model})`;
  }

  // 获取提供商显示名称
  getProviderDisplayName(provider: string): string {
    const providers = this.getSupportedProviders();
    const found = providers.find(p => p.value === provider);
    return found ? found.label : provider;
  }

  // 检查配置是否可用
  isConfigAvailable(config: AIConfig | PublicAIConfig): boolean {
    return config.is_active;
  }

  // 获取配置状态文本
  getConfigStatusText(config: AIConfig | PublicAIConfig): string {
    return config.is_active ? '启用' : '禁用';
  }

  // 获取配置状态样式类
  getConfigStatusClass(config: AIConfig | PublicAIConfig): string {
    return config.is_active 
      ? 'bg-green-100 text-green-800' 
      : 'bg-gray-100 text-gray-800';
  }
}

// 创建AI配置服务实例
export const aiConfigService = new AIConfigService();
export default aiConfigService;