import React, { useState } from 'react';
import { User } from '@/types';

const UserManagement: React.FC = () => {
  // 用户状态
  const [users, setUsers] = useState<User[]>([
    { id: 1, username: 'admin', email: 'admin@example.com', role: '管理员', active: true },
    { id: 2, username: 'user1', email: 'user1@example.com', role: '编辑', active: true },
    { id: 3, username: 'user2', email: 'user2@example.com', role: '查看者', active: false }
  ]);
  
  // 新增表单状态
  const [newUser, setNewUser] = useState<Partial<User & { password: string }>>({
    username: '', email: '', password: '', role: '编辑'
  });
  
  const [showAddForm, setShowAddForm] = useState(false);

  const handleAddUser = () => {
    if (!newUser.username || !newUser.email || !newUser.password) return;
    setUsers([...users, { ...newUser, id: Date.now(), active: true } as User]);
    setNewUser({ username: '', email: '', password: '', role: '编辑' });
    setShowAddForm(false);
  };

  const handleDeleteUser = (id: number) => {
    const user = users.find(u => u.id === id);
    if (user?.username === 'admin') return; // 不能删除admin用户
    setUsers(users.filter(user => user.id !== id));
  };

  const handleToggleUserStatus = (id: number) => {
    setUsers(users.map(user => 
      user.id === id ? { ...user, active: !user.active } : user
    ));
  };

  return (
    <div className="space-y-6">
      {/* 操作区 */}
      <div className="bg-white shadow-sm rounded-lg p-6">
        <div className="flex justify-end">
          <button
            onClick={() => setShowAddForm(!showAddForm)}
            className="rounded-button inline-flex items-center px-4 py-2 bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          >
            <i className="fas fa-plus mr-2"></i>
            新增用户
          </button>
        </div>
      </div>

      {/* 新增用户表单 */}
      {showAddForm && (
        <div className="bg-white shadow-sm rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">新增用户</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">用户名</label>
              <input
                type="text"
                value={newUser.username || ''}
                onChange={(e) => setNewUser({ ...newUser, username: e.target.value })}
                className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                placeholder="输入用户名"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">邮箱</label>
              <input
                type="email"
                value={newUser.email || ''}
                onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
                className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                placeholder="输入邮箱"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">密码</label>
              <input
                type="password"
                value={newUser.password || ''}
                onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
                className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                placeholder="输入密码"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">角色</label>
              <select
                value={newUser.role || ''}
                onChange={(e) => setNewUser({ ...newUser, role: e.target.value })}
                className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
              >
                <option value="管理员">管理员</option>
                <option value="编辑">编辑</option>
                <option value="查看者">查看者</option>
              </select>
            </div>
          </div>
          <div className="mt-4 flex justify-end space-x-3">
            <button
              onClick={() => setShowAddForm(false)}
              className="rounded-button px-4 py-2 border border-gray-300 text-gray-700 text-sm font-medium hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
            >
              取消
            </button>
            <button
              onClick={handleAddUser}
              className="rounded-button px-4 py-2 bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
            >
              添加用户
            </button>
          </div>
        </div>
      )}
      
      {/* 用户列表 */}
      <div className="bg-white shadow-sm rounded-lg overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">用户列表</h3>
          <p className="text-sm text-gray-500 mt-1">共 {users.length} 个用户</p>
        </div>
        
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
                        <div className="h-10 w-10 rounded-full bg-gray-300 flex items-center justify-center">
                          <i className="fas fa-user text-gray-600"></i>
                        </div>
                      </div>
                      <div className="ml-4">
                        <div className="text-sm font-medium text-gray-900">{user.username}</div>
                        <div className="text-sm text-gray-500">{user.email}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                      user.role === '管理员' ? 'bg-purple-100 text-purple-800' :
                      user.role === '编辑' ? 'bg-blue-100 text-blue-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {user.role}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <button
                      onClick={() => handleToggleUserStatus(user.id)}
                      className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        user.active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                      }`}
                    >
                      {user.active ? '活跃' : '禁用'}
                    </button>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <div className="flex space-x-3">
                      <button className="text-blue-600 hover:text-blue-900">
                        <i className="fas fa-edit"></i>
                      </button>
                      <button
                        onClick={() => handleDeleteUser(user.id)}
                        className={`text-red-600 hover:text-red-900 ${
                          user.username === 'admin' ? 'opacity-50 cursor-not-allowed' : ''
                        }`}
                        disabled={user.username === 'admin'}
                      >
                        <i className="fas fa-trash"></i>
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default UserManagement;