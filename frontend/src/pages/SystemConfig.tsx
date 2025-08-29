import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { systemConfigService, SystemConfig, ConfigCategory } from '../services/systemConfig';
import { aiConfigService, AIConfig, CreateAIConfigRequest } from '../services/aiConfig';
import { SystemConfig as SystemConfigType } from '../types';

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
  const [templates, setTemplates] = useState([
    { 
      id: 1, 
      title: '视频内容分析模板', 
      category: '内容分析',
      content: '请分析这段视频的主要内容，包括：\n1. 核心主题\n2. 关键信息点\n3. 目标受众\n4. 内容质量评估' 
    },
    { 
      id: 2, 
      title: '技术评测模板', 
      category: '技术分析',
      content: '请从技术角度分析这段视频：\n1. 技术要点\n2. 实现难度\n3. 适用场景\n4. 最佳实践建议' 
    }
  ]);

  // 标签组
  const [tagGroups, setTagGroups] = useState([
    { id: 1, name: '内容类型', tags: ['教程', '演示', '评测', '讲解', '实战'] },
    { id: 2, name: '技术栈', tags: ['React', 'Vue', 'Angular', 'Node.js', 'Python'] },
    { id: 3, name: '难度等级', tags: ['初级', '中级', '高级', '专家级'] }
  ]);

  // 用户管理
  const [users, setUsers] = useState([
    { id: 1, username: 'admin', email: 'admin@example.com', role: '管理员', active: true, lastLogin: '2024-01-15 10:30:00' },
    { id: 2, username: 'editor', email: 'editor@example.com', role: '编辑', active: true, lastLogin: '2024-01-14 16:45:00' },
    { id: 3, username: 'viewer', email: 'viewer@example.com', role: '查看者', active: false, lastLogin: '2024-01-10 09:15:00' }
  ]);

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
  const [newTemplate, setNewTemplate] = useState({ title: '', category: '内容分析', content: '' });
  const [newTagGroup, setNewTagGroup] = useState({ name: '', tags: [] });
  const [newUser, setNewUser] = useState({ username: '', email: '', password: '', role: '查看者' });
  const [editingTag, setEditingTag] = useState({ groupId: null as number | null, tag: '' });

  // 加载系统配置数据
  useEffect(() => {
    loadConfigs();
    loadCategories();
    loadAiConfigs();
  }, []);

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
      const response = await aiConfigService.getFullConfigs();
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
    
    const errors = validateApiForm({
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

  const handleAddTemplate = () => {
    if (!newTemplate.title || !newTemplate.content) {
      alert('请填写完整的模板信息');
      return;
    }
    setTemplates([...templates, { ...newTemplate, id: Date.now() }]);
    setNewTemplate({ title: '', category: '内容分析', content: '' });
  };

  const handleDeleteTemplate = (id: number) => {
    if (confirm('确定要删除这个模板吗？')) {
      setTemplates(templates.filter(template => template.id !== id));
    }
  };

  const handleAddTagGroup = () => {
    if (!newTagGroup.name) {
      alert('请输入标签组名称');
      return;
    }
    setTagGroups([...tagGroups, { ...newTagGroup, id: Date.now() }]);
    setNewTagGroup({ name: '', tags: [] });
  };

  const handleDeleteTagGroup = (id: number) => {
    if (confirm('确定要删除这个标签组吗？')) {
      setTagGroups(tagGroups.filter(group => group.id !== id));
    }
  };

  const handleAddTag = (groupId: number) => {
    if (!editingTag.tag.trim()) return;
    
    const updatedGroups = tagGroups.map(group => {
      if (group.id === groupId) {
        return { ...group, tags: [...group.tags, editingTag.tag.trim()] };
      }
      return group;
    });
    setTagGroups(updatedGroups);
    setEditingTag({ groupId: null, tag: '' });
  };

  const handleRemoveTag = (groupId: number, tagToRemove: string) => {
    const updatedGroups = tagGroups.map(group => {
      if (group.id === groupId) {
        return { ...group, tags: group.tags.filter(tag => tag !== tagToRemove) };
      }
      return group;
    });
    setTagGroups(updatedGroups);
  };

  const handleAddUser = () => {
    if (!newUser.username || !newUser.email || !newUser.password) {
      alert('请填写完整的用户信息');
      return;
    }
    setUsers([...users, { ...newUser, id: Date.now(), active: true, lastLogin: '' }]);
    setNewUser({ username: '', email: '', password: '', role: '查看者' });
  };

  const handleToggleUser = (id: number) => {
    setUsers(users.map(user => 
      user.id === id ? { ...user, active: !user.active } : user
    ));
  };

  const handleDeleteUser = (id: number) => {
    if (confirm('确定要删除这个用户吗？')) {
      setUsers(users.filter(user => user.id !== id));
    }
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
                          <h3 className="text-md font-medium text-gray-800">{config.key}</h3>
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
                <h3 className="text-md font-medium text-gray-800 mb-4">添加新API</h3>
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
                    添加API
                  </button>
                </div>
              </div>

              {/* API列表 */}
              <div className="space-y-4">
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
                            <h3 className="text-md font-medium text-gray-800">{config.name}</h3>
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
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <input
                      type="text"
                      placeholder="模板标题"
                      value={newTemplate.title}
                      onChange={(e) => setNewTemplate({...newTemplate, title: e.target.value})}
                      className="input-field"
                    />
                    <select
                      value={newTemplate.category}
                      onChange={(e) => setNewTemplate({...newTemplate, category: e.target.value})}
                      className="input-field"
                    >
                      <option value="内容分析">内容分析</option>
                      <option value="技术分析">技术分析</option>
                      <option value="营销分析">营销分析</option>
                      <option value="教育分析">教育分析</option>
                    </select>
                  </div>
                  <textarea
                    placeholder="模板内容"
                    value={newTemplate.content}
                    onChange={(e) => setNewTemplate({...newTemplate, content: e.target.value})}
                    rows={4}
                    className="input-field w-full"
                  />
                  <button onClick={handleAddTemplate} className="btn-primary">
                    添加模板
                  </button>
                </div>
              </div>

              {/* 模板列表 */}
              <div className="space-y-4">
                {templates.map((template) => (
                  <div key={template.id} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <div className="flex items-center space-x-3">
                          <h3 className="text-md font-medium text-gray-800">{template.title}</h3>
                          <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                            {template.category}
                          </span>
                        </div>
                        <p className="text-sm text-gray-600 mt-2 whitespace-pre-wrap">{template.content}</p>
                      </div>
                      <div className="flex space-x-2">
                        <button className="px-3 py-1 text-sm bg-blue-100 text-blue-800 rounded hover:bg-blue-200">
                          编辑
                        </button>
                        <button
                          onClick={() => handleDeleteTemplate(template.id)}
                          className="px-3 py-1 text-sm bg-red-100 text-red-800 rounded hover:bg-red-200"
                        >
                          删除
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 预设标签组 */}
          {activeTab === 'tags' && (
            <div className="space-y-6">
              <div className="flex justify-between items-center">
                <h2 className="text-lg font-medium text-gray-900">预设标签组</h2>
              </div>
              
              {/* 添加新标签组 */}
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="text-md font-medium text-gray-800 mb-4">添加新标签组</h3>
                <div className="flex space-x-4">
                  <input
                    type="text"
                    placeholder="标签组名称"
                    value={newTagGroup.name}
                    onChange={(e) => setNewTagGroup({...newTagGroup, name: e.target.value})}
                    className="input-field flex-1"
                  />
                  <button onClick={handleAddTagGroup} className="btn-primary">
                    添加标签组
                  </button>
                </div>
              </div>

              {/* 标签组列表 */}
              <div className="space-y-4">
                {tagGroups.map((group) => (
                  <div key={group.id} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex justify-between items-start mb-4">
                      <h3 className="text-md font-medium text-gray-800">{group.name}</h3>
                      <button
                        onClick={() => handleDeleteTagGroup(group.id)}
                        className="px-3 py-1 text-sm bg-red-100 text-red-800 rounded hover:bg-red-200"
                      >
                        删除组
                      </button>
                    </div>
                    
                    {/* 标签列表 */}
                    <div className="flex flex-wrap gap-2 mb-4">
                      {group.tags.map((tag, index) => (
                        <span key={index} className="px-2 py-1 bg-blue-100 text-blue-800 text-sm rounded flex items-center">
                          {tag}
                          <button
                            onClick={() => handleRemoveTag(group.id, tag)}
                            className="ml-2 text-blue-600 hover:text-blue-800"
                          >
                            <i className="fas fa-times text-xs"></i>
                          </button>
                        </span>
                      ))}
                    </div>
                    
                    {/* 添加标签 */}
                    <div className="flex space-x-2">
                      <input
                        type="text"
                        placeholder="添加新标签"
                        value={editingTag.groupId === group.id ? editingTag.tag : ''}
                        onChange={(e) => setEditingTag({groupId: group.id, tag: e.target.value})}
                        onKeyPress={(e) => e.key === 'Enter' && handleAddTag(group.id)}
                        className="input-field flex-1"
                      />
                      <button
                        onClick={() => handleAddTag(group.id)}
                        className="btn-secondary"
                      >
                        添加
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 用户管理 */}
          {activeTab === 'users' && (
            <div className="space-y-6">
              <div className="flex justify-between items-center">
                <h2 className="text-lg font-medium text-gray-900">用户管理</h2>
              </div>
              
              {/* 添加新用户 */}
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="text-md font-medium text-gray-800 mb-4">添加新用户</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  <input
                    type="text"
                    placeholder="用户名"
                    value={newUser.username}
                    onChange={(e) => setNewUser({...newUser, username: e.target.value})}
                    className="input-field"
                  />
                  <input
                    type="email"
                    placeholder="邮箱"
                    value={newUser.email}
                    onChange={(e) => setNewUser({...newUser, email: e.target.value})}
                    className="input-field"
                  />
                  <input
                    type="password"
                    placeholder="密码"
                    value={newUser.password}
                    onChange={(e) => setNewUser({...newUser, password: e.target.value})}
                    className="input-field"
                  />
                  <select
                    value={newUser.role}
                    onChange={(e) => setNewUser({...newUser, role: e.target.value})}
                    className="input-field"
                  >
                    <option value="查看者">查看者</option>
                    <option value="编辑">编辑</option>
                    <option value="管理员">管理员</option>
                  </select>
                </div>
                <div className="mt-4">
                  <button onClick={handleAddUser} className="btn-primary">
                    添加用户
                  </button>
                </div>
              </div>

              {/* 用户列表 */}
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        用户名
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        邮箱
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        角色
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        状态
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        最后登录
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        操作
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {users.map((user) => (
                      <tr key={user.id}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {user.username}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {user.email}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          <span className={`px-2 py-1 text-xs rounded-full ${
                            user.role === '管理员' ? 'bg-red-100 text-red-800' :
                            user.role === '编辑' ? 'bg-blue-100 text-blue-800' :
                            'bg-gray-100 text-gray-800'
                          }`}>
                            {user.role}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          <span className={`px-2 py-1 text-xs rounded-full ${
                            user.active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                          }`}>
                            {user.active ? '活跃' : '禁用'}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {user.lastLogin || '从未登录'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                          <div className="flex space-x-2">
                            <button
                              onClick={() => handleToggleUser(user.id)}
                              className={`px-3 py-1 text-xs rounded ${
                                user.active
                                  ? 'bg-yellow-100 text-yellow-800 hover:bg-yellow-200'
                                  : 'bg-green-100 text-green-800 hover:bg-green-200'
                              }`}
                            >
                              {user.active ? '禁用' : '启用'}
                            </button>
                            <button
                              onClick={() => handleDeleteUser(user.id)}
                              className="px-3 py-1 text-xs bg-red-100 text-red-800 rounded hover:bg-red-200"
                            >
                              删除
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SystemConfigPage;