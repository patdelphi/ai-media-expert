# Qwen 上传专用 Key 设计

## 背景

当前项目已经接通了 `Qwen` 的百炼临时文件上传能力，但现有 AI 配置只有一个 `api_key` 字段。实际场景中：

- 百炼临时上传使用一把标准百炼 Key
- `Qwen` 视频解析使用另一把 Key
- 两把 Key 属于同一个阿里云主账号

现有实现会把同一把 `api_key` 同时用于：

- 获取百炼上传凭证
- 上传临时文件
- 调用视频解析模型

这与当前业务需求不符，需要把上传鉴权与解析鉴权彻底拆开。

## 目标

- 为 `Qwen` 文件上传增加独立的 `upload_api_key`
- `upload_api_key` 只用于百炼临时文件上传
- 原 `api_key` 继续只用于模型解析
- 不做 Key 复用，不做自动回退
- 仅对 `Qwen` 的 `upload` 传输方式生效

## 非目标

- 不为其他模型提供单独上传 Key
- 不支持上传与解析跨主账号
- 不改变 `URL` / `Base64` 的现有行为
- 不自动迁移或推断已有配置中的上传 Key

## 方案对比

### 方案A：新增 `upload_api_key`

做法：

- 在 AI 配置模型、接口、前端表单中新增 `upload_api_key`
- 百炼临时上传固定使用 `upload_api_key`
- 视频解析固定使用原 `api_key`

优点：

- 语义清晰
- 最符合当前真实业务
- 行为稳定，不会因为回退逻辑混淆问题

缺点：

- 需要前后端都补字段

结论：

- 采用该方案

### 方案B：上传默认复用 `api_key`，可选填 `upload_api_key`

优点：

- 兼容老配置

缺点：

- 容易混用
- 不符合本次“不要和解析混用”的明确要求

结论：

- 不采用

### 方案C：拆成两条 AI 配置

优点：

- 不必新增字段

缺点：

- 使用复杂
- 前端交互和运维成本更高

结论：

- 不采用

## 数据设计

### 后端数据模型

目标文件：

- `app/models/video.py`
- `app/schemas/video.py`

变更：

- 为 AI 配置新增可空字段 `upload_api_key`
- 数据库存储时沿用现有 `api_key` 的处理方式，支持加密存储
- 完整配置查询接口返回该字段的脱敏值或明文提交态

字段规则：

- `upload_api_key`: 可空字符串
- 仅在 `Qwen + upload` 场景必填
- 其他模型允许为空

### 前端类型

目标文件：

- `frontend/src/services/aiConfig.ts`
- `frontend/src/pages/SystemConfig.tsx`

变更：

- `AIConfig`
- `CreateAIConfigRequest`
- `UpdateAIConfigRequest`

以上类型新增：

- `upload_api_key?: string`

## 后端设计

### 上传鉴权分流

目标文件：

- `app/services/ai_service.py`

行为约束：

- 当 `transmission_method != "upload"` 时，不读取 `upload_api_key`
- 当模型不是 `Qwen` 视频模型时，不读取 `upload_api_key`
- 当模型是 `Qwen` 且传输方式是 `upload` 时：
  - 获取上传凭证使用 `upload_api_key`
  - 上传文件到百炼临时存储使用 `upload_api_key`
  - 调用 `chat/completions` 解析视频使用原 `api_key`

错误处理：

- 若 `Qwen + upload` 且缺少 `upload_api_key`：
  - 直接抛出清晰错误
- 若 `upload_api_key` 无法解密或格式非法：
  - 返回清晰错误，不进入上传请求
- 若上传凭证接口返回 `401/403`：
  - 明确标记为上传 Key 鉴权失败

### 调试信息

目标文件：

- `app/services/ai_service.py`

要求：

- `debug_info` 中记录上传与解析两个阶段的行为
- 脱敏后写入：
  - 是否使用了 `upload_api_key`
  - 上传凭证接口地址
  - 模型解析接口地址
- 不记录明文 Key

## 前端设计

### 系统设置页

目标文件：

- `frontend/src/pages/SystemConfig.tsx`

变更：

- 新建 AI 配置时增加 `上传专用 API Key`
- 编辑 AI 配置时增加 `上传专用 API Key`
- 说明文案明确：
  - 仅用于 `Qwen` 文件上传
  - 不参与模型解析
  - 为空时，`Qwen` 的 `文件上传` 不可用

交互要求：

- 字段为密码样式输入
- 编辑时沿用现有 `api_key` 的掩码策略
- 若已有掩码值且未修改，则更新请求不覆盖原值

### 视频解析页

目标文件：

- `frontend/src/pages/VideoAnalysis.tsx`

本次不新增交互项。

沿用现有：

- `URL方式`
- `Base64编码`
- `文件上传`

但 `文件上传` 的可用性由后端校验决定。

## API 设计

目标文件：

- `app/api/v1/ai_config.py`

要求：

- 创建 AI 配置支持接收 `upload_api_key`
- 更新 AI 配置支持接收 `upload_api_key`
- 查询完整 AI 配置时返回 `upload_api_key`
  - 仅管理员完整接口返回
  - 返回时脱敏
- 测试 AI 配置接口本次不强制验证上传 Key
  - 仍保持原连接测试语义

## 兼容性

- 旧配置无需立刻修改
- 非 `Qwen` 模型完全不受影响
- `Qwen` 若继续使用 `URL` / `Base64`，也不要求填写 `upload_api_key`
- 只有 `Qwen + 文件上传` 才强制要求该字段

## 测试设计

### 后端

目标文件：

- `app/tests/test_ai_config_security.py`

新增覆盖：

- 创建/更新配置时可保存 `upload_api_key`
- `Qwen + upload` 时上传凭证请求使用 `upload_api_key`
- 模型解析请求仍使用 `api_key`
- 缺少 `upload_api_key` 时明确失败
- 非 `Qwen` 模型不会误用 `upload_api_key`

### 前端

目标文件：

- `frontend/src/pages/SystemConfig.test.tsx`

新增覆盖：

- AI 配置表单显示 `上传专用 API Key`
- 创建请求携带 `upload_api_key`
- 编辑时未修改掩码值不会覆盖原值

## 风险与处理

- 风险：字段变更涉及数据库
  - 处理：增加明确迁移脚本，为 AI 配置表新增 `upload_api_key`
- 风险：前端编辑态密钥掩码与真实值混淆
  - 处理：沿用现有 `api_key` 提交策略，未改动时不覆盖
- 风险：调用链路难排查
  - 处理：增强 `debug_info`，拆分上传阶段与解析阶段信息

## 验收标准

- 系统设置可配置并保存 `upload_api_key`
- `Qwen + 文件上传` 时：
  - 上传接口使用 `upload_api_key`
  - 解析接口使用 `api_key`
- 缺少 `upload_api_key` 时返回清晰错误
- 非 `Qwen` 场景无行为回归
- 相关前后端测试通过
