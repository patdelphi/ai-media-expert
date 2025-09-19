# 视频解析功能模块开发计划

## 📋 项目概述

**目标**：开发视频解析功能模块，通过预设模板+标签组整合提示词，调用AI API对选中视频进行解析，返回流式结果并用markdown渲染展示。

**核心功能**：
- 视频选择（复用最近上传的3个视频列表）
- 预设模板管理
- 标签组管理
- 提示词整合
- AI API调用
- 流式结果处理
- Markdown渲染展示

## 🏗️ 系统架构设计

### 1. 数据模型设计

#### 1.1 预设模板模型 (PromptTemplate)
```python
class PromptTemplate(Base):
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)  # 模板名称
    description = Column(String(500))           # 模板描述
    template_content = Column(Text, nullable=False)  # 模板内容
    category = Column(String(100))              # 模板分类
    variables = Column(JSON)                    # 模板变量定义
    is_active = Column(Boolean, default=True)   # 是否启用
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
```

#### 1.2 标签组模型 (TagGroup)
```python
class TagGroup(Base):
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)  # 标签组名称
    description = Column(String(500))           # 标签组描述
    tags = Column(JSON, nullable=False)         # 标签列表
    category = Column(String(100))              # 标签组分类
    is_active = Column(Boolean, default=True)   # 是否启用
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
```

#### 1.3 视频解析记录模型 (VideoAnalysis)
```python
class VideoAnalysis(Base):
    id = Column(Integer, primary_key=True)
    video_file_id = Column(Integer, ForeignKey('uploaded_files.id'))  # 关联视频文件
    template_id = Column(Integer, ForeignKey('prompt_templates.id'))   # 使用的模板
    tag_group_ids = Column(JSON)                # 使用的标签组ID列表
    prompt_content = Column(Text)               # 最终生成的提示词
    ai_provider = Column(String(50))            # AI服务提供商
    ai_model = Column(String(100))              # AI模型名称
    analysis_result = Column(Text)              # 解析结果
    status = Column(String(20), default='pending')  # 状态：pending/processing/completed/failed
    error_message = Column(Text)                # 错误信息
    processing_time = Column(Float)             # 处理时间（秒）
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
```

### 2. API接口设计

#### 2.1 模板管理接口
- `GET /api/v1/templates` - 获取模板列表
- `POST /api/v1/templates` - 创建模板
- `PUT /api/v1/templates/{id}` - 更新模板
- `DELETE /api/v1/templates/{id}` - 删除模板

#### 2.2 标签组管理接口
- `GET /api/v1/tag-groups` - 获取标签组列表
- `POST /api/v1/tag-groups` - 创建标签组
- `PUT /api/v1/tag-groups/{id}` - 更新标签组
- `DELETE /api/v1/tag-groups/{id}` - 删除标签组

#### 2.3 视频解析接口
- `GET /api/v1/videos/recent` - 获取最近上传的视频列表
- `POST /api/v1/analysis/start` - 开始视频解析
- `GET /api/v1/analysis/{id}/stream` - 获取流式解析结果
- `GET /api/v1/analysis/{id}` - 获取解析结果
- `GET /api/v1/analysis/history` - 获取解析历史

### 3. AI API集成方案

#### 3.1 支持的AI服务提供商
- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude)
- Google (Gemini)
- 百度 (文心一言)
- 阿里 (通义千问)

#### 3.2 AI API配置
```python
class AIConfig:
    providers = {
        'openai': {
            'api_key': 'OPENAI_API_KEY',
            'base_url': 'https://api.openai.com/v1',
            'models': ['gpt-4', 'gpt-3.5-turbo']
        },
        'anthropic': {
            'api_key': 'ANTHROPIC_API_KEY',
            'base_url': 'https://api.anthropic.com',
            'models': ['claude-3-opus', 'claude-3-sonnet']
        }
    }
```

## 🔧 开发阶段规划

### 阶段1：数据模型和基础API开发 (2-3天)

**任务清单**：
1. ✅ 检查现有数据结构
2. 🔲 创建PromptTemplate模型
3. 🔲 创建TagGroup模型
4. 🔲 创建VideoAnalysis模型
5. 🔲 数据库迁移脚本
6. 🔲 基础CRUD API开发
7. 🔲 API测试脚本

