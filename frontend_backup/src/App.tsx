import React from 'react';
import { Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import VideoUpload from './pages/VideoUpload';
import VideoDownload from './pages/VideoDownload';
import VideoList from './pages/VideoList';
import VideoAnalysis from './pages/VideoAnalysis';
import SystemSettings from './pages/SystemSettings';
import UserManagement from './pages/UserManagement';

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/upload" element={<VideoUpload />} />
        <Route path="/download" element={<VideoDownload />} />
        <Route path="/videos" element={<VideoList />} />
        <Route path="/analysis/:id?" element={<VideoAnalysis />} />
        <Route path="/settings" element={<SystemSettings />} />
        <Route path="/users" element={<UserManagement />} />
        {/* 默认重定向到仪表板 */}
        <Route path="*" element={<Dashboard />} />
      </Routes>
    </Layout>
  );
}

export default App;