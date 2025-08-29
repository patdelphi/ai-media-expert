import React, { useState, useEffect } from 'react';
import { toast } from 'react-hot-toast';
import userManagementService, {
  UserListItem,
  UserSearchParams,
  AdminUserCreateRequest,
  AdminUserUpdateRequest
} from '../services/userManagement';

interface UserFormData {
  email: string;
  username: string;
  full_name: string;
  password: string;
  role: string;
  is_active: boolean;
  is_verified: boolean;
}

const UserManagement: React.FC = () => {
  const [users, setUsers] = useState<UserListItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [total, setTotal] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize] = useState(20);
  const [searchParams, setSearchParams] = useState<UserSearchParams>({});
  
  // 表单相关状态
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showEditForm, setShowEditForm] = useState(false);
  const [editingUser, setEditingUser] = useState<UserListItem | null>(null);
  const [formData, setFormData] = useState<UserFormData>({
    email: '',
    username: '',
    full_name: '',
    password: '',
    role: 'user',
    is_active: true,
    is_verified: false
  });

  // 搜索表单状态
  const [searchForm, setSearchForm] = useState({
    search: '',
    role: '',
    is_active: '',
    is_verified: ''
  });

  // 加载用户列表
  const loadUsers = async (params: UserSearchParams = {}) => {
    setLoading(true);
    try {
      const response = await userManagementService.getUsersList({
        page: currentPage,
        size: pageSize,
        ...params
      });
      
      if (response.code === 200 && response.data) {
        setUsers(response.data.items);
        setTotal(response.data.total);
      } else {
        toast.error('获取用户列表失败');
      }
    } catch (error) {
      console.error('Load users error:', error);
      toast.error('获取用户列表失败');
    } finally {
      setLoading(false);
    }
  };

  // 初始加载
  useEffect(() => {
    loadUsers(searchParams);
  }, [currentPage, searchParams]);

  // 搜索处理
  const handleSearch = () => {
    const params: UserSearchParams = {};
    if (searchForm.search) params.search = searchForm.search;
    if (searchForm.role) params.role = searchForm.role;
    if (searchForm.is_active !== '') params.is_active = searchForm.is_active === 'true';
    if (searchForm.is_verified !== '') params.is_verified = searchForm.is_verified === 'true';
    
    setSearchParams(params);
    setCurrentPage(1);
  };

  // 重置搜索
  const handleResetSearch = () => {
    setSearchForm({
      search: '',
      role: '',
      is_active: '',
      is_verified: ''
    });
    setSearchParams({});
    setCurrentPage(1);
  };

  // 创建用户
  const handleCreateUser = async () => {
    try {
      const createData: AdminUserCreateRequest = {
        email: formData.email || undefined,
        username: formData.username || undefined,
        full_name: formData.full_name || undefined,
        password: formData.password || undefined,
        role: formData.role,
        is_active: formData.is_active,
        is_verified: formData.is_verified
      };
      
      const response = await userManagementService.createUser(createData);
      
      if (response.code === 200) {
        toast.success('用户创建成功');
        setShowCreateForm(false);
        resetForm();
        loadUsers(searchParams);
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
    setFormData({
      email: user.email,
      username: user.username || '',
      full_name: user.full_name || '',
      password: '',
      role: user.role,
      is_active: user.is_active,
      is_verified: user.is_verified
    });
    setShowEditForm(true);
  };

  // 更新用户
  const handleUpdateUser = async () => {
    if (!editingUser) return;
    
    try {
      const updateData: AdminUserUpdateRequest = {
        email: formData.email || undefined,
        username: formData.username || undefined,
        full_name: formData.full_name || undefined,
        role: formData.role,
        is_active: formData.is_active,
        is_verified: formData.is_verified
      };
      
      const response = await userManagementService.updateUser(editingUser.id, updateData);
      
      if (response.code === 200) {
        toast.success('用户更新成功');
        setShowEditForm(false);
        setEditingUser(null);
        resetForm();
        loadUsers(searchParams);
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
        loadUsers(searchParams);
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
        loadUsers(searchParams);
      } else {
        toast.error(response.message || '删除用户失败');
      }
    } catch (error) {
      console.error('Delete user error:', error);
      toast.error('删除用户失败');
    }
  };

  // 重置表单
  const resetForm = () => {
    setFormData({
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

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div className="bg-white shadow-sm rounded-lg p-6">
        <h1 className="text-2xl font-bold text-gray-900">用户管理</h1>
        <p className="mt-2 text-gray-600">管理系统中的所有用户账户</p>
      </div>

      {/* 搜索和操作区 */}
      <div className="bg-white shadow-sm rounded-lg p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">搜索</label>
            <input
              type="text"
              value={searchForm.search}
              onChange={(e) => setSearchForm({ ...searchForm, search: e.target.value })}
              className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
              placeholder="用户名、邮箱或姓名"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">角色</label>
            <select
              value={searchForm.role}
              onChange={(e) => setSearchForm({ ...searchForm, role: e.target.value })}
              className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
            >
              <option value="">全部角色</option>
              <option value="user">普通用户</option>
              <option value="premium">VIP用户</option>
              <option value="admin">管理员</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">状态</label>
            <select
              value={searchForm.is_active}
              onChange={(e) => setSearchForm({ ...searchForm, is_active: e.target.value })}
              className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
            >
              <option value="">全部状态</option>
              <option value="true">正常</option>
              <option value="false">禁用</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">验证状态</label>
            <select
              value={searchForm.is_verified}
              onChange={(e) => setSearchForm({ ...searchForm, is_verified: e.target.value })}
              className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
            >
              <option value="">全部</option>
              <option value="true">已验证</option>
              <option value="false">未验证</option>
            </select>
          </div>
          <div className="flex items-end space-x-2">
            <button
              onClick={handleSearch}
              className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
            >
              搜索
            </button>
            <button
              onClick={handleResetSearch}
              className="px-4 py-2 bg-gray-600 text-white text-sm font-medium rounded-md hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2"
            >
              重置
            </button>
          </div>
        </div>
        
        <div className="flex justify-end">
          <button
            onClick={() => setShowCreateForm(true)}
            className="inline-flex items-center px-4 py-2 bg-green-600 text-white text-sm font-medium rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2"
          >
            <i className="fas fa-plus mr-2"></i>
            新增用户
          </button>
        </div>
      </div>

      {/* 用户列表 */}
      <div className="bg-white shadow-sm rounded-lg overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">
            用户列表 ({total} 个用户)
          </h3>
        </div>
        
        {loading ? (
          <div className="p-6 text-center">
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
        {total > pageSize && (
          <div className="px-6 py-4 border-t border-gray-200 flex items-center justify-between">
            <div className="text-sm text-gray-700">
              显示第 {(currentPage - 1) * pageSize + 1} 到 {Math.min(currentPage * pageSize, total)} 条，共 {total} 条
            </div>
            <div className="flex space-x-2">
              <button
                onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                disabled={currentPage === 1}
                className="px-3 py-1 text-sm bg-gray-200 text-gray-700 rounded hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                上一页
              </button>
              <span className="px-3 py-1 text-sm text-gray-700">
                第 {currentPage} 页，共 {Math.ceil(total / pageSize)} 页
              </span>
              <button
                onClick={() => setCurrentPage(Math.min(Math.ceil(total / pageSize), currentPage + 1))}
                disabled={currentPage >= Math.ceil(total / pageSize)}
                className="px-3 py-1 text-sm bg-gray-200 text-gray-700 rounded hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                下一页
              </button>
            </div>
          </div>
        )}
      </div>

      {/* 创建用户表单模态框 */}
      {showCreateForm && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">新增用户</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">邮箱</label>
                  <input
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                    placeholder="留空则自动生成临时邮箱"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">用户名</label>
                  <input
                    type="text"
                    value={formData.username}
                    onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                    className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                    placeholder="可选"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">姓名</label>
                  <input
                    type="text"
                    value={formData.full_name}
                    onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                    className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                    placeholder="可选"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">密码</label>
                  <input
                    type="password"
                    value={formData.password}
                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                    className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                    placeholder="留空则自动生成随机密码"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">角色</label>
                  <select
                    value={formData.role}
                    onChange={(e) => setFormData({ ...formData, role: e.target.value })}
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
                      checked={formData.is_active}
                      onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                      className="rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50"
                    />
                    <span className="ml-2 text-sm text-gray-700">启用账户</span>
                  </label>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={formData.is_verified}
                      onChange={(e) => setFormData({ ...formData, is_verified: e.target.checked })}
                      className="rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50"
                    />
                    <span className="ml-2 text-sm text-gray-700">已验证</span>
                  </label>
                </div>
              </div>
              <div className="flex justify-end space-x-3 mt-6">
                <button
                  onClick={() => {
                    setShowCreateForm(false);
                    resetForm();
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
      {showEditForm && editingUser && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">编辑用户</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">邮箱</label>
                  <input
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">用户名</label>
                  <input
                    type="text"
                    value={formData.username}
                    onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                    className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">姓名</label>
                  <input
                    type="text"
                    value={formData.full_name}
                    onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                    className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">角色</label>
                  <select
                    value={formData.role}
                    onChange={(e) => setFormData({ ...formData, role: e.target.value })}
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
                      checked={formData.is_active}
                      onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                      className="rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50"
                    />
                    <span className="ml-2 text-sm text-gray-700">启用账户</span>
                  </label>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={formData.is_verified}
                      onChange={(e) => setFormData({ ...formData, is_verified: e.target.checked })}
                      className="rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50"
                    />
                    <span className="ml-2 text-sm text-gray-700">已验证</span>
                  </label>
                </div>
              </div>
              <div className="flex justify-end space-x-3 mt-6">
                <button
                  onClick={() => {
                    setShowEditForm(false);
                    setEditingUser(null);
                    resetForm();
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
    </div>
  );
};

export default UserManagement;