**输出物**：
- 数据库模型文件
- API接口文件
- 数据库迁移脚本
- API测试用例

### 阶段2：AI API集成和提示词处理 (3-4天)

**任务清单**：
1. 🔲 AI服务配置管理
2. 🔲 提示词模板引擎
3. 🔲 标签组整合逻辑
4. 🔲 AI API调用封装
5. 🔲 流式响应处理
6. 🔲 错误处理和重试机制
7. 🔲 AI服务测试

**输出物**：
- AI服务集成模块
- 提示词处理引擎
- 流式响应处理器
- AI API测试用例

### 阶段3：视频解析核心功能 (2-3天)

**任务清单**：
1. 🔲 视频选择接口
2. 🔲 解析任务创建
3. 🔲 异步解析处理
4. 🔲 解析状态管理
5. 🔲 结果存储和检索
6. 🔲 解析历史管理
7. 🔲 核心功能测试

**输出物**：
- 视频解析服务
- 任务队列处理
- 状态管理系统
- 核心功能测试

### 阶段4：前端集成和UI优化 (2-3天)

**任务清单**：
1. 🔲 视频选择组件
2. 🔲 模板选择组件
3. 🔲 标签组选择组件
4. 🔲 解析进度显示
5. 🔲 Markdown结果渲染
6. 🔲 解析历史查看
7. 🔲 前端集成测试

**输出物**：
- 前端组件库
- 解析界面
- 结果展示页面
- 前端测试用例

## 📊 技术栈选择

### 后端技术
- **框架**：FastAPI
- **数据库**：SQLite (开发) / PostgreSQL (生产)
- **ORM**：SQLAlchemy
- **异步处理**：Celery + Redis
- **AI API**：httpx (异步HTTP客户端)
- **流式处理**：Server-Sent Events (SSE)

### 前端技术
- **框架**：React + TypeScript
- **状态管理**：React Hooks
- **HTTP客户端**：fetch API
- **Markdown渲染**：react-markdown
- **流式数据**：EventSource API
- **UI组件**：Tailwind CSS

## 🔍 关键技术点

### 1. 提示词模板引擎
```python
class PromptEngine:
    def render_template(self, template: str, variables: dict, tags: list) -> str:
        # 使用Jinja2模板引擎
        # 支持变量替换和标签插入
        pass
```

### 2. 流式响应处理
```python
async def stream_analysis_result(analysis_id: int):
    async for chunk in ai_service.stream_response():
        yield f"data: {json.dumps(chunk)}\n\n"
```

### 3. 前端流式数据接收
```javascript
const eventSource = new EventSource(`/api/v1/analysis/${id}/stream`);
eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    setAnalysisResult(prev => prev + data.content);
};
```

## 🧪 测试策略

### 1. 单元测试
- 数据模型测试
- API接口测试
- 提示词引擎测试
- AI服务集成测试

### 2. 集成测试
- 端到端解析流程测试
- 流式响应测试
- 前后端集成测试

### 3. 性能测试
- AI API响应时间测试
- 并发解析能力测试
- 流式数据传输性能测试

## 📈 监控和日志

### 1. 关键指标
- 解析成功率
- 平均解析时间
- AI API调用次数
- 错误率统计

### 2. 日志记录
- 解析请求日志
- AI API调用日志
- 错误和异常日志
- 性能指标日志

## 🚀 部署和运维

### 1. 环境配置
- 开发环境：本地SQLite + 模拟AI API
- 测试环境：PostgreSQL + 真实AI API
- 生产环境：PostgreSQL + Redis + 负载均衡

### 2. 配置管理
- AI API密钥管理
- 数据库连接配置
- 缓存配置
- 日志配置

## 📝 文档计划

1. **API文档**：使用FastAPI自动生成
2. **用户手册**：功能使用说明
3. **开发文档**：代码结构和扩展指南
4. **部署文档**：环境搭建和配置说明

---

**预计总开发时间**：10-12天
**团队规模**：1-2人
**优先级**：高
**风险评估**：中等（主要风险在AI API集成和流式处理）