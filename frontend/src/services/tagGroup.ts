import { apiService, ApiResponse } from './api';

// 标签类型
export interface Tag {
  id: number;
  name: string;
  color?: string;
  tag_group_id: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// 标签组类型
export interface TagGroup {
  id: number;
  name: string;
  description?: string;
  is_active: boolean;
  tags: Tag[];
  created_at: string;
  updated_at: string;
}

// 标签组列表项类型
export interface TagGroupListItem {
  id: number;
  name: string;
  description?: string;
  is_active: boolean;
  tag_count: number;
  created_at: string;
  updated_at: string;
}

// 创建标签组请求类型
export interface CreateTagGroupRequest {
  name: string;
  description?: string;
  is_active?: boolean;
  tags?: CreateTagRequest[];
}

// 更新标签组请求类型
export interface UpdateTagGroupRequest {
  name?: string;
  description?: string;
  is_active?: boolean;
}

// 创建标签请求类型
export interface CreateTagRequest {
  name: string;
  color?: string;
  is_active?: boolean;
}

// 更新标签请求类型
export interface UpdateTagRequest {
  name?: string;
  color?: string;
  is_active?: boolean;
}

// 批量标签操作请求类型
export interface BatchTagOperationRequest {
  tag_group_id: number;
  tags: string[];
}

// 搜索参数类型
export interface TagGroupSearchParams {
  search?: string;
  is_active?: boolean;
  include_tags?: boolean;
}

class TagGroupService {
  /**
   * 获取标签组列表
   */
  async getTagGroups(params: TagGroupSearchParams = {}): Promise<ApiResponse<TagGroup[]>> {
    const queryParams = new URLSearchParams();
    
    if (params.search) queryParams.append('search', params.search);
    if (params.is_active !== undefined) queryParams.append('is_active', params.is_active.toString());
    if (params.include_tags !== undefined) queryParams.append('include_tags', params.include_tags.toString());
    
    const url = `/tag-groups${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
    return apiService.get<TagGroup[]>(url);
  }

  /**
   * 获取标签组详情
   */
  async getTagGroup(groupId: number): Promise<ApiResponse<TagGroup>> {
    return apiService.get<TagGroup>(`/tag-groups/${groupId}`);
  }

  /**
   * 创建标签组
   */
  async createTagGroup(data: CreateTagGroupRequest): Promise<ApiResponse<TagGroup>> {
    return apiService.post<TagGroup>('/tag-groups', data);
  }

  /**
   * 更新标签组
   */
  async updateTagGroup(groupId: number, data: UpdateTagGroupRequest): Promise<ApiResponse<TagGroup>> {
    return apiService.put<TagGroup>(`/tag-groups/${groupId}`, data);
  }

  /**
   * 删除标签组
   */
  async deleteTagGroup(groupId: number): Promise<ApiResponse<{ message: string }>> {
    return apiService.delete<{ message: string }>(`/tag-groups/${groupId}`);
  }

  /**
   * 在标签组中创建标签
   */
  async createTag(groupId: number, data: CreateTagRequest): Promise<ApiResponse<Tag>> {
    return apiService.post<Tag>(`/tag-groups/${groupId}/tags`, data);
  }

  /**
   * 更新标签
   */
  async updateTag(tagId: number, data: UpdateTagRequest): Promise<ApiResponse<Tag>> {
    return apiService.put<Tag>(`/tag-groups/tags/${tagId}`, data);
  }

  /**
   * 删除标签
   */
  async deleteTag(tagId: number): Promise<ApiResponse<{ message: string }>> {
    return apiService.delete<{ message: string }>(`/tag-groups/tags/${tagId}`);
  }

  /**
   * 批量创建标签
   */
  async batchCreateTags(groupId: number, tags: string[]): Promise<ApiResponse<Tag[]>> {
    return apiService.post<Tag[]>(`/tag-groups/${groupId}/tags/batch`, {
      tag_group_id: groupId,
      tags
    });
  }

  /**
   * 启用标签组
   */
  async enableTagGroup(groupId: number): Promise<ApiResponse<TagGroup>> {
    return this.updateTagGroup(groupId, { is_active: true });
  }

  /**
   * 禁用标签组
   */
  async disableTagGroup(groupId: number): Promise<ApiResponse<TagGroup>> {
    return this.updateTagGroup(groupId, { is_active: false });
  }

  /**
   * 启用标签
   */
  async enableTag(tagId: number): Promise<ApiResponse<Tag>> {
    return this.updateTag(tagId, { is_active: true });
  }

  /**
   * 禁用标签
   */
  async disableTag(tagId: number): Promise<ApiResponse<Tag>> {
    return this.updateTag(tagId, { is_active: false });
  }
}

export const tagGroupService = new TagGroupService();
export default tagGroupService;