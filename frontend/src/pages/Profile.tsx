import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const Profile: React.FC = () => {
  const { user } = useAuth();

  return (
    <div className="space-y-6">
      <div className="bg-white shadow-sm rounded-lg p-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-gray-800">个人资料</h2>
            <p className="text-gray-500 text-sm mt-1">查看你的账户信息</p>
          </div>
          <Link to="/settings" className="btn-primary text-sm">
            账户设置
          </Link>
        </div>
      </div>

      <div className="bg-white shadow-sm rounded-lg p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <div className="text-sm text-gray-500">邮箱</div>
            <div className="text-gray-900 mt-1">{user?.email || '-'}</div>
          </div>
          <div>
            <div className="text-sm text-gray-500">用户名</div>
            <div className="text-gray-900 mt-1">{user?.username || '-'}</div>
          </div>
          <div>
            <div className="text-sm text-gray-500">姓名</div>
            <div className="text-gray-900 mt-1">{user?.full_name || '-'}</div>
          </div>
          <div>
            <div className="text-sm text-gray-500">角色</div>
            <div className="text-gray-900 mt-1">{user?.role || '-'}</div>
          </div>
        </div>
      </div>

      <div className="bg-white shadow-sm rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-2">登录安全</h3>
        <p className="text-sm text-gray-600 mb-4">可在账户设置中修改登录密码。</p>
        <Link to="/settings" className="btn-secondary text-sm">
          去修改密码
        </Link>
      </div>
    </div>
  );
};

export default Profile;

