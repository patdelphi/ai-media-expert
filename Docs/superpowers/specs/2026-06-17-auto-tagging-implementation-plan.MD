\uFEFF# 标签体系与 AI 自动打标实施计划

## 目标

基于已确认的 `"2026-06-17-auto-tagging-design.MD"`，将“正式标签体系 + AI 自动打标”拆解为可分批实施、可逐步验证的开发计划。

本计划遵循以下约束：

- 自动打标与模板解析分离
- 自动打标默认先读视频
- 模板解析默认复用打标结果，必要时才二次读视频
- AI 结果先直接生效
- 允许人工修订，并保留版本与变更历史
- 一期暂不做标签关系、冲突规则、统计看板
- 新功能优先先写测试，再补实现

## 交付范围

### 一期交付

- 自动打标数据表与迁移脚本
- 自动打标任务 API
- 自动打标服务与结构化结果落库
- 当前视频有效标签层
- 人工修订与版本历史
- 模板解析默认复用自动打标上下文
- 最小前端展示与修订交互
- 相关前后端测试

### 不在一期

- 标签治理后台
- 标签统计看板
- 标签冲突自动裁决
- 批量任务编排

## 分批实施

### 批次 1：数据层打底

#### 目标

- 先把数据结构和迁移能力建立起来，为后续 API 和服务提供稳定存储层

#### 先写测试

- 新增迁移或模型层测试，至少覆盖：
  - 新表可创建
  - 外键关系正确
  - 关键索引存在
  - 约束字段可正常写入/查询

#### 需要修改/新增的文件

- `"app/models/uploaded_file.py"`
  - 增加与新标签表的 relationship
- `"app/models/video.py"`
  - 评估复用 `Tag`
  - 为 `Tag` 增加必要字段：
    - `source_type`
    - `tag_group_id`
    - `is_active`
- 新增自动打标模型文件，建议：
  - `"app/models/video_auto_tag.py"`
    - `VideoAutoTagTask`
    - `VideoAutoTagItem`
    - `UploadedFileTag`
    - `UploadedFileTagRevision`
    - `UploadedFileTagRevisionItem`
- `"app/models/__init__.py"`
  - 导出新模型
- 新增迁移脚本，建议：
  - `"scripts/add_auto_tagging_tables_migration.py"`

#### 数据表建议

- `video_auto_tag_tasks`
- `video_auto_tag_items`
- `uploaded_file_tags`
- `uploaded_file_tag_revisions`
- `uploaded_file_tag_revision_items`

#### 验证标准

- 迁移脚本可成功执行
- 数据库中可看到新表与索引
- ORM 读写正常

### 批次 2：Schema 与基础 API 骨架

#### 目标

- 先把 API 的输入输出边界定下来

#### 先写测试

- 新增 API 层测试，至少覆盖：
  - 创建自动打标任务请求校验
  - 查询任务详情接口权限
  - 查询当前有效标签接口返回结构
  - 创建修订请求的参数校验

#### 需要修改/新增的文件

- 新增 schema 文件，建议：
  - `"app/schemas/video_auto_tag.py"`
- `"app/api/v1/api.py"`
  - 注册自动打标相关路由
- 新增 endpoint 文件，建议：
  - `"app/api/v1/endpoints/video_auto_tags.py"`
  - `"app/api/v1/endpoints/uploaded_file_tags.py"`

#### 一期接口清单

- `POST /api/v1/video-auto-tags/start`
- `GET /api/v1/video-auto-tags/{task_id}`
- `GET /api/v1/uploaded-files/{video_file_id}/tags`
- `POST /api/v1/uploaded-files/{video_file_id}/tags/revisions`
- `GET /api/v1/uploaded-files/{video_file_id}/tags/revisions`
- `GET /api/v1/uploaded-files/{video_file_id}/tags/revisions/{revision_id}`

#### 验证标准

- 接口可注册
- 基础鉴权与参数校验通过
- 返回结构与 spec 对齐

### 批次 3：自动打标服务

#### 目标

- 打通“启动任务 -> 调模型 -> 解析结构化结果 -> 落库”的主链路

#### 先写测试

- 新增服务层测试，至少覆盖：
  - 自动打标任务创建成功
  - 模型返回标准 JSON 时可正确解析
  - 固定标签命中可正确映射到正式标签
  - 自由标签候选可保留为未提升项
  - 异常 JSON 返回时任务失败并记录错误

#### 需要修改/新增的文件

- 新增服务文件，建议：
  - `"app/services/video_auto_tag_service.py"`
- `"app/services/ai_service.py"`
  - 复用已有视频读取与模型调用能力
  - 新增自动打标专用请求构造方法
- `"app/api/v1/endpoints/video_auto_tags.py"`
  - 调用自动打标服务

#### 实现重点

- 自动组装固定标签库提示词
- 强约束模型输出结构化 JSON
- 输出校验：
  - JSON 格式
  - 置信度范围
  - 时间段合法性
  - 空字段兜底
- 自动打标结果落库：
  - `video_auto_tag_tasks`
  - `video_auto_tag_items`

#### 验证标准

- 自动打标任务可跑通
- 失败和成功状态都可追踪
- 原始结果与结构化摘要能正确保存

### 批次 4：主标签同步

#### 目标

- 将自动打标的有效结果同步为视频当前主标签

#### 先写测试

- 新增同步逻辑测试，至少覆盖：
  - 固定标签命中直接进入 `uploaded_file_tags`
  - 自由标签低于阈值时不进入主标签层
  - 自由标签高于阈值时可进入主标签层
  - 同步失败时事务回滚

