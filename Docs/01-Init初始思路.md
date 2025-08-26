## AI新媒体专家项目需求

v0.2
2025-1-26

#### 基础设想
* 目标：建立基于AI技术的新媒体运营专家系统，构建多种类专家，每个可以独立解决一项特定的新媒体运营任务，组合起来可以构建自动化工作流
* 使用大量开源技术避免重复造轮子
* 集成在线与本地AI API
* 基于Web端的轻量化应用，无操作系统限制
* 支持SQLite（开发环境）和PostgreSQL（生产环境）的灵活数据库配置
* 优先使用本地AI模型，可选集成云端AI API作为补充

#### 系统架构设计

##### 核心架构
* **API网关**: 统一管理各专家模块的接口调用，提供统一的认证和限流
* **消息队列**: 使用Redis/Celery处理异步任务，支持任务优先级和重试机制
* **缓存策略**: 视频元数据和AI分析结果的多级缓存（内存+Redis）
* **文件存储**: 本地存储为主，支持云存储扩展（S3兼容）
* **微服务架构**: 各专家模块独立部署，通过API网关统一访问

##### 数据库设计

**用户管理模块**
* `users`: 用户基本信息（id, email, password_hash, created_at, updated_at）
* `user_sessions`: 用户会话管理（session_id, user_id, expires_at, device_info）
* `user_preferences`: 用户偏好设置（user_id, preferences_json）

**媒体管理模块**
* `videos`: 视频基本信息（id, title, description, file_path, file_size, duration, resolution, format）
* `video_metadata`: 视频元数据（video_id, platform, original_url, author, publish_date, view_count, like_count）
* `download_tasks`: 下载任务（id, user_id, url, status, progress, error_msg, created_at）
* `analysis_results`: AI分析结果（id, video_id, analysis_type, result_json, confidence, created_at）

**标签系统模块**
* `tags`: 标签定义（id, name, category, description, color）
* `video_tags`: 视频标签关联（video_id, tag_id, confidence, created_by）
* `tag_categories`: 标签分类（id, name, parent_id, description）

**任务队列模块**
* `task_queue`: 任务队列（id, task_type, payload, status, priority, retry_count）
* `task_logs`: 任务执行日志（id, task_id, level, message, timestamp）
* `task_status`: 任务状态跟踪（task_id, status, progress, start_time, end_time）

#### 安全与权限管理

##### 认证机制
* JWT token认证，支持访问令牌和刷新令牌
* 密码加密存储（bcrypt + salt）
* 支持多设备登录管理

##### 权限控制
* 基于角色的访问控制（RBAC）
* API访问频率限制（用户级别和IP级别）
* 敏感操作二次验证

##### 数据安全
* 用户数据隔离策略
* 敏感配置加密存储
* 定期数据备份机制

#### 系统入口
* 简单的用户注册、登录机制，邮箱+密码，不需要验证邮箱
* 支持第三方登录（Google、GitHub、微信登录等）
* 入口为专家集中展示与选择，选择后进入专家单独页面
* 统一的用户仪表板，显示任务状态和系统概览

