import React, { useState, useEffect, useMemo } from 'react';
import { toast } from 'react-hot-toast';
import { useAuth } from '../contexts/AuthContext';
import { systemConfigService, SystemConfig, ConfigCategory } from '../services/systemConfig';
import { aiConfigService, AIConfig, CreateAIConfigRequest } from '../services/aiConfig';
import { promptTemplateService, PromptTemplate, CreatePromptTemplateRequest } from '../services/promptTemplate';
import userManagementService, {
  UserListItem,
  UserSearchParams,
  AdminUserCreateRequest,
  AdminUserUpdateRequest
} from '../services/userManagement';
import tagGroupService, {
  TagGroup,
  Tag,
  CreateTagGroupRequest,
  UpdateTagGroupRequest,
  CreateTagRequest
} from '../services/tagGroup';
import { SystemConfig as SystemConfigType } from '../types';
import { marked } from 'marked';

// 预设标签颜色
const PRESET_TAG_COLORS = [
  { name: '蓝色', value: '#3B82F6' },
  { name: '绿色', value: '#10B981' },
  { name: '红色', value: '#EF4444' },
  { name: '黄色', value: '#F59E0B' },
  { name: '紫色', value: '#8B5CF6' },
  { name: '粉色', value: '#EC4899' },
  { name: '青色', value: '#06B6D4' },
  { name: '橙色', value: '#F97316' },
  { name: '灰色', value: '#6B7280' },
  { name: '深蓝', value: '#1E40AF' }
];

