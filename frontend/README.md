# AI Media Expert Frontend

基于 React + TypeScript + Vite 构建的智能视频处理平台前端应用。

## 功能特性

- 🎥 **视频上传** - 支持拖拽上传，多文件批量处理
- 📥 **视频下载** - 支持多平台视频链接解析和下载
- 📋 **视频列表** - 可排序、可搜索的视频管理界面
- 🧠 **视频解析** - AI 智能视频内容分析和解读
- ⚙️ **系统配置** - 完整的系统设置和用户管理
- 📊 **数据看板** - 实时数据统计和可视化展示

## 技术栈

- **框架**: React 18 + TypeScript
- **构建工具**: Vite
- **路由**: React Router v6
- **样式**: TailwindCSS
- **图表**: ECharts
- **轮播**: Swiper
- **图标**: Font Awesome

## 项目结构

```
frontend/
├── public/                 # 静态资源
├── src/
│   ├── components/         # 共享组件
│   │   └── Layout.tsx     # 主布局组件
│   ├── pages/             # 页面组件
│   │   ├── Dashboard.tsx  # 数据看板
│   │   ├── VideoUpload.tsx # 视频上传
│   │   ├── VideoDownload.tsx # 视频下载
│   │   ├── VideoList.tsx  # 视频列表
│   │   ├── VideoAnalysis.tsx # 视频解析
│   │   └── SystemSettings.tsx # 系统配置
│   ├── hooks/             # 自定义 Hooks
│   ├── utils/             # 工具函数
│   ├── types/             # TypeScript 类型定义
│   ├── App.tsx            # 主应用组件
│   ├── main.tsx           # 应用入口
│   └── index.css          # 全局样式
├── package.json
├── vite.config.ts
├── tailwind.config.js
└── tsconfig.json
```

## 快速开始

### 环境要求

- Node.js >= 16.0.0
- npm >= 8.0.0

### 安装依赖

```bash
cd frontend
npm install
```

### 开发模式

```bash
npm run dev
```

应用将在 http://localhost:3000 启动

### 构建生产版本

```bash
npm run build
```

### 预览生产版本

```bash
npm run preview
```

## 主要页面说明

### 1. 数据看板 (`/dashboard`)
- 系统概览统计
- 实时数据图表
- 最近活动记录
- 系统状态监控

### 2. 视频上传 (`/upload`)
- 拖拽上传支持
- 多文件批量上传
- 实时上传进度
- 文件格式验证

### 3. 视频下载 (`/download`)
- 多平台链接解析
- 视频信息预览
- 下载选项配置
- 下载队列管理

### 4. 视频列表 (`/videos`)
- 表格式数据展示
- 多字段排序
- 高级搜索过滤
- 批量操作支持

### 5. 视频解析 (`/analysis/:id?`)
- AI 提示词配置
- 多种解析模板
- 实时流式输出
- 结果导出功能

### 6. 系统配置 (`/settings`)
- 基础系统设置
- AI API 配置
- 提示词模板管理
- 标签组管理
- 用户权限管理

## 开发指南

### 代码规范

- 使用 TypeScript 进行类型检查
- 遵循 ESLint 代码规范
- 使用 Prettier 格式化代码
- 组件采用函数式组件 + Hooks

### 样式规范

- 优先使用 TailwindCSS 工具类
- 自定义样式放在 `src/index.css`
- 响应式设计优先
- 保持设计系统一致性

### 组件开发

- 组件文件使用 PascalCase 命名
- 导出默认组件
- 使用 TypeScript 接口定义 Props
- 添加适当的注释和文档

### 状态管理

- 使用 React Hooks 进行状态管理
- 复杂状态使用 useReducer
- 全局状态考虑 Context API
- 异步状态使用自定义 useAsync Hook

## 部署说明

### 构建优化

- 代码分割和懒加载
- 图片资源优化
- 生产环境压缩
- Source Map 生成

### 环境配置

开发环境和生产环境可以通过环境变量进行配置：

```bash
# 开发环境
VITE_API_BASE_URL=http://localhost:8000/api

# 生产环境
VITE_API_BASE_URL=https://api.example.com
```

## 浏览器支持

- Chrome >= 88
- Firefox >= 85
- Safari >= 14
- Edge >= 88

## 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](../LICENSE) 文件了解详情。

## 联系方式

如有问题或建议，请通过以下方式联系：

- 项目 Issues: [GitHub Issues](https://github.com/your-repo/issues)
- 邮箱: your-email@example.com

---

**注意**: 这是一个前端原型项目，主要用于演示界面和交互逻辑。实际的后端 API 集成需要根据具体的后端接口进行调整。