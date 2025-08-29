import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { AIApiConfig, PromptTemplate, TagGroup, User } from '@/types';

const SystemSettings: React.FC = () => {
  const location = useLocation();
  const [activeTab, setActiveTab] = useState('basic');
  
  // 根据路径设置默认标签页
  useEffect(() => {
    if (location.pathname === '/users') {
      setActiveTab('users');
    }
  }, [location.pathname]);
  
  // AI API配置状态
  const [aiApis, setAiApis] = useState<AIApiConfig[]>([
    { id: '1', provider: 'OpenAI', apiKey: 'sk-*****', enabled: true, endpoint: 'https://api.openai.com/v1', model: 'gpt-3.5-turbo' },
    { id: '2', provider: 'Anthropic', apiKey: 'sk-*****', enabled: false, endpoint: 'https://api.anthropic.com/v1', model: 'claude-3' },
    { id: '3', provider: 'Custom', apiKey: 'sk-*****', enabled: true, endpoint: 'https://api.custom.com/v1', model: 'custom-model' }
  ]);
  
  // 提示词模板状态
  const [templates, setTemplates] = useState<PromptTemplate[]>([
    { id: '1', title: '默认提示词', content: '# 欢迎使用\n这是一个默认提示词模板' },
    { id: '2', title: '客服回复', content: '您好，请问有什么可以帮助您的？' }
  ]);
  
  // 标签组状态
  const [tagGroups, setTagGroups] = useState<TagGroup[]>([
    { id: '1', name: '常用标签', tags: ['重要', '紧急', '待处理'] },
    { id: '2', name: '项目分类', tags: ['前端', '后端', '设计'] }
  ]);
  

  
  // 新增表单状态
  const [newApi, setNewApi] = useState<Partial<AIApiConfig>>({ provider: 'OpenAI', apiKey: '', enabled: true, endpoint: '', model: '' });
  const [newTemplate, setNewTemplate] = useState<Partial<PromptTemplate>>({ title: '', content: '' });
  const [newTagGroup, setNewTagGroup] = useState<Partial<TagGroup>>({ name: '', tags: [] });

  const [editingTag, setEditingTag] = useState<{ groupId: string | null; tag: string }>({ groupId: null, tag: '' });
  
  // 选中的模板和标签组
  const [selectedTemplate, setSelectedTemplate] = useState<string>('1');
  const [selectedTagGroup, setSelectedTagGroup] = useState<string>('1');

  const handleAddApi = () => {
    if (!newApi.provider || !newApi.apiKey) return;
    setAiApis([...aiApis, { ...newApi, id: Date.now().toString() } as AIApiConfig]);
    setNewApi({ provider: 'OpenAI', apiKey: '', enabled: true, endpoint: '', model: '' });
  };

  const handleAddTemplate = () => {
    if (!newTemplate.title || !newTemplate.content) return;
    setTemplates([...templates, { ...newTemplate, id: Date.now().toString() } as PromptTemplate]);
    setNewTemplate({ title: '', content: '' });
  };

  const handleAddTagGroup = () => {
    if (!newTagGroup.name) return;
    setTagGroups([...tagGroups, { ...newTagGroup, id: Date.now().toString(), tags: [] } as TagGroup]);
    setNewTagGroup({ name: '', tags: [] });
  };



  const handleAddTag = (groupId: string) => {
    if (!editingTag.tag) return;
    const updatedGroups = tagGroups.map(group => {
      if (group.id === groupId) {
        return { ...group, tags: [...group.tags, editingTag.tag] };
      }
      return group;
    });
    setTagGroups(updatedGroups);
    setEditingTag({ groupId: null, tag: '' });
  };

  const handleRemoveTag = (groupId: string, tagIndex: number) => {
    const updatedGroups = tagGroups.map(group => {
      if (group.id === groupId) {
        return { ...group, tags: group.tags.filter((_, index) => index !== tagIndex) };
      }
      return group;
    });
    setTagGroups(updatedGroups);
  };

  const handleDeleteApi = (id: string) => {
    setAiApis(aiApis.filter(api => api.id !== id));
  };

  const handleDeleteTemplate = (id: string) => {
    setTemplates(templates.filter(template => template.id !== id));
  };

  const handleDeleteTagGroup = (id: string) => {
    setTagGroups(tagGroups.filter(group => group.id !== id));
  };

  const handleToggleApiStatus = (id: string) => {
    setAiApis(aiApis.map(api => 
      api.id === id ? { ...api, enabled: !api.enabled } : api
    ));
  };

  return (
    <div className="space-y-6">
      <div className="bg-white shadow-sm rounded-lg overflow-hidden">

        {/* Tabs */}
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8 px-6">
            {[
              { id: 'basic', label: '基础设置', icon: 'fa-cog' },
              { id: 'ai', label: 'AI API 配置', icon: 'fa-robot' },
              { id: 'template', label: '提示词模板', icon: 'fa-file-text' },
              { id: 'tags', label: '预设标签组', icon: 'fa-tags' }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm flex items-center ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <i className={`fas ${tab.icon} mr-2`}></i>
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        {/* Content */}
        <div className="p-6">
          {/* Basic Settings */}
          {activeTab === 'basic' && (
            <div>
              <h2 className="text-lg font-medium text-gray-900 mb-6">基础设置</h2>
              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">系统名称</label>
                  <input
                    type="text"
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                    placeholder="请输入系统名称"
                    defaultValue="AI Media Expert"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">系统语言</label>
                  <select className="mt-1 block w-full rounded-md border-gray-300 py-2 pl-3 pr-10 text-base focus:border-blue-500 focus:outline-none focus:ring-blue-500 sm:text-sm">
                    <option>简体中文</option>
                    <option>English</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">时区设置</label>
                  <select className="mt-1 block w-full rounded-md border-gray-300 py-2 pl-3 pr-10 text-base focus:border-blue-500 focus:outline-none focus:ring-blue-500 sm:text-sm">
                    <option>UTC+8 (中国标准时间)</option>
                    <option>UTC+0 (格林尼治标准时间)</option>
                  </select>
                </div>
                <div className="flex items-center">
                  <input
                    id="auto-update"
                    name="auto-update"
                    type="checkbox"
                    className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <label htmlFor="auto-update" className="ml-2 block text-sm text-gray-700">
                    启用自动更新
                  </label>
                </div>
                <div className="pt-5">
                  <button
                    type="button"
                    className="rounded-button inline-flex justify-center rounded-md border border-transparent bg-blue-600 py-2 px-4 text-sm font-medium text-white shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                  >
                    保存设置
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* AI API Settings */}
          {activeTab === 'ai' && (
            <div>
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-lg font-medium text-gray-900">AI API 配置</h2>
                <button
                  type="button"
                  className="rounded-button inline-flex items-center rounded-md border border-transparent bg-blue-600 px-3 py-2 text-sm font-medium leading-4 text-white shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                >
                  <i className="fas fa-plus mr-1"></i> 新增 API
                </button>
              </div>
              
              {/* Add New API Form */}
              <div className="bg-gray-50 p-4 rounded-lg mb-6">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">服务商名称</label>
                    <input
                      type="text"
                      value={newApi.provider || ''}
                      onChange={(e) => setNewApi({ ...newApi, provider: e.target.value })}
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                      placeholder="输入服务商名称"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">API 调用地址</label>
                    <input
                      type="text"
                      value={newApi.endpoint || ''}
                      onChange={(e) => setNewApi({ ...newApi, endpoint: e.target.value })}
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                      placeholder="输入 API 调用地址"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">模型名称</label>
                    <input
                      type="text"
                      value={newApi.model || ''}
                      onChange={(e) => setNewApi({ ...newApi, model: e.target.value })}
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                      placeholder="输入模型名称"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">API Key</label>
                    <input
                      type="password"
                      value={newApi.apiKey || ''}
                      onChange={(e) => setNewApi({ ...newApi, apiKey: e.target.value })}
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                      placeholder="输入 API Key"
                    />
                  </div>
                </div>
                <div className="mt-4 flex items-center justify-between">
                  <div className="flex items-center">
                    <input
                      id="enable-api"
                      type="checkbox"
                      checked={newApi.enabled || false}
                      onChange={(e) => setNewApi({ ...newApi, enabled: e.target.checked })}
                      className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <label htmlFor="enable-api" className="ml-2 block text-sm text-gray-700">
                      启用
                    </label>
                  </div>
                  <button
                    type="button"
                    onClick={handleAddApi}
                    className="rounded-button inline-flex justify-center rounded-md border border-transparent bg-blue-600 py-2 px-4 text-sm font-medium text-white shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                  >
                    添加 API
                  </button>
                </div>
              </div>
              
              {/* API List */}
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">服务商</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">API 调用地址</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">模型名称</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">API Key</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">状态</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">操作</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {aiApis.map((api) => (
                      <tr key={api.id}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{api.provider}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{api.endpoint}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{api.model}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{api.apiKey}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          <button
                            onClick={() => handleToggleApiStatus(api.id)}
                            className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                              api.enabled ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                            }`}
                          >
                            {api.enabled ? '已启用' : '已禁用'}
                          </button>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          <button className="text-blue-600 hover:text-blue-900 mr-3">
                            <i className="fas fa-edit"></i>
                          </button>
                          <button 
                            onClick={() => handleDeleteApi(api.id)}
                            className="text-red-600 hover:text-red-900"
                          >
                            <i className="fas fa-trash"></i>
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Template Settings */}
          {activeTab === 'template' && (
            <div>
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-lg font-medium text-gray-900">提示词模板配置</h2>
                <button
                  type="button"
                  className="rounded-button inline-flex items-center rounded-md border border-transparent bg-blue-600 px-3 py-2 text-sm font-medium leading-4 text-white shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                >
                  <i className="fas fa-plus mr-1"></i> 新增模板
                </button>
              </div>
              <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
                {/* Template List */}
                <div className="lg:col-span-1">
                  <div className="border border-gray-200 rounded-lg overflow-hidden">
                    <div className="bg-gray-50 px-4 py-3 border-b border-gray-200">
                      <h3 className="text-sm font-medium text-gray-700">模板列表</h3>
                    </div>
                    <div className="divide-y divide-gray-200">
                      {templates.map((template) => (
                        <div
                          key={template.id}
                          className={`px-4 py-3 hover:bg-gray-50 cursor-pointer ${
                            selectedTemplate === template.id ? 'bg-blue-50' : ''
                          }`}
                          onClick={() => setSelectedTemplate(template.id)}
                        >
                          <div className="flex justify-between items-center">
                            <span className="text-sm font-medium text-gray-700">{template.title}</span>
                            <div>
                              <button className="text-blue-600 hover:text-blue-900 mr-2">
                                <i className="fas fa-edit"></i>
                              </button>
                              <button 
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleDeleteTemplate(template.id);
                                }}
                                className="text-red-600 hover:text-red-900"
                              >
                                <i className="fas fa-trash"></i>
                              </button>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
                
                {/* Template Editor */}
                <div className="lg:col-span-3">
                  <div className="border border-gray-200 rounded-lg overflow-hidden">
                    <div className="bg-gray-50 px-4 py-3 border-b border-gray-200">
                      <h3 className="text-sm font-medium text-gray-700">模板编辑器</h3>
                    </div>
                    <div className="p-4">
                      <div className="mb-4">
                        <label className="block text-sm font-medium text-gray-700 mb-1">模板标题</label>
                        <input
                          type="text"
                          value={newTemplate.title || ''}
                          onChange={(e) => setNewTemplate({ ...newTemplate, title: e.target.value })}
                          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                          placeholder="输入模板标题"
                        />
                      </div>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Markdown 编辑</label>
                          <textarea
                            rows={10}
                            value={newTemplate.content || ''}
                            onChange={(e) => setNewTemplate({ ...newTemplate, content: e.target.value })}
                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                            placeholder="输入 Markdown 内容"
                          ></textarea>
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">预览效果</label>
                          <div className="mt-1 block w-full rounded-md border border-gray-300 p-3 h-64 bg-gray-50 overflow-y-auto">
                            <div className="prose prose-sm max-w-none whitespace-pre-wrap">
                              {newTemplate.content || '预览内容将在这里显示'}
                            </div>
                          </div>
                        </div>
                      </div>
                      <div className="mt-4 flex justify-end">
                        <button
                          type="button"
                          onClick={handleAddTemplate}
                          className="rounded-button inline-flex justify-center rounded-md border border-transparent bg-blue-600 py-2 px-4 text-sm font-medium text-white shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                        >
                          保存模板
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Tag Settings */}
          {activeTab === 'tags' && (
            <div>
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-lg font-medium text-gray-900">预设标签组</h2>
                <button
                  type="button"
                  onClick={handleAddTagGroup}
                  className="rounded-button inline-flex items-center rounded-md border border-transparent bg-blue-600 px-3 py-2 text-sm font-medium leading-4 text-white shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                >
                  <i className="fas fa-plus mr-1"></i> 新增标签组
                </button>
              </div>
              <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
                {/* Tag Group List */}
                <div className="lg:col-span-1">
                  <div className="border border-gray-200 rounded-lg overflow-hidden mb-4">
                    <div className="bg-gray-50 px-4 py-3 border-b border-gray-200">
                      <h3 className="text-sm font-medium text-gray-700">标签组列表</h3>
                    </div>
                    <div className="divide-y divide-gray-200">
                      {tagGroups.map((group) => (
                        <div
                          key={group.id}
                          className={`px-4 py-3 hover:bg-gray-50 cursor-pointer ${
                            selectedTagGroup === group.id ? 'bg-blue-50' : ''
                          }`}
                          onClick={() => setSelectedTagGroup(group.id)}
                        >
                          <div className="flex justify-between items-center">
                            <span className="text-sm font-medium text-gray-700">{group.name}</span>
                            <div>
                              <button className="text-blue-600 hover:text-blue-900 mr-2">
                                <i className="fas fa-edit"></i>
                              </button>
                              <button 
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleDeleteTagGroup(group.id);
                                }}
                                className="text-red-600 hover:text-red-900"
                              >
                                <i className="fas fa-trash"></i>
                              </button>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                  
                  {/* Add New Tag Group */}
                  <div className="border border-gray-200 rounded-lg overflow-hidden">
                    <div className="bg-gray-50 px-4 py-3 border-b border-gray-200">
                      <h3 className="text-sm font-medium text-gray-700">新增标签组</h3>
                    </div>
                    <div className="p-4">
                      <input
                        type="text"
                        value={newTagGroup.name || ''}
                        onChange={(e) => setNewTagGroup({ ...newTagGroup, name: e.target.value })}
                        className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                        placeholder="输入标签组名称"
                      />
                      <button
                        onClick={handleAddTagGroup}
                        className="mt-2 w-full rounded-button bg-blue-600 text-white py-2 text-sm hover:bg-blue-700"
                      >
                        添加标签组
                      </button>
                    </div>
                  </div>
                </div>
                
                {/* Tag Management */}
                <div className="lg:col-span-3">
                  <div className="border border-gray-200 rounded-lg overflow-hidden">
                    <div className="bg-gray-50 px-4 py-3 border-b border-gray-200">
                      <h3 className="text-sm font-medium text-gray-700">标签管理</h3>
                    </div>
                    <div className="p-4">
                      {selectedTagGroup && (
                        <>
                          <div className="mb-4">
                            <label className="block text-sm font-medium text-gray-700 mb-1">组名</label>
                            <input
                              type="text"
                              value={tagGroups.find(g => g.id === selectedTagGroup)?.name || ''}
                              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                              placeholder="输入组名"
                              readOnly
                            />
                          </div>
                          <div className="mb-4">
                            <label className="block text-sm font-medium text-gray-700 mb-1">标签列表</label>
                            <div className="mt-2 flex flex-wrap gap-2">
                              {tagGroups.find(g => g.id === selectedTagGroup)?.tags.map((tag, index) => (
                                <span key={index} className="inline-flex items-center rounded-full bg-blue-100 px-3 py-1 text-sm font-medium text-blue-700">
                                  {tag}
                                  <button 
                                    type="button" 
                                    onClick={() => handleRemoveTag(selectedTagGroup, index)}
                                    className="ml-1 text-blue-500 hover:text-blue-700"
                                  >
                                    <i className="fas fa-times"></i>
                                  </button>
                                </span>
                              ))}
                            </div>
                          </div>
                          <div className="flex items-center">
                            <input
                              type="text"
                              value={editingTag.tag}
                              onChange={(e) => setEditingTag({ ...editingTag, tag: e.target.value })}
                              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                              placeholder="输入新标签"
                            />
                            <button
                              type="button"
                              onClick={() => handleAddTag(selectedTagGroup)}
                              className="rounded-button ml-2 inline-flex justify-center rounded-md border border-transparent bg-blue-600 py-2 px-3 text-sm font-medium text-white shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                            >
                              添加
                            </button>
                          </div>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}


        </div>
      </div>
    </div>
  );
};

export default SystemSettings;