#### 1号专家：视频下载专家
* 输入网址、媒体账号，可自动化批量或单条下载媒体视频
* 非登录或登录状态均要下载最高质量视频
* 登录可要求用户录入cookie或要用户扫码登录
* 可只下载视频或音频
* 可下载字幕、弹幕、评论等附加信息
* 支持多平台：抖音、快手、B站、YouTube、Instagram等
* 第一个版本专项处理抖音视频下载
* 选择下载视频后，进入下载队列，无需在界面等待完成
* 可随时查看下载进度，可暂停、继续、重新开始、删除，自动记录相关log
* 下载后视频存储在本地，在DB中记录视频编号，对应账号、原始地址，原始标题，关键词，下载后的文件名，相关视频参数（大小、尺寸、码率、帧率）等
* 管理界面批量列出、管理已下载视频，支持搜索、筛选、排序
* 还可以自己上传视频，人工填写信息，自动解析参数，记录到DB，已备后续使用
* 支持下载任务调度和优先级管理
* 参考项目
	* [Douyin_TikTok_Download_API](https://github.com/Evil0ctal/Douyin_TikTok_Download_API)
	* [TikTokDownloader](https://github.com/JoeanAmier/TikTokDownloader)

#### 2号专家：视频解读专家
* 选择1号专家下载或上传的视频
* 选择视频解析模板，可以预设多套模板，或使用默认模板
* 支持自定义解析模板（JSON配置）
* 选择封闭式标签库，或现有标签+开放标签，或完全开放式标签库
* 调用多媒体模型，解读视频，按解析模板，将视频的解读结果以markdown格式存储在本地DB
* 支持多种AI模型：视觉理解、语音识别、情感分析、内容分类
* 根据打标策略，为视频打标，标签记录数据库
* AI解读过程为异步、流式过程，无需在界面等待结果
* 支持批量处理和定时任务
* 管理界面，可以查看已经处理视频和对应的解读记录，并支持下载记录等功能
* 结果导出支持多种格式（JSON、CSV、Excel、PDF报告）

#### 3号专家：视频字幕专家
* 基于Whisper等开源模型进行语音识别
* 支持多语言识别和翻译
* 字幕时间轴自动对齐
* 支持字幕格式转换（SRT、VTT、ASS等）
* 字幕内容智能校对和优化
* 支持批量处理和自动化工作流

#### 4 - 10号专家
* 暂不开发（预留界面位置与接口）

#### 监控与运维

##### 系统监控
* 健康检查接口（/health, /ready）
* 任务执行状态实时监控
* 系统资源使用监控（CPU、内存、磁盘、网络）
* API响应时间和错误率监控

##### 日志管理
* 结构化日志记录（JSON格式）
* 日志级别管理（DEBUG、INFO、WARN、ERROR）
* 日志轮转和归档策略
* 错误日志告警机制

##### 性能优化
* 数据库查询优化和索引策略
* 静态资源CDN加速
* 图片和视频压缩优化
* 缓存命中率监控

#### 技术栈

##### 后端服务
* **Web框架**: FastAPI（主要API服务）+ Gradio（AI模型界面）
* **数据库**: SQLAlchemy + Alembic（ORM和迁移）
* **任务队列**: Celery + Redis（异步任务处理）
* **缓存**: Redis（会话、缓存、消息队列）
* **包管理**: uv（Python）、npm（Node.js）

##### 视频处理
* **视频下载**: [yt-dlp](https://github.com/yt-dlp/yt-dlp)（主要）+ [gallery-dl](https://github.com/mikf/gallery-dl)（备选）
* **多媒体处理**: [FFmpeg](https://github.com/FFmpeg/FFmpeg)
* **视频分析**: [OpenCV](https://github.com/opencv/opencv)（计算机视觉基础）
* **目标检测**: [YOLO](https://github.com/ultralytics/ultralytics)（实时检测）
* **媒体处理**: [MediaPipe](https://github.com/google/mediapipe)（Google媒体处理框架）

##### AI模型集成
* **本地模型**:
  * [Whisper](https://github.com/openai/whisper)（语音识别）
  * [CLIP](https://github.com/openai/CLIP)（图像理解）
  * [Transformers](https://github.com/huggingface/transformers)（HuggingFace模型库，同时支持[模塔](https://www.modelscope.cn/)）
* **云端API**（可选集成）:
  * GLM-4.5V 视频推理接口（作为本地模型的补充）
  * OpenAI兼容类型LLM接口（支持多种本地和云端服务）
  * Gemini接口（高级分析功能的备选方案）
  * 本地Ollama、LM Studio接口（优先推荐的本地化方案）

##### 前端界面
* **主界面**: Gradio（快速原型）
* **管理后台**: React/Vue（可选，复杂管理功能）
* **UI组件**: 支持自定义主题和响应式设计

##### 部署运维
* **容器化**: Docker + Docker Compose
* **反向代理**: Nginx
* **监控**: Prometheus + Grafana（可选）
* **日志**: ELK Stack或简化版本

##### 数据存储
* **主数据库**: 
  * **开发环境**: SQLite - 轻量级，无需额外配置，便于快速开发和测试
  * **生产环境**: PostgreSQL - 高性能，支持并发，适合生产部署
  * **自动切换**: 通过环境变量自动选择数据库类型
* **文件存储**: 本地文件系统 + S3兼容存储（MinIO/AWS S3）
* **配置管理**: 环境变量 + 配置文件 + 数据库配置表

#### 开发计划

##### Phase 1 (MVP - 4周)
1. **基础架构搭建**
   - FastAPI项目初始化
   - 数据库设计和迁移
   - 用户认证系统
   - Docker开发环境

2. **视频下载专家**
   - yt-dlp集成
   - 抖音视频下载功能
   - 基础任务队列
   - 简单的管理界面

##### Phase 2 (核心功能 - 6周)
1. **视频解读专家**
   - AI模型集成
   - 视频分析流水线
   - 标签系统实现
   - 结果展示界面

2. **系统优化**
   - 异步任务优化
   - 缓存策略实现
   - 错误处理完善
   - 性能监控

##### Phase 3 (扩展功能 - 4周)
1. **字幕专家**
   - Whisper集成
   - 多语言支持
   - 字幕格式转换

2. **系统完善**
   - 批量处理功能
   - 高级搜索和筛选
   - 数据导出功能
   - 用户权限细化

#### 部署建议

##### 开发环境
```bash
# 使用Docker Compose一键启动
docker-compose up -d
```

##### 生产环境
* 使用PostgreSQL替代SQLite
* 配置Redis集群
* 设置Nginx负载均衡
* 配置SSL证书
* 设置定时备份

##### 扩展性考虑
* 支持水平扩展（多实例部署）
* 数据库读写分离
* CDN静态资源加速
* 微服务拆分（按专家模块）

#### 风险评估与应对

##### 技术风险
* **AI API限制**: 准备多个备选方案，支持本地模型
* **视频平台反爬**: 及时更新下载工具，准备多个下载源
* **性能瓶颈**: 提前进行压力测试，准备扩展方案

##### 合规风险
* **版权问题**: 明确使用条款，仅供个人学习使用
* **数据隐私**: 严格的数据隔离和加密策略
* **平台政策**: 遵守各平台的使用条款

#### 成本估算

##### 开发成本
* 开发时间：约14周（3.5个月）
* 人力成本：1-2名全栈开发者
* 基础设施：开发阶段基本免费

##### 运营成本
* 服务器：$50-200/月（根据用户量）
* AI API调用：$100-500/月（根据使用量）
* 存储成本：$20-100/月（根据视频数量）

---

**注意事项**：
1. 本项目仅供学习和研究使用
2. 请遵守相关平台的使用条款
3. 注意保护用户隐私和数据安全
4. 建议在使用前咨询相关法律法规


