# GLM-4.5V视频理解模型 - ngrok配置指南

## 概述

由于GLM-4.5V等视频理解模型运行在远程服务器上，无法直接访问本地的`localhost`地址，因此需要使用ngrok等内网穿透工具将本地服务暴露到公网，让AI模型能够访问视频文件。

## 快速开始

### 方法一：使用自动化脚本（推荐）

1. **运行启动脚本**：
   ```bash
   # Windows用户
   start_ngrok.bat
   
   # 或者直接运行Python脚本
   python scripts/start_ngrok.py
   ```

2. **按提示操作**：
   - 脚本会自动检查并安装ngrok
   - 输入后端服务端口（默认8000）
   - 获取公网URL并自动更新.env文件

3. **重启后端服务**：
   ```bash
   # 停止当前服务（Ctrl+C）
   # 重新启动
   uvicorn app.app:app --host 0.0.0.0 --port 8000 --reload
   ```

### 方法二：手动配置

1. **安装ngrok**：
   ```bash
   npm install -g ngrok
   ```

2. **启动ngrok隧道**：
   ```bash
   ngrok http 8000
   ```

3. **获取公网URL**：
   - 从ngrok输出中复制HTTPS地址
   - 例如：`https://abc123.ngrok.io`

4. **配置环境变量**：
   ```bash
   # 在.env文件中添加
   NGROK_URL=https://abc123.ngrok.io
   ```

5. **重启后端服务**。

## 配置说明

### 环境变量

在`.env`文件中可以配置以下变量：

```bash
# ngrok公网地址（优先级最高）
NGROK_URL=https://abc123.ngrok.io

# 自定义公网地址（如果有固定域名）
PUBLIC_BASE_URL=https://your-domain.com

# 服务器配置
HOST=0.0.0.0
PORT=8000
```

### URL优先级

系统按以下优先级选择基础URL：
1. `PUBLIC_BASE_URL` - 自定义公网地址
2. `NGROK_URL` - ngrok生成的地址
3. `http://localhost:8000` - 本地地址（默认）

## 使用流程

### 1. 启动服务

```bash
# 终端1：启动后端服务
uvicorn app.app:app --host 0.0.0.0 --port 8000 --reload

# 终端2：启动ngrok隧道
ngrok http 8000

# 终端3：启动前端服务
cd frontend && npm run dev
```

### 2. 配置AI模型

在系统配置中添加GLM-4.5V模型：
- **提供商**：GLM
- **模型名称**：glm-4.5v
- **API密钥**：你的GLM API密钥
- **API基础URL**：https://open.bigmodel.cn/api/paas/v4

### 3. 测试视频分析

1. 上传视频文件
2. 选择GLM-4.5V模型
3. 配置分析参数
4. 开始分析
5. 查看实时调试信息，确认使用"视频内容理解模式"

## 故障排除

### 常见问题

**Q: ngrok安装失败**
A: 确保已安装Node.js，然后运行：
```bash
npm install -g ngrok
```

**Q: 无法访问ngrok管理界面**
A: 访问 http://localhost:4040 查看隧道状态

**Q: GLM模型仍显示"元数据分析模式"**
A: 检查：
1. .env文件中是否正确设置了NGROK_URL
2. 后端服务是否重启
3. AI配置中模型名称是否为"glm-4.5v"

**Q: 视频URL无法访问**
A: 检查：
1. ngrok隧道是否正常运行
2. 视频文件是否存在于uploads目录
3. 静态文件服务是否正确配置

### 调试方法

1. **查看生成的视频URL**：
   - 在后端日志中查找"Generated video URL for GLM model"
   - 手动访问该URL确认视频可访问

2. **检查ngrok状态**：
   ```bash
   curl http://localhost:4040/api/tunnels
   ```

3. **验证环境变量**：
   ```python
   from app.core.config import settings
   print(settings.get_base_url())
   ```

## 安全注意事项

1. **HTTPS优先**：ngrok默认提供HTTPS，确保数据传输安全
2. **临时使用**：ngrok免费版URL会定期变更，仅适合开发测试
3. **访问控制**：生产环境建议使用付费版ngrok或云存储方案
4. **敏感数据**：避免在公网URL中暴露敏感信息

## 生产环境建议

对于生产环境，建议使用以下方案：

1. **云存储服务**：
   - 阿里云OSS、腾讯云COS
   - AWS S3、Google Cloud Storage
   - 提供稳定的公网访问能力

2. **CDN加速**：
   - 提高视频加载速度
   - 减少带宽成本
   - 提供更好的用户体验

3. **域名绑定**：
   - 使用固定域名
   - 配置SSL证书
   - 提供专业的服务体验

## 相关链接

- [ngrok官方文档](https://ngrok.com/docs)
- [GLM-4.5V API文档](https://open.bigmodel.cn/dev/api)
- [项目GitHub仓库](https://github.com/your-repo)