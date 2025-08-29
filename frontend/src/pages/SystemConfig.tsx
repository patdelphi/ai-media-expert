import React, { useState } from 'react';
import { SystemConfig } from '../types';

const SystemConfigPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState('basic');
  
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

  // AI API配置
  const [aiApis, setAiApis] = useState([
    { id: 1, provider: 'OpenAI', name: 'GPT-4', apiKey: 'sk-*****', baseUrl: 'https://api.openai.com/v1', enabled: true },
    { id: 2, provider: 'Anthropic', name: 'Claude-3', apiKey: 'sk-*****', baseUrl: 'https://api.anthropic.com', enabled: false },
    { id: 3, provider: 'Custom', name: '自定义API', apiKey: 'sk-*****', baseUrl: 'https://api.custom.com', enabled: true }
  ]);

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
  const [newApi, setNewApi] = useState({ provider: 'OpenAI', name: '', apiKey: '', baseUrl: '', enabled: true });
  const [newTemplate, setNewTemplate] = useState({ title: '', category: '内容分析', content: '' });
  const [newTagGroup, setNewTagGroup] = useState({ name: '', tags: [] });
  const [newUser, setNewUser] = useState({ username: '', email: '', password: '', role: '查看者' });
  const [editingTag, setEditingTag] = useState({ groupId: null as number | null, tag: '' });

  // 处理函数
  const handleAddApi = () => {
    if (!newApi.name || !newApi.apiKey) {
      alert('请填写完整的API信息');
      return;
    }
    setAiApis([...aiApis, { ...newApi, id: Date.now() }]);
    setNewApi({ provider: 'OpenAI', name: '', apiKey: '', baseUrl: '', enabled: true });
  };

  const handleDeleteApi = (id: number) => {
    if (confirm('确定要删除这个API配置吗？')) {
      setAiApis(aiApis.filter(api => api.id !== id));
    }
  };

  const handleToggleApi = (id: number) => {
    setAiApis(aiApis.map(api => 
      api.id === id ? { ...api, enabled: !api.enabled } : api
    ));
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

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-800">系统配置</h1>
        <div className="text-sm text-gray-500">
          管理系统设置、API配置和用户权限
        </div>
      </div>

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
              </button>
            ))}
          </nav>
        </div>

        <div className="p-6">
          {/* 基础设置 */}
          {activeTab === 'basic' && (
            <div className="space-y-6">
              <h2 className="text-lg font-medium text-gray-900">基础设置</h2>
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
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  <select
                    value={newApi.provider}
                    onChange={(e) => setNewApi({...newApi, provider: e.target.value})}
                    className="input-field"
                  >
                    <option value="OpenAI">OpenAI</option>
                    <option value="Anthropic">Anthropic</option>
                    <option value="Custom">自定义</option>
                  </select>
                  <input
                    type="text"
                    placeholder="API名称"
                    value={newApi.name}
                    onChange={(e) => setNewApi({...newApi, name: e.target.value})}
                    className="input-field"
                  />
                  <input
                    type="text"
                    placeholder="API Key"
                    value={newApi.apiKey}
                    onChange={(e) => setNewApi({...newApi, apiKey: e.target.value})}
                    className="input-field"
                  />
                  <button onClick={handleAddApi} className="btn-primary">
                    添加API
                  </button>
                </div>
                <div className="mt-4">
                  <input
                    type="text"
                    placeholder="Base URL (可选)"
                    value={newApi.baseUrl}
                    onChange={(e) => setNewApi({...newApi, baseUrl: e.target.value})}
                    className="input-field w-full"
                  />
                </div>
              </div>

              {/* API列表 */}
              <div className="space-y-4">
                {aiApis.map((api) => (
                  <div key={api.id} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <div className="flex items-center space-x-3">
                          <h3 className="text-md font-medium text-gray-800">{api.name}</h3>
                          <span className={`px-2 py-1 text-xs rounded-full ${
                            api.enabled ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                          }`}>
                            {api.enabled ? '已启用' : '已禁用'}
                          </span>
                        </div>
                        <p className="text-sm text-gray-600 mt-1">{api.provider}</p>
                        <p className="text-sm text-gray-500 mt-1">API Key: {api.apiKey}</p>
                        {api.baseUrl && (
                          <p className="text-sm text-gray-500">Base URL: {api.baseUrl}</p>
                        )}
                      </div>
                      <div className="flex space-x-2">
                        <button
                          onClick={() => handleToggleApi(api.id)}
                          className={`px-3 py-1 text-sm rounded ${
                            api.enabled
                              ? 'bg-yellow-100 text-yellow-800 hover:bg-yellow-200'
                              : 'bg-green-100 text-green-800 hover:bg-green-200'
                          }`}
                        >
                          {api.enabled ? '禁用' : '启用'}
                        </button>
                        <button
                          onClick={() => handleDeleteApi(api.id)}
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