const SystemConfigPage: React.FC = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('basic');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // 系统配置数据
  const [configs, setConfigs] = useState<SystemConfig[]>([]);
  const [categories, setCategories] = useState<ConfigCategory[]>([]);
  const [filteredConfigs, setFilteredConfigs] = useState<SystemConfig[]>([]);
  
  // 表单状态
  const [editingConfig, setEditingConfig] = useState<SystemConfig | null>(null);
  const [newConfigForm, setNewConfigForm] = useState({
    key: '',
    value: '',
    description: '',
    category: 'general',
    data_type: 'string',
    is_public: false,
    is_encrypted: false
  });
  
  // 基础设置
  const [basicSettings, setBasicSettings] = useState({
    systemName: 'AI媒体专家',
    systemDescription: '智能视频处理平台',
    maxFileSize: 500, // MB
    allowedFormats: ['MP4', 'AVI', 'MOV', 'WMV', 'FLV', 'WebM', 'MKV'],
    autoBackup: true,
    backupInterval: 24, // hours
    logLevel: 'info'
  });

  // AI配置数据
  const [aiConfigs, setAiConfigs] = useState<AIConfig[]>([]);
  const [loadingAiConfigs, setLoadingAiConfigs] = useState(false);

  // 提示词模板
  const [templates, setTemplates] = useState<PromptTemplate[]>([]);
  const [loadingTemplates, setLoadingTemplates] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState<PromptTemplate | null>(null);

  // 标签组
  const [tagGroups, setTagGroups] = useState<TagGroup[]>([]);
  const [loadingTagGroups, setLoadingTagGroups] = useState(false);
  const [showTagGroupCreateForm, setShowTagGroupCreateForm] = useState(false);
  const [showTagGroupEditForm, setShowTagGroupEditForm] = useState(false);
  const [editingTagGroup, setEditingTagGroup] = useState<TagGroup | null>(null);
  const [tagGroupFormData, setTagGroupFormData] = useState({
    name: '',
    description: '',
    is_active: true
  });
  const [showTagCreateForm, setShowTagCreateForm] = useState<{ groupId: number | null }>({ groupId: null });
  const [tagFormData, setTagFormData] = useState({
    name: '',
    color: PRESET_TAG_COLORS[0].value,
    is_active: true
  });
  const [batchTagInput, setBatchTagInput] = useState('');
  const [showBatchTagForm, setShowBatchTagForm] = useState<{ groupId: number | null }>({ groupId: null });

  // 用户管理
  const [users, setUsers] = useState<UserListItem[]>([]);
  const [loadingUsers, setLoadingUsers] = useState(false);
  const [userTotal, setUserTotal] = useState(0);
  const [userCurrentPage, setUserCurrentPage] = useState(1);
  const [userPageSize] = useState(10);
  const [userSearchParams, setUserSearchParams] = useState<UserSearchParams>({});
  const [showUserCreateForm, setShowUserCreateForm] = useState(false);
  const [showUserEditForm, setShowUserEditForm] = useState(false);
  const [editingUser, setEditingUser] = useState<UserListItem | null>(null);
  const [userFormData, setUserFormData] = useState({
    email: '',
    username: '',
    full_name: '',
    password: '',
    role: 'user',
    is_active: true,
    is_verified: false
  });
  const [userSearchForm, setUserSearchForm] = useState({
    search: '',
    role: '',
    is_active: '',
    is_verified: ''
  });

  // 表单状态
  const [newApi, setNewApi] = useState({
    provider: 'custom',
    name: '',
    apiKey: '',
    baseUrl: '',
    model: '',
    maxTokens: 4000,
    temperature: 0.7
  });
  
  const [editingApi, setEditingApi] = useState<AIConfig | null>(null);
  const [validationErrors, setValidationErrors] = useState<{[key: string]: string}>({});
  const [newTemplate, setNewTemplate] = useState({ title: '', content: '' });
  const [templateValidationErrors, setTemplateValidationErrors] = useState<{[key: string]: string}>({});

  // 加载系统配置数据
  useEffect(() => {
    loadConfigs();
    loadCategories();
    loadAiConfigs();
    loadTemplates();
    loadUsers();
    loadTagGroups();
  }, []);

  // 当标签组标签页激活时重新加载数据
  useEffect(() => {
    if (activeTab === 'tags') {
      loadTagGroups();
    }
  }, [activeTab]);

  // 当用户搜索参数或分页改变时重新加载用户
  useEffect(() => {
    if (activeTab === 'users') {
      loadUsers();
    }
  }, [userCurrentPage, userSearchParams, activeTab]);

  // 根据当前标签页筛选配置
  useEffect(() => {
    filterConfigsByTab();
  }, [configs, activeTab]);

  const loadConfigs = async () => {
    if (user?.role !== 'admin') return;
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await systemConfigService.getConfigs();
      if (response.code === 200) {
        setConfigs(response.data);
      } else {
        setError(response.message || '加载配置失败');
      }
    } catch (err: any) {
      setError(err.message || '加载配置失败');
    } finally {
      setLoading(false);
    }
  };

  const loadCategories = async () => {
    if (user?.role !== 'admin') return;
    
    try {
      const response = await systemConfigService.getCategories();
      if (response.code === 200) {
        setCategories(response.data);
      }
    } catch (err) {
      console.error('Failed to load categories:', err);
    }
  };

  const filterConfigsByTab = () => {
    let categoryFilter = '';
    switch (activeTab) {
      case 'basic':
        categoryFilter = 'system';
        break;
      case 'ai':
        categoryFilter = 'ai';
        break;
      case 'template':
        categoryFilter = 'template';
        break;
      case 'tags':
        categoryFilter = 'tag';
        break;
      case 'users':
        categoryFilter = 'user';
        break;
      default:
        setFilteredConfigs(configs);
        return;
    }
    
    const filtered = configs.filter(config => config.category === categoryFilter);
    setFilteredConfigs(filtered);
  };

  const handleCreateConfig = async () => {
    if (!newConfigForm.key || !newConfigForm.value) {
      setError('配置键和值不能为空');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await systemConfigService.createConfig(newConfigForm);
      if (response.code === 200) {
        setConfigs([...configs, response.data]);
        setNewConfigForm({
          key: '',
          value: '',
          description: '',
          category: 'general',
          data_type: 'string',
          is_public: false,
          is_encrypted: false
        });
      } else {
        setError(response.message || '创建配置失败');
      }
    } catch (err: any) {
      setError(err.message || '创建配置失败');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateConfig = async (config: SystemConfig) => {
    if (!editingConfig) return;

    setLoading(true);
    setError(null);

    try {
      const response = await systemConfigService.updateConfig(config.key, {
        value: editingConfig.value,
        description: editingConfig.description,
        is_public: editingConfig.is_public,
        is_active: editingConfig.is_active
      });
      
      if (response.code === 200) {
        setConfigs(configs.map(c => c.id === config.id ? response.data : c));
        setEditingConfig(null);
      } else {
        setError(response.message || '更新配置失败');
      }
    } catch (err: any) {
      setError(err.message || '更新配置失败');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteConfig = async (key: string) => {
    if (!confirm('确定要删除这个配置吗？')) return;

    setLoading(true);
    setError(null);

    try {
      const response = await systemConfigService.deleteConfig(key);
      if (response.code === 200) {
        setConfigs(configs.filter(c => c.key !== key));
      } else {
        setError(response.message || '删除配置失败');
      }
    } catch (err: any) {
      setError(err.message || '删除配置失败');
    } finally {
      setLoading(false);
    }
  };

  const handleExportConfigs = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await systemConfigService.exportConfigs({
        format: 'json',
        include_encrypted: false
      });
      
      if (response.code === 200) {
        // 创建下载链接
        const blob = new Blob([response.data.data], { type: 'application/json' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `system-config-${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
      } else {
        setError(response.message || '导出配置失败');
      }
    } catch (err: any) {
      setError(err.message || '导出配置失败');
    } finally {
      setLoading(false);
    }
  };

  // 处理函数
  const loadAiConfigs = async () => {
    if (user?.role !== 'admin') return;
    
    setLoadingAiConfigs(true);
    try {
      const response = await aiConfigService.getFullConfigs(true); // 包含非活跃配置
      if (response.code === 200) {
        setAiConfigs(response.data);
      } else {
        setError(response.message || '加载AI配置失败');
      }
    } catch (err: any) {
      setError(err.message || '加载AI配置失败');
    } finally {
      setLoadingAiConfigs(false);
    }
  };

  // 加载提示词模板
  const loadTemplates = async () => {
    if (user?.role !== 'admin') return;
    
    setLoadingTemplates(true);
    try {
      const response = await promptTemplateService.getTemplates();
      if (response.code === 200) {
        setTemplates(response.data);
      } else {
        setError(response.message || '加载提示词模板失败');
      }
    } catch (err: any) {
      setError(err.message || '加载提示词模板失败');
    } finally {
      setLoadingTemplates(false);
    }
  };

  // 验证模板表单
  const validateTemplateForm = (data: any) => {
    const errors: {[key: string]: string} = {};
    
    if (!data.title?.trim()) {
      errors.title = '模板标题是必填项';
    }
    
    if (!data.content?.trim()) {
      errors.content = '模板内容是必填项';
    }
    
    return errors;
  };

  // 添加提示词模板
  const handleAddTemplate = async () => {
    const errors = validateTemplateForm(newTemplate);
    setTemplateValidationErrors(errors);
    
    if (Object.keys(errors).length > 0) {
      setError('请修正表单中的错误');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const templateData: CreatePromptTemplateRequest = {
        title: newTemplate.title,
        content: newTemplate.content,
        is_active: true
      };

      const response = await promptTemplateService.createTemplate(templateData);
      if (response.code === 200) {
        setTemplates([response.data, ...templates]);
        setNewTemplate({ title: '', content: '' });
        setTemplateValidationErrors({});
        setError(null);
      } else {
        setError(response.message || '添加提示词模板失败');
      }
    } catch (err: any) {
      if (err.response?.status === 400 && err.response?.data?.detail) {
        setError(err.response.data.detail);
      } else if (err.response?.data?.message) {
        setError(err.response.data.message);
      } else {
        setError(err.message || '添加提示词模板失败');
      }
    } finally {
      setLoading(false);
    }
  };

  // 编辑提示词模板
  const handleEditTemplate = (template: PromptTemplate) => {
    setEditingTemplate(template);
  };

  // 更新提示词模板
  const handleUpdateTemplate = async () => {
    if (!editingTemplate) return;

    const errors = validateTemplateForm(editingTemplate);
    setTemplateValidationErrors(errors);
    
    if (Object.keys(errors).length > 0) {
      setError('请修正表单中的错误');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await promptTemplateService.updateTemplate(editingTemplate.id, {
        title: editingTemplate.title,
        content: editingTemplate.content,
        is_active: editingTemplate.is_active
      });
      
      if (response.code === 200) {
        setTemplates(templates.map(t => t.id === editingTemplate.id ? response.data : t));
        setEditingTemplate(null);
        setTemplateValidationErrors({});
        setError(null);
      } else {
        setError(response.message || '更新提示词模板失败');
      }
    } catch (err: any) {
      if (err.response?.status === 400 && err.response?.data?.detail) {
        setError(err.response.data.detail);
      } else if (err.response?.data?.message) {
        setError(err.response.data.message);
      } else {
        setError(err.message || '更新提示词模板失败');
      }
    } finally {
      setLoading(false);
    }
  };

  // 取消编辑
  const handleCancelEditTemplate = () => {
    setEditingTemplate(null);
    setTemplateValidationErrors({});
  };

  // 删除提示词模板
  const handleDeleteTemplate = async (templateId: number) => {
    if (!confirm('确定要删除这个提示词模板吗？')) return;

    setLoading(true);
    setError(null);

    try {
      const response = await promptTemplateService.deleteTemplate(templateId);
      if (response.code === 200) {
        setTemplates(templates.filter(t => t.id !== templateId));
      } else {
        setError(response.message || '删除提示词模板失败');
      }
    } catch (err: any) {
      setError(err.message || '删除提示词模板失败');
    } finally {
      setLoading(false);
    }
  };

  // 使用提示词模板
  const handleUseTemplate = async (templateId: number) => {
    try {
      await promptTemplateService.useTemplate(templateId);
      // 重新加载模板列表以更新使用次数
      loadTemplates();
    } catch (err: any) {
      console.error('更新模板使用次数失败:', err);
    }
  };

  const validateApiForm = (data: any) => {
    const errors: {[key: string]: string} = {};
    
    if (!data.name?.trim()) {
      errors.name = 'API名称是必填项';
    }
    
    if (!data.apiKey?.trim()) {
      errors.apiKey = 'API Key是必填项';
    }
    
    if (!data.baseUrl?.trim()) {
      errors.baseUrl = 'Base URL是必填项';
    } else if (!/^https?:\/\/.+/.test(data.baseUrl)) {
      errors.baseUrl = 'Base URL格式不正确，请以http://或https://开头';
    }
    
    if (!data.model?.trim()) {
      errors.model = '模型名称是必填项';
    }
    
    if (data.maxTokens && (data.maxTokens < 1 || data.maxTokens > 32000)) {
      errors.maxTokens = '最大Token数应在1-32000之间';
    }
    
    if (data.temperature && (data.temperature < 0 || data.temperature > 2)) {
      errors.temperature = '温度参数应在0-2之间';
    }
    
    return errors;
  };

  const handleAddApi = async () => {
    console.log('🆕 调用新增配置功能 - handleAddApi', { configName: newApi.name });
    
    const errors = validateApiForm({
      name: newApi.name,
      apiKey: newApi.apiKey,
      baseUrl: newApi.baseUrl,
      model: newApi.model,
      maxTokens: newApi.maxTokens,
      temperature: newApi.temperature
    });
    setValidationErrors(errors);
    
    if (Object.keys(errors).length > 0) {
      setError('请修正表单中的错误');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      console.log('📡 发送POST请求创建配置', { url: '/api/v1/ai-config/' });
      const configData: CreateAIConfigRequest = {
        name: newApi.name,
        provider: 'custom',
        api_key: newApi.apiKey,
        api_base: newApi.baseUrl,
        model: newApi.model,
        max_tokens: newApi.maxTokens,
        temperature: newApi.temperature,
        is_active: true
      };

      const response = await aiConfigService.createConfig(configData);
      if (response.code === 200) {
        setAiConfigs([...aiConfigs, response.data]);
        setNewApi({
          provider: 'custom',
          name: '',
          apiKey: '',
          baseUrl: '',
          model: '',
          maxTokens: 4000,
          temperature: 0.7
        });
        setValidationErrors({});
        setError(null); // 清除之前的错误
      } else {
        setError(response.message || '添加AI配置失败');
      }
    } catch (err: any) {
      // 处理HTTP错误响应
      if (err.response?.status === 400 && err.response?.data?.detail) {
        setError(err.response.data.detail);
      } else if (err.response?.data?.message) {
        setError(err.response.data.message);
      } else {
        setError(err.message || '添加AI配置失败');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleEditApi = (config: AIConfig) => {
    setEditingApi({
      ...config,
      api_key: config.api_key // 保持原有的API key
    });
    setValidationErrors({});
  };

  const handleUpdateApi = async () => {
    if (!editingApi) return;
    
    console.log('🔄 调用编辑保存功能 - handleUpdateApi', { configId: editingApi.id, configName: editingApi.name });
    
    const errors = validateApiForm({
      name: editingApi.name,
      apiKey: editingApi.api_key,
      baseUrl: editingApi.api_base,
      model: editingApi.model,
      maxTokens: editingApi.max_tokens,
      temperature: editingApi.temperature
    });
    setValidationErrors(errors);
    
    if (Object.keys(errors).length > 0) {
      setError('请修正表单中的错误');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      console.log('📡 发送PUT请求更新配置', { url: `/api/v1/ai-config/${editingApi.id}` });
      const response = await aiConfigService.updateConfig(editingApi.id, {
        name: editingApi.name,
        provider: editingApi.provider,
        api_key: editingApi.api_key,
        api_base: editingApi.api_base,
        model: editingApi.model,
        max_tokens: editingApi.max_tokens,
        temperature: editingApi.temperature
      });
      
      if (response.code === 200) {
        setAiConfigs(aiConfigs.map(config => 
          config.id === editingApi.id ? response.data : config
        ));
        setEditingApi(null);
        setValidationErrors({});
      } else {
        setError(response.message || '更新AI配置失败');
      }
    } catch (err: any) {
      setError(err.message || '更新AI配置失败');
    } finally {
      setLoading(false);
    }
  };

  const handleCancelEdit = () => {
    setEditingApi(null);
    setValidationErrors({});
  };

  const handleDeleteApi = async (configId: number) => {
    if (!confirm('确定要删除这个AI配置吗？')) return;

    setLoading(true);
    try {
      const response = await aiConfigService.deleteConfig(configId);
      if (response.code === 200) {
        setAiConfigs(aiConfigs.filter(config => config.id !== configId));
      } else {
        setError(response.message || '删除AI配置失败');
      }
    } catch (err: any) {
      setError(err.message || '删除AI配置失败');
    } finally {
      setLoading(false);
    }
  };

  const handleToggleApi = async (configId: number, isActive: boolean) => {
    setLoading(true);
    try {
      const response = isActive 
        ? await aiConfigService.activateConfig(configId)
        : await aiConfigService.deactivateConfig(configId);
      
      if (response.code === 200) {
        setAiConfigs(aiConfigs.map(config => 
          config.id === configId ? { ...config, is_active: isActive } : config
        ));
      } else {
        setError(response.message || '更新AI配置状态失败');
      }
    } catch (err: any) {
      setError(err.message || '更新AI配置状态失败');
    } finally {
      setLoading(false);
    }
  };

  const handleTestApi = async (configId: number) => {
    setLoading(true);
    try {
      const response = await aiConfigService.testConfig(configId);
      if (response.code === 200) {
        const result = response.data;
        if (result.success) {
          alert(`测试成功！\n响应时间: ${result.response_time}\n模型: ${result.model_info?.model}`);
        } else {
          alert(`测试失败: ${result.message}`);
        }
      } else {
        setError(response.message || 'AI配置测试失败');
      }
    } catch (err: any) {
      setError(err.message || 'AI配置测试失败');
    } finally {
      setLoading(false);
    }
  };



  // 加载标签组列表
  const loadTagGroups = async () => {
    setLoadingTagGroups(true);
    try {
      const response = await tagGroupService.getTagGroups({ include_tags: true });
      
      if (response.code === 200 && response.data) {
        setTagGroups(response.data);
      } else {
        toast.error('获取标签组列表失败');
      }
    } catch (error) {
      console.error('Load tag groups error:', error);
      toast.error('获取标签组列表失败');
    } finally {
      setLoadingTagGroups(false);
    }
  };

  // 创建标签组
  const handleCreateTagGroup = async () => {
    if (!tagGroupFormData.name.trim()) {
      toast.error('请输入标签组名称');
      return;
    }
    
    try {
      const createData: CreateTagGroupRequest = {
        name: tagGroupFormData.name.trim(),
        description: tagGroupFormData.description.trim() || undefined,
        is_active: tagGroupFormData.is_active,
        tags: []
      };
      
      const response = await tagGroupService.createTagGroup(createData);
      
      if (response.code === 200) {
        toast.success('标签组创建成功');
        setShowTagGroupCreateForm(false);
        resetTagGroupForm();
        loadTagGroups();
      } else {
        toast.error(response.message || '创建标签组失败');
      }
    } catch (error) {
      console.error('Create tag group error:', error);
      toast.error('创建标签组失败');
    }
  };

  // 编辑标签组
  const handleEditTagGroup = (tagGroup: TagGroup) => {
    setEditingTagGroup(tagGroup);
    setTagGroupFormData({
      name: tagGroup.name,
      description: tagGroup.description || '',
      is_active: tagGroup.is_active
    });
    setShowTagGroupEditForm(true);
  };

  // 更新标签组
  const handleUpdateTagGroup = async () => {
    if (!editingTagGroup) return;
    
    try {
      const updateData: UpdateTagGroupRequest = {
        name: tagGroupFormData.name.trim() || undefined,
        description: tagGroupFormData.description.trim() || undefined,
        is_active: tagGroupFormData.is_active
      };
      
      const response = await tagGroupService.updateTagGroup(editingTagGroup.id, updateData);
      
      if (response.code === 200) {
        toast.success('标签组更新成功');
        setShowTagGroupEditForm(false);
        setEditingTagGroup(null);
        resetTagGroupForm();
        loadTagGroups();
      } else {
        toast.error(response.message || '更新标签组失败');
      }
    } catch (error) {
      console.error('Update tag group error:', error);
      toast.error('更新标签组失败');
    }
  };

  // 删除标签组
  const handleDeleteTagGroup = async (tagGroup: TagGroup) => {
    if (!confirm(`确定要删除标签组 "${tagGroup.name}" 吗？这将同时删除该组下的所有标签。`)) {
      return;
    }
    
    try {
      const response = await tagGroupService.deleteTagGroup(tagGroup.id);
      
      if (response.code === 200) {
        toast.success('标签组删除成功');
        loadTagGroups();
      } else {
        toast.error(response.message || '删除标签组失败');
      }
    } catch (error) {
      console.error('Delete tag group error:', error);
      toast.error('删除标签组失败');
    }
  };

  // 创建标签
  const handleCreateTag = async (groupId: number) => {
    if (!tagFormData.name.trim()) {
      toast.error('请输入标签名称');
      return;
    }
    
    try {
      const createData: CreateTagRequest = {
        name: tagFormData.name.trim(),
        color: tagFormData.color || undefined,
        is_active: tagFormData.is_active
      };
      
      const response = await tagGroupService.createTag(groupId, createData);
      
      if (response.code === 200) {
        toast.success('标签创建成功');
        setShowTagCreateForm({ groupId: null });
        resetTagForm();
        loadTagGroups();
      } else {
        toast.error(response.message || '创建标签失败');
      }
    } catch (error: any) {
      console.error('Create tag error:', error);
      const errorMessage = error?.response?.data?.detail || error?.response?.data?.message || '创建标签失败';
      toast.error(errorMessage);
    }
  };

  // 删除标签
  const handleDeleteTag = async (tag: Tag) => {
    if (!confirm(`确定要删除标签 "${tag.name}" 吗？`)) {
      return;
    }
    
    try {
      const response = await tagGroupService.deleteTag(tag.id);
      
      if (response.code === 200) {
        toast.success('标签删除成功');
        loadTagGroups();
      } else {
        toast.error(response.message || '删除标签失败');
      }
    } catch (error: any) {
      console.error('Delete tag error:', error);
      const errorMessage = error?.response?.data?.detail || error?.response?.data?.message || '删除标签失败';
      toast.error(errorMessage);
    }
  };

  // 批量创建标签
  const handleBatchCreateTags = async (groupId: number) => {
    if (!batchTagInput.trim()) {
      toast.error('请输入标签名称');
      return;
    }
    
    const tagNames = batchTagInput.split(',').map(name => name.trim()).filter(name => name);
    if (tagNames.length === 0) {
      toast.error('请输入有效的标签名称');
      return;
    }
    
    try {
      const response = await tagGroupService.batchCreateTags(groupId, tagNames);
      
      if (response.code === 200) {
        toast.success(response.message || '标签批量创建成功');
        setShowBatchTagForm({ groupId: null });
        setBatchTagInput('');
        loadTagGroups();
      } else {
        toast.error(response.message || '批量创建标签失败');
      }
    } catch (error: any) {
      console.error('Batch create tags error:', error);
      const errorMessage = error?.response?.data?.detail || error?.response?.data?.message || '批量创建标签失败';
      toast.error(errorMessage);
    }
  };

  // 重置标签组表单
  const resetTagGroupForm = () => {
    setTagGroupFormData({
      name: '',
      description: '',
      is_active: true
    });
  };

  // 重置标签表单
  const resetTagForm = () => {
    setTagFormData({
      name: '',
      color: PRESET_TAG_COLORS[0].value,
      is_active: true
    });
  };

  // 加载用户列表
  const loadUsers = async (params: UserSearchParams = {}) => {
    setLoadingUsers(true);
    try {
      const response = await userManagementService.getUsersList({
        page: userCurrentPage,
        size: userPageSize,
        ...params
      });
      
      if (response.code === 200 && response.data) {
        setUsers(response.data.items);
        setUserTotal(response.data.total);
      } else {
        toast.error('获取用户列表失败');
      }
    } catch (error) {
      console.error('Load users error:', error);
      toast.error('获取用户列表失败');
    } finally {
      setLoadingUsers(false);
    }
  };

  // 搜索用户
  const handleUserSearch = () => {
    const params: UserSearchParams = {};
    if (userSearchForm.search) params.search = userSearchForm.search;
    if (userSearchForm.role) params.role = userSearchForm.role;
    if (userSearchForm.is_active !== '') params.is_active = userSearchForm.is_active === 'true';
    if (userSearchForm.is_verified !== '') params.is_verified = userSearchForm.is_verified === 'true';
    
    setUserSearchParams(params);
    setUserCurrentPage(1);
  };

  // 重置用户搜索
  const handleResetUserSearch = () => {
    setUserSearchForm({
      search: '',
      role: '',
      is_active: '',
      is_verified: ''
    });
    setUserSearchParams({});
    setUserCurrentPage(1);
  };

  // 创建用户
  const handleCreateUser = async () => {
    try {
      const createData: AdminUserCreateRequest = {
        email: userFormData.email || undefined,
        username: userFormData.username || undefined,
        full_name: userFormData.full_name || undefined,
        password: userFormData.password || undefined,
        role: userFormData.role,
        is_active: userFormData.is_active,
        is_verified: userFormData.is_verified
      };
      
      const response = await userManagementService.createUser(createData);
      
      if (response.code === 200) {
        toast.success('用户创建成功');
        setShowUserCreateForm(false);
        resetUserForm();
        loadUsers(userSearchParams);
      } else {
        toast.error(response.message || '创建用户失败');
      }
    } catch (error) {
      console.error('Create user error:', error);
      toast.error('创建用户失败');
    }
  };

  // 编辑用户
  const handleEditUser = (user: UserListItem) => {
    setEditingUser(user);
    setUserFormData({
      email: user.email,
      username: user.username || '',
      full_name: user.full_name || '',
      password: '',
      role: user.role,
      is_active: user.is_active,
      is_verified: user.is_verified
    });
    setShowUserEditForm(true);
  };

  // 更新用户
  const handleUpdateUser = async () => {
    if (!editingUser) return;
    
    try {
      const updateData: AdminUserUpdateRequest = {
        email: userFormData.email || undefined,
        username: userFormData.username || undefined,
        full_name: userFormData.full_name || undefined,
        role: userFormData.role,
        is_active: userFormData.is_active,
        is_verified: userFormData.is_verified
      };
      
      const response = await userManagementService.updateUser(editingUser.id, updateData);
      
      if (response.code === 200) {
        toast.success('用户更新成功');
        setShowUserEditForm(false);
        setEditingUser(null);
        resetUserForm();
        loadUsers(userSearchParams);
      } else {
        toast.error(response.message || '更新用户失败');
      }
    } catch (error) {
      console.error('Update user error:', error);
      toast.error('更新用户失败');
    }
  };

  // 切换用户状态
  const handleToggleUserStatus = async (user: UserListItem) => {
    try {
      const response = await userManagementService.updateUserStatus(user.id, {
        is_active: !user.is_active,
        reason: !user.is_active ? '管理员启用' : '管理员禁用'
      });
      
      if (response.code === 200) {
        toast.success(`用户已${!user.is_active ? '启用' : '禁用'}`);
        loadUsers(userSearchParams);
      } else {
        toast.error(response.message || '操作失败');
      }
    } catch (error) {
      console.error('Toggle user status error:', error);
      toast.error('操作失败');
    }
  };

  // 删除用户
  const handleDeleteUser = async (user: UserListItem) => {
    if (!confirm(`确定要删除用户 ${user.username || user.email} 吗？`)) {
      return;
    }
    
    try {
      const response = await userManagementService.deleteUser(user.id);
      
      if (response.code === 200) {
        toast.success('用户删除成功');
        loadUsers(userSearchParams);
      } else {
        toast.error(response.message || '删除用户失败');
      }
    } catch (error) {
      console.error('Delete user error:', error);
      toast.error('删除用户失败');
    }
  };

  // 重置用户表单
  const resetUserForm = () => {
    setUserFormData({
      email: '',
      username: '',
      full_name: '',
      password: '',
      role: 'user',
      is_active: true,
      is_verified: false
    });
  };

  // 角色显示名称
  const getRoleDisplayName = (role: string) => {
    const roleMap: { [key: string]: string } = {
      'user': '普通用户',
      'premium': 'VIP用户',
      'admin': '管理员'
    };
    return roleMap[role] || role;
  };

  // 状态显示
  const getStatusBadge = (isActive: boolean) => {
    return (
      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
        isActive 
          ? 'bg-green-100 text-green-800' 
          : 'bg-red-100 text-red-800'
      }`}>
        {isActive ? '正常' : '禁用'}
      </span>
    );
  };

  // 验证状态显示
  const getVerifiedBadge = (isVerified: boolean) => {
    return (
      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
        isVerified 
          ? 'bg-blue-100 text-blue-800' 
          : 'bg-gray-100 text-gray-800'
      }`}>
        {isVerified ? '已验证' : '未验证'}
      </span>
    );
  };

  const handleSaveBasicSettings = () => {
    // 这里应该调用API保存设置
    alert('基础设置已保存');
  };

  // 检查用户权限
  if (user?.role !== 'admin') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="mb-4">
            <i className="fas fa-lock text-6xl text-gray-400"></i>
          </div>
          <h2 className="text-2xl font-bold text-gray-800 mb-2">访问被拒绝</h2>
          <p className="text-gray-600 mb-4">
            只有管理员才能访问系统配置页面。
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-800">系统配置</h1>
        <div className="flex space-x-3">
          <button 
            className="btn-secondary"
            onClick={() => handleExportConfigs()}
            disabled={loading}
          >
            <i className="fas fa-download mr-2"></i>
            导出配置
          </button>
          <button 
            className="btn-primary"
            onClick={() => loadConfigs()}
            disabled={loading}
          >
            <i className={`fas ${loading ? 'fa-spinner fa-spin' : 'fa-sync'} mr-2`}></i>
            刷新配置
          </button>
        </div>
      </div>

      {/* 错误提示 */}
      {error && (
        <div className="mb-4 bg-red-50 border border-red-200 rounded-md p-3">
          <div className="flex">
            <i className="fas fa-exclamation-circle text-red-400 mr-2 mt-0.5"></i>
            <span className="text-sm text-red-700">{error}</span>
            <button 
              onClick={() => setError(null)}
              className="ml-auto text-red-400 hover:text-red-600"
            >
              <i className="fas fa-times"></i>
            </button>
          </div>
        </div>
      )}

      {/* 标签页导航 */}
      <div className="bg-white rounded-lg shadow-sm">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8 px-6">
            {[
              { key: 'basic', label: '基础设置', icon: 'fa-cog' },
              { key: 'ai', label: 'AI API配置', icon: 'fa-robot' },
              { key: 'template', label: '提示词模板', icon: 'fa-file-alt' },
              { key: 'tags', label: '预设标签组', icon: 'fa-tags' },
              { key: 'video-download', label: '视频下载配置', icon: 'fa-download' },
              { key: 'users', label: '用户管理', icon: 'fa-users' }
            ].map((tab) => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm flex items-center space-x-2 ${
                  activeTab === tab.key
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <i className={`fas ${tab.icon}`}></i>
                <span>{tab.label}</span>
                {categories.find(c => c.category === tab.key) && (
                  <span className="ml-2 bg-gray-200 text-gray-600 text-xs px-2 py-1 rounded-full">
                    {categories.find(c => c.category === tab.key)?.count || 0}
                  </span>
                )}
              </button>
            ))}
          </nav>
        </div>

        <div className="p-6">
          {/* 基础设置 */}
          {activeTab === 'basic' && (
            <div className="space-y-6">
              <div className="flex justify-between items-center">
                <h2 className="text-lg font-medium text-gray-900">基础设置</h2>
                <button 
                  onClick={handleCreateConfig}
                  className="btn-primary"
                  disabled={loading}
                >
                  <i className="fas fa-plus mr-2"></i>
                  添加配置
                </button>
              </div>

              {/* 添加新配置表单 */}
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="text-md font-medium text-gray-800 mb-4">添加新配置</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  <input
                    type="text"
                    placeholder="配置键"
                    value={newConfigForm.key}
                    onChange={(e) => setNewConfigForm({...newConfigForm, key: e.target.value})}
                    className="input-field"
                  />
                  <input
                    type="text"
                    placeholder="配置值"
                    value={newConfigForm.value}
                    onChange={(e) => setNewConfigForm({...newConfigForm, value: e.target.value})}
                    className="input-field"
                  />
                  <select
                    value={newConfigForm.data_type}
                    onChange={(e) => setNewConfigForm({...newConfigForm, data_type: e.target.value})}
                    className="input-field"
                  >
                    <option value="string">字符串</option>
                    <option value="number">数字</option>
                    <option value="boolean">布尔值</option>
                    <option value="json">JSON</option>
                  </select>
                </div>
                <div className="mt-4">
                  <textarea
                    placeholder="配置描述"
                    value={newConfigForm.description}
                    onChange={(e) => setNewConfigForm({...newConfigForm, description: e.target.value})}
                    rows={2}
                    className="input-field w-full"
                  />
                </div>
                <div className="mt-4 flex space-x-4">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={newConfigForm.is_public}
                      onChange={(e) => setNewConfigForm({...newConfigForm, is_public: e.target.checked})}
                      className="mr-2"
                    />
                    <span className="text-sm text-gray-700">公开配置</span>
                  </label>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={newConfigForm.is_encrypted}
                      onChange={(e) => setNewConfigForm({...newConfigForm, is_encrypted: e.target.checked})}
                      className="mr-2"
                    />
                    <span className="text-sm text-gray-700">加密存储</span>
                  </label>
                </div>
              </div>

              {/* 配置列表 */}
              <div className="space-y-4">
                {filteredConfigs.map((config) => (
                  <div key={config.id} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <div className="flex items-center space-x-3">
                          <h3 className="text-lg font-bold text-gray-900">{config.key}</h3>
                          <span className={`px-2 py-1 text-xs rounded-full ${
                            config.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                          }`}>
                            {config.is_active ? '启用' : '禁用'}
                          </span>
                          {config.is_public && (
                            <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                              公开
                            </span>
                          )}
                          {config.is_encrypted && (
                            <span className="px-2 py-1 bg-yellow-100 text-yellow-800 text-xs rounded">
                              加密
                            </span>
                          )}
                        </div>
                        {editingConfig?.id === config.id ? (
                          <div className="mt-2 space-y-2">
                            <input
                              type="text"
                              value={editingConfig.value}
                              onChange={(e) => setEditingConfig({...editingConfig, value: e.target.value})}
                              className="input-field w-full"
                            />
                            <textarea
                              value={editingConfig.description}
                              onChange={(e) => setEditingConfig({...editingConfig, description: e.target.value})}
                              rows={2}
                              className="input-field w-full"
                            />
                          </div>
                        ) : (
                          <div className="mt-2">
                            <p className="text-sm text-gray-600">{config.value}</p>
                            {config.description && (
                              <p className="text-sm text-gray-500 mt-1">{config.description}</p>
                            )}
                          </div>
                        )}
                      </div>
                      <div className="flex space-x-2">
                        {editingConfig?.id === config.id ? (
                          <>
                            <button
                              onClick={() => handleUpdateConfig(config)}
                              className="px-3 py-1 text-sm bg-green-100 text-green-800 rounded hover:bg-green-200"
                              disabled={loading}
                            >
                              保存
                            </button>
                            <button
                              onClick={() => setEditingConfig(null)}
                              className="px-3 py-1 text-sm bg-gray-100 text-gray-800 rounded hover:bg-gray-200"
                            >
                              取消
                            </button>
                          </>
                        ) : (
                          <>
                            <button
                              onClick={() => setEditingConfig(config)}
                              className="px-3 py-1 text-sm bg-blue-100 text-blue-800 rounded hover:bg-blue-200"
                            >
                              编辑
                            </button>
                            <button
                              onClick={() => handleDeleteConfig(config.key)}
                              className="px-3 py-1 text-sm bg-red-100 text-red-800 rounded hover:bg-red-200"
                              disabled={loading}
                            >
                              删除
                            </button>
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">系统名称</label>
                  <input
                    type="text"
                    value={basicSettings.systemName}
                    onChange={(e) => setBasicSettings({...basicSettings, systemName: e.target.value})}
                    className="input-field"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">系统描述</label>
                  <input
                    type="text"
                    value={basicSettings.systemDescription}
                    onChange={(e) => setBasicSettings({...basicSettings, systemDescription: e.target.value})}
                    className="input-field"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">最大文件大小 (MB)</label>
                  <input
                    type="number"
                    value={basicSettings.maxFileSize}
                    onChange={(e) => setBasicSettings({...basicSettings, maxFileSize: parseInt(e.target.value)})}
                    className="input-field"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">备份间隔 (小时)</label>
                  <input
                    type="number"
                    value={basicSettings.backupInterval}
                    onChange={(e) => setBasicSettings({...basicSettings, backupInterval: parseInt(e.target.value)})}
                    className="input-field"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">日志级别</label>
                  <select
                    value={basicSettings.logLevel}
                    onChange={(e) => setBasicSettings({...basicSettings, logLevel: e.target.value})}
                    className="input-field"
                  >
                    <option value="debug">Debug</option>
                    <option value="info">Info</option>
                    <option value="warn">Warning</option>
                    <option value="error">Error</option>
                  </select>
                </div>
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="autoBackup"
                    checked={basicSettings.autoBackup}
                    onChange={(e) => setBasicSettings({...basicSettings, autoBackup: e.target.checked})}
                    className="mr-2"
                  />
                  <label htmlFor="autoBackup" className="text-sm font-medium text-gray-700">启用自动备份</label>
                </div>
              </div>
              <div className="flex justify-end">
                <button onClick={handleSaveBasicSettings} className="btn-primary">
                  保存设置
                </button>
              </div>
            </div>
          )}

          {/* AI API配置 */}
          {activeTab === 'ai' && (
            <div className="space-y-6">
              <div className="flex justify-between items-center">
                <h2 className="text-lg font-medium text-gray-900">AI API配置</h2>
              </div>
              
              {/* 添加新API */}
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="text-md font-medium text-gray-800 mb-4">🆕 添加新的AI API配置</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  <div>
                    <input
                      type="text"
                      placeholder="API名称 *"
                      value={newApi.name}
                      onChange={(e) => setNewApi({...newApi, name: e.target.value})}
                      className={`input-field ${validationErrors.name ? 'border-red-500' : ''}`}
                    />
                    {validationErrors.name && (
                      <p className="text-red-500 text-xs mt-1">{validationErrors.name}</p>
                    )}
                  </div>
                  <div>
                    <input
                      type="text"
                      placeholder="API Key *"
                      value={newApi.apiKey}
                      onChange={(e) => setNewApi({...newApi, apiKey: e.target.value})}
                      className={`input-field ${validationErrors.apiKey ? 'border-red-500' : ''}`}
                    />
                    {validationErrors.apiKey && (
                      <p className="text-red-500 text-xs mt-1">{validationErrors.apiKey}</p>
                    )}
                  </div>
                  <div>
                    <input
                      type="text"
                      placeholder="模型名称 *"
                      value={newApi.model}
                      onChange={(e) => setNewApi({...newApi, model: e.target.value})}
                      className={`input-field ${validationErrors.model ? 'border-red-500' : ''}`}
                    />
                    {validationErrors.model && (
                      <p className="text-red-500 text-xs mt-1">{validationErrors.model}</p>
                    )}
                  </div>
                </div>
                <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <input
                      type="text"
                      placeholder="Base URL *"
                      value={newApi.baseUrl}
                      onChange={(e) => setNewApi({...newApi, baseUrl: e.target.value})}
                      className={`input-field ${validationErrors.baseUrl ? 'border-red-500' : ''}`}
                    />
                    {validationErrors.baseUrl && (
                      <p className="text-red-500 text-xs mt-1">{validationErrors.baseUrl}</p>
                    )}
                  </div>
                  <div>
                    <input
                      type="number"
                      placeholder="最大Token数"
                      value={newApi.maxTokens}
                      onChange={(e) => setNewApi({...newApi, maxTokens: parseInt(e.target.value)})}
                      className={`input-field ${validationErrors.maxTokens ? 'border-red-500' : ''}`}
                    />
                    {validationErrors.maxTokens && (
                      <p className="text-red-500 text-xs mt-1">{validationErrors.maxTokens}</p>
                    )}
                  </div>
                  <div>
                    <input
                      type="number"
                      placeholder="温度 (0-2)"
                      step="0.1"
                      min="0"
                      max="2"
                      value={newApi.temperature}
                      onChange={(e) => setNewApi({...newApi, temperature: parseFloat(e.target.value)})}
                      className={`input-field ${validationErrors.temperature ? 'border-red-500' : ''}`}
                    />
                    {validationErrors.temperature && (
                      <p className="text-red-500 text-xs mt-1">{validationErrors.temperature}</p>
                    )}
                  </div>
                </div>
                <div className="mt-4">
                  <button onClick={handleAddApi} className="btn-primary" disabled={loading}>
                    <i className={`fas ${loading ? 'fa-spinner fa-spin' : 'fa-plus'} mr-2`}></i>
                    {loading ? '创建中...' : '创建新配置'}
                  </button>
                </div>
              </div>

              {/* 已有配置列表 */}
              <div className="space-y-4">
                <h3 className="text-md font-medium text-gray-800">📋 已有AI API配置</h3>
                {loadingAiConfigs ? (
                  <div className="text-center py-8">
                    <i className="fas fa-spinner fa-spin text-2xl text-gray-400 mb-2"></i>
                    <p className="text-gray-500">加载AI配置中...</p>
                  </div>
                ) : aiConfigs.length === 0 ? (
                  <div className="text-center py-8">
                    <i className="fas fa-robot text-4xl text-gray-300 mb-4"></i>
                    <p className="text-gray-500">暂无AI配置</p>
                  </div>
                ) : (
                  aiConfigs.map((config) => (
                    <div key={config.id} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <div className="flex items-center space-x-3">
                            <h3 className="text-lg font-bold text-gray-900">{config.name}</h3>
                            <span className={`px-2 py-1 text-xs rounded-full ${
                              config.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                            }`}>
                              {config.is_active ? '已启用' : '已禁用'}
                            </span>

                          </div>
                          {editingApi?.id === config.id ? (
                            <div className="mt-4 space-y-3">
                              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                <div>
                                  <input
                                    type="text"
                                    placeholder="API名称"
                                    value={editingApi.name}
                                    onChange={(e) => setEditingApi({...editingApi, name: e.target.value})}
                                    className="input-field w-full"
                                  />
                                </div>
                                <div>
                                  <input
                                    type="text"
                                    placeholder="模型名称 *"
                                    value={editingApi.model}
                                    onChange={(e) => setEditingApi({...editingApi, model: e.target.value})}
                                    className={`input-field w-full ${validationErrors.model ? 'border-red-500' : ''}`}
                                  />
                                  {validationErrors.model && (
                                    <p className="text-red-500 text-xs mt-1">{validationErrors.model}</p>
                                  )}
                                </div>
                              </div>
                              <div>
                                <input
                                  type="text"
                                  placeholder="API Key *"
                                  value={editingApi.api_key}
                                  onChange={(e) => setEditingApi({...editingApi, api_key: e.target.value})}
                                  className={`input-field w-full ${validationErrors.apiKey ? 'border-red-500' : ''}`}
                                />
                                {validationErrors.apiKey && (
                                  <p className="text-red-500 text-xs mt-1">{validationErrors.apiKey}</p>
                                )}
                              </div>
                              <div>
                                <input
                                  type="text"
                                  placeholder="Base URL *"
                                  value={editingApi.api_base}
                                  onChange={(e) => setEditingApi({...editingApi, api_base: e.target.value})}
                                  className={`input-field w-full ${validationErrors.baseUrl ? 'border-red-500' : ''}`}
                                />
                                {validationErrors.baseUrl && (
                                  <p className="text-red-500 text-xs mt-1">{validationErrors.baseUrl}</p>
                                )}
                              </div>
                              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                <div>
                                  <input
                                    type="number"
                                    placeholder="最大Token数"
                                    value={editingApi.max_tokens}
                                    onChange={(e) => setEditingApi({...editingApi, max_tokens: parseInt(e.target.value)})}
                                    className={`input-field w-full ${validationErrors.maxTokens ? 'border-red-500' : ''}`}
                                  />
                                  {validationErrors.maxTokens && (
                                    <p className="text-red-500 text-xs mt-1">{validationErrors.maxTokens}</p>
                                  )}
                                </div>
                                <div>
                                  <input
                                    type="number"
                                    placeholder="温度 (0-2)"
                                    step="0.1"
                                    min="0"
                                    max="2"
                                    value={editingApi.temperature}
                                    onChange={(e) => setEditingApi({...editingApi, temperature: parseFloat(e.target.value)})}
                                    className={`input-field w-full ${validationErrors.temperature ? 'border-red-500' : ''}`}
                                  />
                                  {validationErrors.temperature && (
                                    <p className="text-red-500 text-xs mt-1">{validationErrors.temperature}</p>
                                  )}
                                </div>
                              </div>
                            </div>
                          ) : (
                            <div className="mt-2 space-y-1">
                              <p className="text-sm text-gray-600">模型: {config.model}</p>
                              <p className="text-sm text-gray-500">API Key: {'*'.repeat(Math.min(config.api_key?.length || 0, 20))}</p>
                              <p className="text-sm text-gray-500">Base URL: {config.api_base}</p>
                              <div className="flex space-x-4 text-sm text-gray-500">
                                <span>最大Token: {config.max_tokens}</span>
                                <span>温度: {config.temperature}</span>
                              </div>
                              {config.created_at && (
                                <p className="text-xs text-gray-400">创建时间: {new Date(config.created_at).toLocaleString()}</p>
                              )}
                            </div>
                          )}
                        </div>
                        <div className="flex space-x-2">
                          {editingApi?.id === config.id ? (
                            <>
                              <button
                                onClick={handleUpdateApi}
                                className="px-3 py-1 text-sm bg-green-100 text-green-800 rounded hover:bg-green-200"
                                disabled={loading}
                              >
                                保存
                              </button>
                              <button
                                onClick={handleCancelEdit}
                                className="px-3 py-1 text-sm bg-gray-100 text-gray-800 rounded hover:bg-gray-200"
                              >
                                取消
                              </button>
                            </>
                          ) : (
                            <>
                              <button
                                onClick={() => handleTestApi(config.id)}
                                className="px-3 py-1 text-sm bg-blue-100 text-blue-800 rounded hover:bg-blue-200"
                                disabled={loading}
                              >
                                测试
                              </button>
                              <button
                                onClick={() => handleEditApi(config)}
                                className="px-3 py-1 text-sm bg-purple-100 text-purple-800 rounded hover:bg-purple-200"
                              >
                                编辑
                              </button>
                              <button
                                onClick={() => handleToggleApi(config.id, !config.is_active)}
                                className={`px-3 py-1 text-sm rounded ${
                                  config.is_active
                                    ? 'bg-yellow-100 text-yellow-800 hover:bg-yellow-200'
                                    : 'bg-green-100 text-green-800 hover:bg-green-200'
                                }`}
                                disabled={loading}
                              >
                                {config.is_active ? '禁用' : '启用'}
                              </button>
                              <button
                                onClick={() => handleDeleteApi(config.id)}
                                className="px-3 py-1 text-sm bg-red-100 text-red-800 rounded hover:bg-red-200"
                                disabled={loading}
                              >
                                删除
                              </button>
                            </>
                          )}
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}

          {/* 提示词模板 */}
          {activeTab === 'template' && (
            <div className="space-y-6">
              <div className="flex justify-between items-center">
                <h2 className="text-lg font-medium text-gray-900">提示词模板</h2>
              </div>
              
              {/* 添加新模板 */}
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="text-md font-medium text-gray-800 mb-4">添加新模板</h3>
                <div className="space-y-4">
                  <div className="mb-4">
                    <input
                      type="text"
                      placeholder="模板标题 *"
                      value={newTemplate.title}
                      onChange={(e) => setNewTemplate({...newTemplate, title: e.target.value})}
                      className={`input-field w-full ${templateValidationErrors.title ? 'border-red-500' : ''}`}
                    />
                    {templateValidationErrors.title && (
                      <p className="text-red-500 text-xs mt-1">{templateValidationErrors.title}</p>
                    )}
                  </div>
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                     <div className="flex flex-col">
                       <label className="text-sm font-medium text-gray-700 mb-2">模板内容</label>
                       <textarea
                         placeholder="请输入提示词模板内容，支持Markdown格式 *"
                         value={newTemplate.content}
                         onChange={(e) => setNewTemplate({...newTemplate, content: e.target.value})}
                         className={`input-field resize-y font-mono text-sm ${templateValidationErrors.content ? 'border-red-500' : ''}`}
                         style={{ minHeight: '300px', maxHeight: '600px' }}
                         rows={Math.max(10, newTemplate.content.split('\n').length + 2)}
                       />
                       {templateValidationErrors.content && (
                         <p className="text-red-500 text-xs mt-1">{templateValidationErrors.content}</p>
                       )}
                     </div>
                     <div className="flex flex-col">
                       <label className="text-sm font-medium text-gray-700 mb-2">预览效果</label>
                       <div 
                         className="border border-gray-300 rounded-md p-3 bg-gray-50 overflow-auto"
                         style={{ minHeight: '300px', maxHeight: '600px', height: `${Math.max(300, Math.min(600, newTemplate.content.split('\n').length * 24 + 100))}px` }}
                       >
                         <div className="prose prose-sm max-w-none">
                           {newTemplate.content ? (
                             <div dangerouslySetInnerHTML={{ __html: marked(newTemplate.content) }} />
                           ) : (
                             <p className="text-gray-400 italic">在左侧输入内容，这里将显示预览效果</p>
                           )}
                         </div>
                       </div>
                     </div>
                   </div>
                  <button 
                     onClick={handleAddTemplate} 
                     className="btn-primary"
                     disabled={loading}
                   >
                     {loading ? '添加中...' : '添加模板'}
                   </button>
                </div>
              </div>

              {/* 模板列表 */}
              <div className="space-y-4">
                {loadingTemplates ? (
                  <div className="text-center py-8">
                    <i className="fas fa-spinner fa-spin text-2xl text-gray-400 mb-2"></i>
                    <p className="text-gray-500">加载提示词模板中...</p>
                  </div>
                ) : templates.length === 0 ? (
                  <div className="text-center py-8">
                    <i className="fas fa-file-alt text-4xl text-gray-300 mb-4"></i>
                    <p className="text-gray-500">暂无提示词模板</p>
                  </div>
                ) : (
                  templates.map((template) => (
                    <div key={template.id} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          {editingTemplate?.id === template.id ? (
                            <div className="space-y-4">
                              <div>
                                <input
                                  type="text"
                                  placeholder="模板标题 *"
                                  value={editingTemplate.title}
                                  onChange={(e) => setEditingTemplate({...editingTemplate, title: e.target.value})}
                                  className={`input-field w-full ${templateValidationErrors.title ? 'border-red-500' : ''}`}
                                />
                                {templateValidationErrors.title && (
                                  <p className="text-red-500 text-xs mt-1">{templateValidationErrors.title}</p>
                                )}
                              </div>
                              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                                <div className="flex flex-col">
                                  <label className="text-sm font-medium text-gray-700 mb-2">模板内容</label>
                                  <textarea
                                    placeholder="请输入提示词模板内容，支持Markdown格式 *"
                                    value={editingTemplate.content}
                                    onChange={(e) => setEditingTemplate({...editingTemplate, content: e.target.value})}
                                    className={`input-field resize-y font-mono text-sm ${templateValidationErrors.content ? 'border-red-500' : ''}`}
                                    style={{ minHeight: '300px', maxHeight: '600px' }}
                                    rows={Math.max(10, editingTemplate.content.split('\n').length + 2)}
                                  />
                                  {templateValidationErrors.content && (
                                    <p className="text-red-500 text-xs mt-1">{templateValidationErrors.content}</p>
                                  )}
                                </div>
                                <div className="flex flex-col">
                                  <label className="text-sm font-medium text-gray-700 mb-2">预览效果</label>
                                  <div 
                                    className="border border-gray-300 rounded-md p-3 bg-gray-50 overflow-auto"
                                    style={{ minHeight: '300px', maxHeight: '600px', height: `${Math.max(300, Math.min(600, editingTemplate.content.split('\n').length * 24 + 100))}px` }}
                                  >
                                    <div className="prose prose-sm max-w-none">
                                      {editingTemplate.content ? (
                                        <div dangerouslySetInnerHTML={{ __html: marked(editingTemplate.content) }} />
                                      ) : (
                                        <p className="text-gray-400 italic">在左侧输入内容，这里将显示预览效果</p>
                                      )}
                                    </div>
                                  </div>
                                </div>
                              </div>
                            </div>
                          ) : (
                            <div>
                              <div className="flex items-center space-x-3 mb-2">
                                <h3 className="text-lg font-bold text-gray-900">{template.title}</h3>
                                <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded">
                                  使用次数: {template.usage_count}
                                </span>
                                {template.created_at && (
                                  <span className="text-xs text-gray-400">
                                    创建时间: {new Date(template.created_at).toLocaleString()}
                                  </span>
                                )}
                              </div>
                              <div className="prose prose-sm max-w-none">
                                <div dangerouslySetInnerHTML={{ __html: marked(template.content) }} />
                              </div>
                            </div>
                          )}
                        </div>
                        <div className="flex space-x-2 ml-4">
                          {editingTemplate?.id === template.id ? (
                            <>
                              <button
                                onClick={handleUpdateTemplate}
                                className="px-3 py-1 text-sm bg-green-100 text-green-800 rounded hover:bg-green-200"
                                disabled={loading}
                              >
                                {loading ? '保存中...' : '保存'}
                              </button>
                              <button
                                onClick={handleCancelEditTemplate}
                                className="px-3 py-1 text-sm bg-gray-100 text-gray-800 rounded hover:bg-gray-200"
                                disabled={loading}
                              >
                                取消
                              </button>
                            </>
                          ) : (
                            <>
                              <button
                                onClick={() => handleUseTemplate(template.id)}
                                className="px-3 py-1 text-sm bg-blue-100 text-blue-800 rounded hover:bg-blue-200"
                              >
                                使用
                              </button>
                              <button
                                onClick={() => handleEditTemplate(template)}
                                className="px-3 py-1 text-sm bg-yellow-100 text-yellow-800 rounded hover:bg-yellow-200"
                              >
                                编辑
                              </button>
                              <button
                                onClick={() => handleDeleteTemplate(template.id)}
                                className="px-3 py-1 text-sm bg-red-100 text-red-800 rounded hover:bg-red-200"
                                disabled={loading}
                              >
                                删除
                              </button>
                            </>
                          )}
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}

          {/* 预设标签组 */}
          {activeTab === 'tags' && (
            <div className="space-y-6">
              <div className="flex justify-between items-center">
                <h2 className="text-lg font-medium text-gray-900">预设标签组</h2>
                <button
                  onClick={() => setShowTagGroupCreateForm(true)}
                  className="btn-primary"
                >
                  <i className="fas fa-plus mr-2"></i>
                  新增标签组
                </button>
              </div>
              
              {/* 标签组列表 */}
              {loadingTagGroups ? (
                <div className="text-center py-8">
                  <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                  <p className="mt-2 text-gray-600">加载中...</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {tagGroups.map((group) => (
                    <div key={group.id} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex justify-between items-start mb-4">
                        <div>
                          <h3 className="text-lg font-bold text-gray-900">{group.name}</h3>
                          {group.description && (
                            <p className="text-sm text-gray-600 mt-1">{group.description}</p>
                          )}
                          <div className="flex items-center mt-2">
                            <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                              group.is_active 
                                ? 'bg-green-100 text-green-800' 
                                : 'bg-red-100 text-red-800'
                            }`}>
                              {group.is_active ? '启用' : '禁用'}
                            </span>
                            <span className="ml-2 text-xs text-gray-500">
                              {group.tags.length} 个标签
                            </span>
                          </div>
                        </div>
                        <div className="flex space-x-2">
                          <button
                            onClick={() => handleEditTagGroup(group)}
                            className="px-3 py-1 text-sm bg-blue-100 text-blue-800 rounded hover:bg-blue-200"
                          >
                            编辑
                          </button>
                          <button
                            onClick={() => handleDeleteTagGroup(group)}
                            className="px-3 py-1 text-sm bg-red-100 text-red-800 rounded hover:bg-red-200"
                          >
                            删除
                          </button>
                        </div>
                      </div>
                      
                      {/* 标签列表 */}
                      <div className="flex flex-wrap gap-2 mb-4">
                        {group.tags.map((tag) => (
                          <span 
                            key={tag.id} 
                            className="px-2 py-1 text-sm rounded flex items-center"
                            style={{
                              backgroundColor: tag.color ? `${tag.color}20` : '#EBF8FF',
                              color: tag.color || '#2B6CB0',
                              border: `1px solid ${tag.color || '#2B6CB0'}30`
                            }}
                          >
                            {tag.name}
                            <button
                              onClick={() => handleDeleteTag(tag)}
                              className="ml-2 hover:opacity-70"
                            >
                              <i className="fas fa-times text-xs"></i>
                            </button>
                          </span>
                        ))}
                      </div>
                      
                      {/* 标签操作按钮 */}
                      <div className="flex space-x-2">
                        <button
                          onClick={() => setShowTagCreateForm({ groupId: group.id })}
                          className="btn-secondary text-sm"
                        >
                          <i className="fas fa-plus mr-1"></i>
                          添加标签
                        </button>
                        <button
                          onClick={() => setShowBatchTagForm({ groupId: group.id })}
                          className="btn-secondary text-sm"
                        >
                          <i className="fas fa-layer-group mr-1"></i>
                          批量添加
                        </button>
                      </div>
                    </div>
                  ))}
                  
                  {tagGroups.length === 0 && (
                    <div className="text-center py-8 text-gray-500">
                      <i className="fas fa-tags text-4xl mb-4"></i>
                      <p>暂无标签组，点击上方按钮创建第一个标签组</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* 视频下载配置 */}
          {activeTab === 'video-download' && (
            <div className="space-y-6">
              <div className="flex justify-between items-center">
                <h2 className="text-lg font-medium text-gray-900">视频下载配置</h2>
                <button 
                  className="btn-primary"
                  onClick={() => window.location.reload()}
                >
                  <i className="fas fa-sync mr-2"></i>
                  刷新配置
                </button>
              </div>

              {/* 基础下载设置 */}
              <div className="bg-white border border-gray-200 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  <i className="fas fa-cog mr-2 text-blue-500"></i>
                  基础下载设置
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      默认下载路径
                    </label>
                    <input
                      type="text"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="/downloads/videos"
                      defaultValue="./downloads"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      最大并发下载数
                    </label>
                    <select className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
                      <option value="1">1个</option>
                      <option value="2" selected>2个</option>
                      <option value="3">3个</option>
                      <option value="5">5个</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      下载超时时间（秒）
                    </label>
                    <input
                      type="number"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      defaultValue="300"
                      min="30"
                      max="3600"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      自动重试次数
                    </label>
                    <select className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
                      <option value="0">不重试</option>
                      <option value="1">1次</option>
                      <option value="2" selected>2次</option>
                      <option value="3">3次</option>
                    </select>
                  </div>
                </div>
              </div>

              {/* 平台配置 */}
              <div className="bg-white border border-gray-200 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  <i className="fas fa-globe mr-2 text-green-500"></i>
                  平台配置
                </h3>
                <div className="space-y-4">
                  {[
                    { name: '抖音', key: 'douyin', icon: 'fab fa-tiktok', color: 'text-red-500' },
                    { name: 'TikTok', key: 'tiktok', icon: 'fab fa-tiktok', color: 'text-black' },
                    { name: 'B站', key: 'bilibili', icon: 'fas fa-play-circle', color: 'text-blue-500' },
                    { name: '小红书', key: 'xiaohongshu', icon: 'fas fa-book', color: 'text-pink-500' },
                    { name: '快手', key: 'kuaishou', icon: 'fas fa-video', color: 'text-yellow-500' },
                    { name: '微信视频号', key: 'weixin', icon: 'fab fa-weixin', color: 'text-green-500' }
                  ].map((platform) => (
                    <div key={platform.key} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center space-x-3">
                          <i className={`${platform.icon} ${platform.color} text-xl`}></i>
                          <span className="font-medium text-gray-900">{platform.name}</span>
                          <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">
                            已启用
                          </span>
                        </div>
                        <button className="text-blue-600 hover:text-blue-800 text-sm">
                          <i className="fas fa-cog mr-1"></i>
                          配置
                        </button>
                      </div>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Cookie配置
                          </label>
                          <textarea
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                            rows={2}
                            placeholder="请输入平台Cookie（可选，用于提高解析成功率）"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            User-Agent
                          </label>
                          <input
                            type="text"
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                            placeholder="自定义User-Agent（可选）"
                          />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* 高级设置 */}
              <div className="bg-white border border-gray-200 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  <i className="fas fa-sliders-h mr-2 text-purple-500"></i>
                  高级设置
                </h3>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-sm font-medium text-gray-900">启用代理下载</h4>
                      <p className="text-sm text-gray-500">通过代理服务器下载视频，提高成功率</p>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input type="checkbox" className="sr-only peer" />
                      <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                    </label>
                  </div>
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-sm font-medium text-gray-900">自动清理临时文件</h4>
                      <p className="text-sm text-gray-500">下载完成后自动清理临时文件</p>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input type="checkbox" className="sr-only peer" defaultChecked />
                      <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                    </label>
                  </div>
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-sm font-medium text-gray-900">启用下载历史记录</h4>
                      <p className="text-sm text-gray-500">记录所有下载历史，便于管理和统计</p>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input type="checkbox" className="sr-only peer" defaultChecked />
                      <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                    </label>
                  </div>
                </div>
              </div>

              {/* 保存按钮 */}
              <div className="flex justify-end space-x-3">
                <button className="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400">
                  重置配置
                </button>
                <button className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">
                  <i className="fas fa-save mr-2"></i>
                  保存配置
                </button>
              </div>
            </div>
          )}

          {/* 用户管理 */}
          {activeTab === 'users' && (
            <div className="space-y-6">
              <div className="flex justify-between items-center">
                <h2 className="text-lg font-medium text-gray-900">用户管理</h2>
                <button
                  onClick={() => setShowUserCreateForm(true)}
                  className="btn-primary"
                >
                  <i className="fas fa-plus mr-2"></i>
                  新增用户
                </button>
              </div>
              
              {/* 搜索和筛选 */}
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 mb-4">
                  <div>
                    <input
                      type="text"
                      value={userSearchForm.search}
                      onChange={(e) => setUserSearchForm({ ...userSearchForm, search: e.target.value })}
                      className="input-field"
                      placeholder="搜索用户名、邮箱或姓名"
                    />
                  </div>
                  <div>
                    <select
                      value={userSearchForm.role}
                      onChange={(e) => setUserSearchForm({ ...userSearchForm, role: e.target.value })}
                      className="input-field"
                    >
                      <option value="">全部角色</option>
                      <option value="user">普通用户</option>
                      <option value="premium">VIP用户</option>
                      <option value="admin">管理员</option>
                    </select>
                  </div>
                  <div>
                    <select
                      value={userSearchForm.is_active}
                      onChange={(e) => setUserSearchForm({ ...userSearchForm, is_active: e.target.value })}
                      className="input-field"
                    >
                      <option value="">全部状态</option>
                      <option value="true">正常</option>
                      <option value="false">禁用</option>
                    </select>
                  </div>
                  <div>
                    <select
                      value={userSearchForm.is_verified}
                      onChange={(e) => setUserSearchForm({ ...userSearchForm, is_verified: e.target.value })}
                      className="input-field"
                    >
                      <option value="">全部验证状态</option>
                      <option value="true">已验证</option>
                      <option value="false">未验证</option>
                    </select>
                  </div>
                  <div className="flex space-x-2">
                    <button
                      onClick={handleUserSearch}
                      className="btn-primary flex-1"
                    >
                      搜索
                    </button>
                    <button
                      onClick={handleResetUserSearch}
                      className="btn-secondary flex-1"
                    >
                      重置
                    </button>
                  </div>
                </div>
              </div>

              {/* 用户列表 */}
              {loadingUsers ? (
                <div className="text-center py-8">
                  <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                  <p className="mt-2 text-gray-600">加载中...</p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          用户信息
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          角色
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          状态
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          验证状态
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          创建时间
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          操作
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {users.map((user) => (
                        <tr key={user.id} className="hover:bg-gray-50">
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="flex items-center">
                              <div className="flex-shrink-0 h-10 w-10">
                                {user.avatar_url ? (
                                  <img className="h-10 w-10 rounded-full" src={user.avatar_url} alt="" />
                                ) : (
                                  <div className="h-10 w-10 rounded-full bg-gray-300 flex items-center justify-center">
                                    <i className="fas fa-user text-gray-600"></i>
                                  </div>
                                )}
                              </div>
                              <div className="ml-4">
                                <div className="text-sm font-medium text-gray-900">
                                  {user.username || '未设置用户名'}
                                </div>
                                <div className="text-sm text-gray-500">{user.email}</div>
                                {user.full_name && (
                                  <div className="text-sm text-gray-500">{user.full_name}</div>
                                )}
                              </div>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                              user.role === 'admin' ? 'bg-purple-100 text-purple-800' :
                              user.role === 'premium' ? 'bg-yellow-100 text-yellow-800' :
                              'bg-gray-100 text-gray-800'
                            }`}>
                              {getRoleDisplayName(user.role)}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            {getStatusBadge(user.is_active)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            {getVerifiedBadge(user.is_verified)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {new Date(user.created_at).toLocaleDateString('zh-CN')}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                            <button
                              onClick={() => handleEditUser(user)}
                              className="text-blue-600 hover:text-blue-900"
                            >
                              编辑
                            </button>
                            <button
                              onClick={() => handleToggleUserStatus(user)}
                              className={`${
                                user.is_active ? 'text-red-600 hover:text-red-900' : 'text-green-600 hover:text-green-900'
                              }`}
                            >
                              {user.is_active ? '禁用' : '启用'}
                            </button>
                            <button
                              onClick={() => handleDeleteUser(user)}
                              className="text-red-600 hover:text-red-900"
                            >
                              删除
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
              
              {/* 分页 */}
              {userTotal > userPageSize && (
                <div className="flex items-center justify-between">
                  <div className="text-sm text-gray-700">
                    显示第 {(userCurrentPage - 1) * userPageSize + 1} 到 {Math.min(userCurrentPage * userPageSize, userTotal)} 条，共 {userTotal} 条
                  </div>
                  <div className="flex space-x-2">
                    <button
                      onClick={() => setUserCurrentPage(Math.max(1, userCurrentPage - 1))}
                      disabled={userCurrentPage === 1}
                      className="px-3 py-1 text-sm bg-gray-200 text-gray-700 rounded hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      上一页
                    </button>
                    <span className="px-3 py-1 text-sm text-gray-700">
                      第 {userCurrentPage} 页，共 {Math.ceil(userTotal / userPageSize)} 页
                    </span>
                    <button
                      onClick={() => setUserCurrentPage(Math.min(Math.ceil(userTotal / userPageSize), userCurrentPage + 1))}
                      disabled={userCurrentPage >= Math.ceil(userTotal / userPageSize)}
                      className="px-3 py-1 text-sm bg-gray-200 text-gray-700 rounded hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      下一页
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* 创建用户表单模态框 */}
      {showUserCreateForm && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">新增用户</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">邮箱</label>
                  <input
                    type="email"
                    value={userFormData.email}
                    onChange={(e) => setUserFormData({ ...userFormData, email: e.target.value })}
                    className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                    placeholder="留空则自动生成临时邮箱"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">用户名</label>
                  <input
                    type="text"
                    value={userFormData.username}
                    onChange={(e) => setUserFormData({ ...userFormData, username: e.target.value })}
                    className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                    placeholder="可选"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">姓名</label>
                  <input
                    type="text"
                    value={userFormData.full_name}
                    onChange={(e) => setUserFormData({ ...userFormData, full_name: e.target.value })}
                    className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                    placeholder="可选"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">密码</label>
                  <input
                    type="password"
                    value={userFormData.password}
                    onChange={(e) => setUserFormData({ ...userFormData, password: e.target.value })}
                    className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                    placeholder="留空则自动生成随机密码"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">角色</label>
                  <select
                    value={userFormData.role}
                    onChange={(e) => setUserFormData({ ...userFormData, role: e.target.value })}
                    className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                  >
                    <option value="user">普通用户</option>
                    <option value="premium">VIP用户</option>
                    <option value="admin">管理员</option>
                  </select>
                </div>
                <div className="flex items-center space-x-4">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={userFormData.is_active}
                      onChange={(e) => setUserFormData({ ...userFormData, is_active: e.target.checked })}
                      className="rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50"
                    />
                    <span className="ml-2 text-sm text-gray-700">启用账户</span>
                  </label>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={userFormData.is_verified}
                      onChange={(e) => setUserFormData({ ...userFormData, is_verified: e.target.checked })}
                      className="rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50"
                    />
                    <span className="ml-2 text-sm text-gray-700">已验证</span>
                  </label>
                </div>
              </div>
              <div className="flex justify-end space-x-3 mt-6">
                <button
                  onClick={() => {
                    setShowUserCreateForm(false);
                    resetUserForm();
                  }}
                  className="px-4 py-2 bg-gray-300 text-gray-700 text-sm font-medium rounded-md hover:bg-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2"
                >
                  取消
                </button>
                <button
                  onClick={handleCreateUser}
                  className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                >
                  创建
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 编辑用户表单模态框 */}
      {showUserEditForm && editingUser && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">编辑用户</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">邮箱</label>
                  <input
                    type="email"
                    value={userFormData.email}
                    onChange={(e) => setUserFormData({ ...userFormData, email: e.target.value })}
                    className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">用户名</label>
                  <input
                    type="text"
                    value={userFormData.username}
                    onChange={(e) => setUserFormData({ ...userFormData, username: e.target.value })}
                    className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">姓名</label>
                  <input
                    type="text"
                    value={userFormData.full_name}
                    onChange={(e) => setUserFormData({ ...userFormData, full_name: e.target.value })}
                    className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">角色</label>
                  <select
                    value={userFormData.role}
                    onChange={(e) => setUserFormData({ ...userFormData, role: e.target.value })}
                    className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                  >
                    <option value="user">普通用户</option>
                    <option value="premium">VIP用户</option>
                    <option value="admin">管理员</option>
                  </select>
                </div>
                <div className="flex items-center space-x-4">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={userFormData.is_active}
                      onChange={(e) => setUserFormData({ ...userFormData, is_active: e.target.checked })}
                      className="rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50"
                    />
                    <span className="ml-2 text-sm text-gray-700">启用账户</span>
                  </label>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={userFormData.is_verified}
                      onChange={(e) => setUserFormData({ ...userFormData, is_verified: e.target.checked })}
                      className="rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50"
                    />
                    <span className="ml-2 text-sm text-gray-700">已验证</span>
                  </label>
                </div>
              </div>
              <div className="flex justify-end space-x-3 mt-6">
                <button
                  onClick={() => {
                    setShowUserEditForm(false);
                    setEditingUser(null);
                    resetUserForm();
                  }}
                  className="px-4 py-2 bg-gray-300 text-gray-700 text-sm font-medium rounded-md hover:bg-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2"
                >
                  取消
                </button>
                <button
                  onClick={handleUpdateUser}
                  className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                >
                  更新
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 创建标签组表单模态框 */}
      {showTagGroupCreateForm && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">新增标签组</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">标签组名称</label>
                  <input
                    type="text"
                    value={tagGroupFormData.name}
                    onChange={(e) => setTagGroupFormData({ ...tagGroupFormData, name: e.target.value })}
                    className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                    placeholder="请输入标签组名称"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">描述</label>
                  <textarea
                    value={tagGroupFormData.description}
                    onChange={(e) => setTagGroupFormData({ ...tagGroupFormData, description: e.target.value })}
                    rows={3}
                    className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                    placeholder="请输入标签组描述（可选）"
                  />
                </div>
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    checked={tagGroupFormData.is_active}
                    onChange={(e) => setTagGroupFormData({ ...tagGroupFormData, is_active: e.target.checked })}
                    className="rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50"
                  />
                  <span className="ml-2 text-sm text-gray-700">启用标签组</span>
                </div>
              </div>
              <div className="flex justify-end space-x-3 mt-6">
                <button
                  onClick={() => {
                    setShowTagGroupCreateForm(false);
                    resetTagGroupForm();
                  }}
                  className="px-4 py-2 bg-gray-300 text-gray-700 text-sm font-medium rounded-md hover:bg-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2"
                >
                  取消
                </button>
                <button
                  onClick={handleCreateTagGroup}
                  className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                >
                  创建
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 编辑标签组表单模态框 */}
      {showTagGroupEditForm && editingTagGroup && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">编辑标签组</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">标签组名称</label>
                  <input
                    type="text"
                    value={tagGroupFormData.name}
                    onChange={(e) => setTagGroupFormData({ ...tagGroupFormData, name: e.target.value })}
                    className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">描述</label>
                  <textarea
                    value={tagGroupFormData.description}
                    onChange={(e) => setTagGroupFormData({ ...tagGroupFormData, description: e.target.value })}
                    rows={3}
                    className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                  />
                </div>
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    checked={tagGroupFormData.is_active}
                    onChange={(e) => setTagGroupFormData({ ...tagGroupFormData, is_active: e.target.checked })}
                    className="rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50"
                  />
                  <span className="ml-2 text-sm text-gray-700">启用标签组</span>
                </div>
              </div>
              <div className="flex justify-end space-x-3 mt-6">
                <button
                  onClick={() => {
                    setShowTagGroupEditForm(false);
                    setEditingTagGroup(null);
                    resetTagGroupForm();
                  }}
                  className="px-4 py-2 bg-gray-300 text-gray-700 text-sm font-medium rounded-md hover:bg-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2"
                >
                  取消
                </button>
                <button
                  onClick={handleUpdateTagGroup}
                  className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                >
                  更新
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 创建标签表单模态框 */}
      {showTagCreateForm.groupId && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">添加标签</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">标签名称</label>
                  <input
                    type="text"
                    value={tagFormData.name}
                    onChange={(e) => setTagFormData({ ...tagFormData, name: e.target.value })}
                    className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                    placeholder="请输入标签名称"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">标签颜色</label>
                  <div className="grid grid-cols-5 gap-2">
                    {PRESET_TAG_COLORS.map((color) => (
                      <button
                        key={color.value}
                        type="button"
                        onClick={() => setTagFormData({ ...tagFormData, color: color.value })}
                        className={`w-8 h-8 rounded-full border-2 ${
                          tagFormData.color === color.value 
                            ? 'border-gray-800 ring-2 ring-gray-300' 
                            : 'border-gray-300 hover:border-gray-400'
                        }`}
                        style={{ backgroundColor: color.value }}
                        title={color.name}
                      />
                    ))}
                  </div>
                </div>
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    checked={tagFormData.is_active}
                    onChange={(e) => setTagFormData({ ...tagFormData, is_active: e.target.checked })}
                    className="rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50"
                  />
                  <span className="ml-2 text-sm text-gray-700">启用标签</span>
                </div>
              </div>
              <div className="flex justify-end space-x-3 mt-6">
                <button
                  onClick={() => {
                    setShowTagCreateForm({ groupId: null });
                    resetTagForm();
                  }}
                  className="px-4 py-2 bg-gray-300 text-gray-700 text-sm font-medium rounded-md hover:bg-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2"
                >
                  取消
                </button>
                <button
                  onClick={() => handleCreateTag(showTagCreateForm.groupId!)}
                  className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                >
                  创建
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 批量添加标签表单模态框 */}
      {showBatchTagForm.groupId && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">批量添加标签</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">标签名称</label>
                  <textarea
                    value={batchTagInput}
                    onChange={(e) => setBatchTagInput(e.target.value)}
                    rows={4}
                    className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                    placeholder="请输入标签名称，多个标签用逗号分隔\n例如：前端,后端,全栈,移动端"
                  />
                </div>
                <div className="text-sm text-gray-500">
                  <p>• 多个标签请用逗号分隔</p>
                  <p>• 重复的标签名称将被自动跳过</p>
                </div>
              </div>
              <div className="flex justify-end space-x-3 mt-6">
                <button
                  onClick={() => {
                    setShowBatchTagForm({ groupId: null });
                    setBatchTagInput('');
                  }}
                  className="px-4 py-2 bg-gray-300 text-gray-700 text-sm font-medium rounded-md hover:bg-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2"
                >
                  取消
                </button>
                <button
                  onClick={() => handleBatchCreateTags(showBatchTagForm.groupId!)}
                  className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                >
                  批量创建
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SystemConfigPage;