#### 需要修改/新增的文件

- `"app/services/video_auto_tag_service.py"`
  - 增加同步主标签方法
- 可选新增辅助服务：
  - `"app/services/tag_sync_service.py"`

#### 实现重点

- 正式标签映射
- 自由标签提升策略
- 主标签层去重
- 事务边界清晰

#### 验证标准

- 自动打标完成后，视频可查到当前有效标签
- 主标签数据和任务结果可相互追溯

### 批次 5：人工修订与版本历史

#### 目标

- 支持人工后改，但不覆盖 AI 原始结果

#### 先写测试

- 新增修订接口测试，至少覆盖：
  - 创建新修订版本成功
  - `add/remove/adjust` 三类操作可写入
  - 修订失败时整笔事务回滚
  - 修订后 `uploaded_file_tags` 正确更新
  - 原始自动打标任务结果保持不变

#### 需要修改/新增的文件

- `"app/api/v1/endpoints/uploaded_file_tags.py"`
- `"app/services/uploaded_file_tag_revision_service.py"` 或合并到标签服务中
- `"app/schemas/video_auto_tag.py"`

#### 实现重点

- 版本号递增
- 明细级变更记录
- 当前有效标签重建
- 修订理由留痕

#### 验证标准

- 历史版本可查
- 当前主标签可回溯来源
- 修订不会污染 AI 原始数据

### 批次 6：模板解析复用自动打标结果

#### 目标

- 让现有模板解析默认不重复读视频

#### 先写测试

- 新增解析链路测试，至少覆盖：
  - 有自动打标结果时，模板解析默认读取当前有效标签
  - 有自动打标摘要时，模板解析默认读取结构化摘要
  - 高精度模板可触发二次读视频
  - 无自动打标结果时有明确降级策略

#### 需要修改的文件

- `"app/api/v1/endpoints/video_analysis.py"`
- `"app/services/ai_service.py"`
- 如有必要新增：
  - `"app/services/video_analysis_context_service.py"`

#### 实现重点

- 模板解析上下文构造重构
- 默认上下文来源：
  - 当前有效标签
  - 最近一次成功自动打标摘要
- 高精度模板开关设计
- 缺失自动打标结果时的降级策略

#### 验证标准

- 普通模板默认不重复读视频
- 高精度模板能显式再次读视频

### 批次 7：前端展示与修订交互

#### 目标

- 让用户在界面上能看到打标结果、主标签和修订历史

#### 先写测试

- 新增前端页面测试，至少覆盖：
  - 自动打标结果展示
  - 当前有效标签展示
  - 发起人工修订
  - 查看修订历史
  - 模板解析使用自动打标上下文的状态提示

#### 需要修改/新增的文件

- 新增服务文件，建议：
  - `"frontend/src/services/videoAutoTag.ts"`
- `"frontend/src/pages/VideoAnalysis.tsx"`
  - 增加自动打标结果区块
  - 增加当前有效标签展示
- 如 UI 过重，可新增组件：
  - `"frontend/src/components/auto-tag/AutoTagPanel.tsx"`
  - `"frontend/src/components/auto-tag/EffectiveTagsPanel.tsx"`
  - `"frontend/src/components/auto-tag/TagRevisionDialog.tsx"`

#### 一期最小 UI

- 启动自动打标按钮
- 自动打标状态展示
- 当前有效标签列表
- 人工新增/删除标签
- 修订历史弹窗或侧栏

#### 验证标准

- 用户可完整走通：
  - 自动打标
  - 查看结果
  - 人工修订
  - 再发起模板解析

## 推荐开发顺序

建议严格按以下顺序推进：

1. 批次 1：数据层打底
2. 批次 2：Schema 与 API 骨架
3. 批次 3：自动打标服务
4. 批次 4：主标签同步
5. 批次 5：人工修订与版本历史
6. 批次 6：模板解析复用自动打标结果
7. 批次 7：前端展示与修订交互

原因：

- 先稳定数据结构
- 再稳定接口边界
- 再打通 AI 主链路
- 最后接前端，返工最少

## 风险点

### 1. 老 `videos` 域与当前 `uploaded_files` 域混用

- 当前视频解析主链路已经基于 `uploaded_files`
- 自动打标一期必须对齐 `uploaded_files`
- 不建议把新功能继续挂到旧 `videos` 表

### 2. 模型 JSON 输出不稳定

- 必须强约束 schema
- 必须做后端兜底校验
- 必须保留原始响应摘要便于排错

### 3. 自由标签泛滥

- 一期先做阈值 + 人工确认
- 暂不做自动治理

### 4. 模板解析上下文变复杂

- 建议抽出独立上下文构造服务
- 避免继续把所有逻辑堆在 `"video_analysis.py"`

## 测试策略

### 后端

- 优先 `pytest`
- 每个批次都要有聚焦测试
- 自动打标服务与事务逻辑必须单独测

### 前端

- 优先 `vitest`
- 先测服务层与关键页面交互
- 避免写低价值快照测试

## 本次建议的第一批实际开工内容

如果现在就进入开发，建议先只做下面这批：

1. 批次 1：数据层打底
2. 批次 2：Schema 与 API 骨架
3. 批次 3：自动打标服务

这样能最快拿到一个后端可跑通的最小闭环：

- 能启动自动打标
- 能保存结构化结果
- 能查到结果详情

等这三批稳定后，再继续主标签同步和人工修订。
