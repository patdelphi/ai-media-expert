# 基于视频解析结果的候选标签生成与采纳（2026-06-17）

## 背景

当前系统已具备：

- 基于上传视频的“自动打标”（读视频、输出结构化标签、同步当前标签、支持人工修订）
- “视频解析”（输出文本分析结果/摘要，并在解析 prompt 中复用当前标签与最近一次自动打标摘要）
- “视频打标”独立入口与标签集合/排除/恢复/排序/颜色区分等 UX

现在需要新增一条补充链路：**基于“已完成的 AI 视频解析结果”再调用一次 AI 生成候选标签**，并由用户勾选确认后采纳到当前标签集合。

## 目标

- 在解析结果页提供入口：从某次解析记录生成候选标签
- 候选标签需用户勾选确认后才入库
- 复用既有标签体系与修订接口，避免再造主标签表
- 候选标签可缓存到该次解析记录中，支持“重新生成”
- 采纳后的标签来源需可区分（用于颜色），但不在标签文字上增加“人工”等字样

## 非目标

- 不新增复杂标签关系、冲突规则引擎、统计看板
- 不要求把解析结果候选标签纳入“自动打标任务历史”中（除非后续明确要统一任务视图）
- 不做批量视频一键基于解析结果打标（一期仅单次解析记录）

## 术语与语义

- 解析记录：`video_analyses` 的一条记录（`analysis_id`）
- 候选标签：由“解析结果 + AI”生成的结构化标签候选列表，不直接进入当前标签集合
- 采纳：用户勾选候选标签后写入标签修订（`add` / `remove` / `adjust`）
- 标签来源（前端颜色用）：
  - `ai_auto`：上传视频自动打标生成
  - `manual_override`：人工修订新增/恢复
  - `ai_assisted`：基于解析结果生成并采纳（属于 AI 生成色，不显示文字标识）

## 总体方案（推荐：候选写入解析记录的 result_metadata）

### 核心思路

1. 在解析结果页点击“生成候选标签”
2. 后端读取该次解析记录的 `analysis_result / result_summary / 相关上下文`，再调用一次 AI，让模型输出稳定 JSON
3. 后端将候选标签写入该次解析记录的 `result_metadata.tag_candidates`（缓存）
4. 前端展示候选标签列表（checkbox），用户勾选后点击“采纳为标签”
5. 前端将勾选项转换为修订操作，调用既有修订接口写入当前标签集合

### 为什么不直接入库

- 避免“误标”污染当前标签
- 符合你确认的流程：候选必须人工确认

## 后端设计

### 1) 新增接口：生成候选标签

- Method：`POST`
- Path：`/api/v1/video-analysis/{analysis_id}/tag-candidates`
- Query：
  - `force: bool = false`（可选；为 true 时强制重新生成并覆盖缓存）
- 行为：
  - 解析记录不存在：`404`
  - 解析未完成或无可用内容：`400`
  - 若 `result_metadata.tag_candidates` 已存在且 `force=false`：直接返回缓存（幂等）
  - 否则调用 AI 生成候选，并写入 `result_metadata.tag_candidates`
- 返回：
  - `analysis_id`
  - `video_file_id`
  - `tag_candidates: TagCandidate[]`

#### TagCandidate 结构（稳定协议）

```json
{
  "tag_name": "品牌曝光",
  "confidence": 0.93,
  "reason": "解析结果中提到品牌出现频繁且有明确露出",
  "evidence_start_seconds": null,
  "evidence_end_seconds": null
}
```

字段说明：

- `tag_name`：必填，去除首尾空格后不能为空
- `confidence`：`0~1`，为空时后端兜底为 `0`
- `reason`：可选，过长需裁剪
- `evidence_*`：一期可为空（解析文本通常缺少时间轴证据）

### 2) 复用既有接口：采纳为当前标签

不新增采纳接口，直接复用：

- `POST /api/v1/uploaded-files/{video_file_id}/tags/revisions`

前端将候选标签转换为 `operations`：

- `add`：采纳标签
  - `tag_name`
  - `confidence`
  - `note`（建议包含来源：`analysis_id`）
  - `source`：`ai_assisted`
- `remove`：若你选择对已存在标签进行排除（一期可不做；默认只做 add/恢复）

### 3) 权限与归属

为避免“跨用户读取解析结果并生成候选标签”，新增接口需要对齐打标接口的 owner 校验：

- 管理员可访问任意
- 普通用户只能访问自己的解析记录与对应视频

### 4) AI 调用策略

- `temperature = 0`
- 强约束输出为 JSON
- 输出校验：
  - JSON parse
  - `tag_candidates` 是数组
  - 每项 `tag_name` 非空
  - `confidence` 兜底到 `0~1`
- 失败处理：
  - 生成失败返回 `500`，错误信息不包含敏感 prompt 细节
  - 不覆盖已有缓存（除非 `force=true` 且生成成功）

## 前端设计（解析结果页）

### 入口位置

在解析结果页（完成状态）新增区块：`解析结果打标`，包含：

- 按钮：`生成候选标签`（若已有缓存则显示 `重新生成`）
- 候选列表：checkbox + 标签名 + 百分比 + 理由（可折叠/省略）
- 操作：`采纳所选为标签`

### 去重/默认勾选策略

采纳前拉取当前标签集合：

- `GET /api/v1/uploaded-files/{video_file_id}/tags`

规则：

- 若候选标签已存在且当前生效：默认不勾选，并标记“已存在”（不可点或仍可点由前端策略决定）
- 若候选标签存在但已排除：允许勾选（采纳=恢复，本质走 `add`）
- 若候选标签不存在：默认勾选（可选）

### 颜色规则

采纳后写入标签时：

- `source = ai_assisted` → 前端按 AI 色展示（与 `ai_auto` 同色）
- `source = manual_override` → 手动修订色

## 数据结构变更

- `video_analyses.result_metadata`：新增约定字段 `tag_candidates`
- `uploaded_file_tags.source`：新增允许值 `ai_assisted`（并保持兼容已有 `ai_auto/manual_override`）

## 测试策略

### 后端（pytest）

- 生成候选标签接口：
  - 未完成解析返回 `400`
  - 已有缓存且 `force=false` 返回缓存
  - `force=true` 会刷新缓存
  - 权限校验：非本人访问拒绝
- 采纳来源写入：
  - 修订接口写入 `source=ai_assisted` 后，`GET /uploaded-files/{id}/tags` 返回正确来源

### 前端（vitest）

- 解析结果页显示“解析结果打标”区块（仅 completed）
- 点击“生成候选标签”调用新接口并渲染列表
- 勾选后点击采纳，调用修订接口，刷新标签集合
- 已存在标签默认不勾选/置灰逻辑

## 兼容性与回滚

- 新增能力不影响既有“上传视频自动打标”
- 若需要回滚：
  - 前端移除区块即可
  - 后端新接口可停止挂载或禁用
  - `result_metadata.tag_candidates` 字段可保留，不影响主流程
