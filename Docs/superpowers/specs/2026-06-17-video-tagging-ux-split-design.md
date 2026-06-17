﻿# 视频打标独立入口与 UX 优化设计（2026-06-17）

## 背景

当前“自动打标”相关能力集成在 `"/video/analysis"` 的 Step2 中，导致：

- 打标与解析耦合，用户心智不清晰（选视频后只能“下一步”进入解析流程）
- 标签集合/排除/恢复等交互需要更明确的入口与状态表达
- 打标页面 UX 信息密度偏高，不利于频繁操作

## 目标

1. 选择视频后提供两个入口：
   - 视频解析（保留原“下一步”链路）
   - 视频打标（独立为单独功能，但仍在同一页面内切换模式）
2. 标签 Chip 交互统一为一个 `x`：
   - 当前生效标签：点击 `x` -> 确认“是否排除” -> 是：提交 `remove`
   - 已排除标签：点击 `x` -> 确认“是否恢复” -> 是：提交 `add`
3. 优化打标 UX：更清晰的结构、更少噪音、常用操作更聚焦

## 非目标

- 不新增数据库表/迁移（仅前端结构调整与复用既有修订接口）
- 不引入复杂标签冲突规则/层级关系/统计看板

## 术语与语义

### 历史标签集合（前端展示）

- 由后端接口 `GET "/uploaded-files/{video_file_id}/tags"` 返回
- 每条标签包含：
  - `tag_name`
  - `confidence`：历史聚合后的最高置信度
  - `is_effective`：是否当前生效（已排除为 false）

### 百分比显示（%）

- 展示值：`Math.round(confidence * 100)`
- 置信度来源规则：
  - 自动打标：模型返回的 `confidence`
  - 人工新增/恢复：默认按 `confidence=1`（即 100%）提交

## 页面信息架构（同页模式切换）

### Step1：选择视频

当 `selectedVideo` 已选择时，在原来的“下一步”旁新增入口按钮：

- 主按钮：`视频解析`（原“下一步”语义不变，进入解析 Step2/3/4/5）
- 次按钮：`视频打标`（进入打标模式，不进入解析步骤）

### 打标模式（独立功能区）

建议将打标功能抽成独立组件（避免 `VideoAnalysis.tsx` 继续膨胀）：

- `VideoTaggingPanel`
  - 顶部：当前视频标题/文件名 + 返回选择视频
  - 操作区（固定在顶部或首屏）：开始自动打标、刷新、人工新增标签
  - 内容区：
    1) 历史标签集合（含状态与排除/恢复）
    2) 自动打标历史（默认仅展开最近一次，可手动展开查看）
    3) 修订历史（版本列表）

## 交互细节

### 标签 Chip

- 展示结构（单行）：
  - `tag_name` + `XX%` +（仅已排除显示 badge）+ `x`
- `x` 点击逻辑：
  - 若 `is_effective=true`：
    - 弹框：是否排除？
    - 确认后调用修订接口提交 `remove`
  - 若 `is_effective=false`：
    - 弹框：是否恢复？
    - 确认后调用修订接口提交 `add`

### 展示规则（已落地）

- 标签来源仅用颜色区分：
  - `source="ai_auto"`：AI 自动打标
  - `source="manual_override"`：人工修订（新增/恢复）
- 排序规则：
  - 先 AI（生效）→ 后人工修订（生效）→ 最后已排除
  - 组内按拼音顺序

### 修订接口约定

- URL：`POST "/uploaded-files/{video_file_id}/tags/revisions"`
- 排除 payload：
  - `operations: [{ action: "remove", tag_name, note }]`
- 恢复 payload：
  - `operations: [{ action: "add", tag_name, confidence: 1, note }]`

## API 使用清单（不新增后端改动为前提）

- 历史标签集合：`GET "/uploaded-files/{video_file_id}/tags"`
- 修订：`POST "/uploaded-files/{video_file_id}/tags/revisions"`
- 修订历史：`GET "/uploaded-files/{video_file_id}/tags/revisions"`
- 自动打标任务：
  - 启动：`POST "/video-auto-tags/start"`
  - 任务详情：`GET "/video-auto-tags/{task_id}"`
  - 历史列表：`GET "/video-auto-tags/video-files/{video_file_id}/tasks"`

## 测试策略

### 前端（vitest）

1. Step1 选中视频后展示两个入口按钮
2. 进入打标模式后展示关键区块（历史标签集合/自动打标历史/修订历史）
3. 点击当前生效标签的 `x` 会调用 `window.confirm` 并触发 `remove`
4. 点击已排除标签的 `x` 会调用 `window.confirm` 并触发 `add`

### 后端（pytest）

不新增接口时不增加测试；若为配合前端需要调整接口响应字段，则补对应回归。

## 回滚方案

- 前端入口按钮/打标模式为纯 UI 行为，可通过回退前端改动恢复原入口
- 后端接口不变更时不存在数据迁移回滚问题
