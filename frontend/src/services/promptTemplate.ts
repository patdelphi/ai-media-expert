import { apiService, ApiResponse } from './api';

export interface PromptTemplate {
  id: number;
  title: string;
  content: string;
  is_active: boolean;
  usage_count: number;
  created_at: string;
  updated_at: string;
}

export interface CreatePromptTemplateRequest {
  title: string;
  content: string;
  is_active?: boolean;
}

export interface UpdatePromptTemplateRequest {
  title?: string;
  content?: string;
  is_active?: boolean;
}

class PromptTemplateService {
  // 获取提示词模板列表
  async getTemplates(includeInactive?: boolean): Promise<ApiResponse<PromptTemplate[]>> {
    const params = includeInactive ? { include_inactive: includeInactive } : {};
    return apiService.get('/prompt-templates', params);
  }

  // 获取单个提示词模板详情
  async getTemplate(templateId: number): Promise<ApiResponse<PromptTemplate>> {
    return apiService.get(`/prompt-templates/${templateId}`);
  }

  // 创建提示词模板
  async createTemplate(data: CreatePromptTemplateRequest): Promise<ApiResponse<PromptTemplate>> {
    return apiService.post('/prompt-templates', data);
  }

  // 更新提示词模板
  async updateTemplate(
    templateId: number,
    data: UpdatePromptTemplateRequest
  ): Promise<ApiResponse<PromptTemplate>> {
    return apiService.put(`/prompt-templates/${templateId}`, data);
  }

  // 删除提示词模板
  async deleteTemplate(templateId: number): Promise<ApiResponse<any>> {
    return apiService.delete(`/prompt-templates/${templateId}`);
  }

  // 使用提示词模板（增加使用次数）
  async useTemplate(templateId: number): Promise<ApiResponse<any>> {
    return apiService.post(`/prompt-templates/${templateId}/use`);
  }
}

export const promptTemplateService = new PromptTemplateService();
export default promptTemplateService;