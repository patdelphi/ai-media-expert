# 优化方案（以去除无用/冗余代码为重点）
 
> 说明：本文件用于后续逐项执行与验收（先保证“可运行与一致性”，再做清理与重构）。任何删除/移动文件操作，执行前都会单独向你确认。
 
## 目标
 
- 让后端/前端/异步任务的启动方式一致、可复现
- 清理重复实现与“备份目录/调试脚本/重复路由”
- 让测试能够稳定跑起来（至少覆盖关键路径）
 
## 优先级任务清单（建议执行顺序）
 
### P0：把工程跑通（不做大重构）
 
- [x] 对齐 Python 打包入口：修复 `"pyproject.toml"` 的 `"app.main:main"` 不存在问题（已新增 `"app/main.py"`）
- [x] 对齐 pytest 收集路径：让测试只跑稳定用例（已改为收集 `"app/tests"`，并修复现有测试失败）
- [x] 对齐 Celery 入口与 broker：代码与 `"docker-compose.yml"` 统一（已新增 `"app/tasks/celery.py"` 并改为读取配置）
 
### P1：去除明显冗余（最小风险）
 
- [x] 统一 API 路由汇总：在 `"app/api/v1/__init__.py"` 与 `"app/api/v1/api.py"` 中保留一份“唯一真源”，另一份删除或改为薄包装（已收敛到 `"app/api/v1/api.py"`）
- [x] 清理/隔离前端备份目录：评估 `"frontend_backup/"` 是否仍被使用，若不需要则移动到归档或删除（已删除）
- [x] 清理重复/试验性上传接口：合并 `"simple_upload" / "minimal_upload" / "test_upload"` 等，保留 1 套正式 API（已统一使用 `"/simple-upload/simple"`，并从路由移除 `"/minimal"` 与 `"/test-upload"`）
 
### P2：结构性清理（需要测试兜底）
 
- [x] 盘点根目录 `"test_*.py"` / `"debug_*.py"`：标记为手工工具并从 pytest 默认收集中排除（已新增清单 `"scripts/manual_tools.md"`，并在 pytest 忽略）
- [x] 去除未使用依赖：基于导入与运行链路，拆分“必需依赖”和“可选依赖”（已拆分到 optional-dependencies：`ai/ui/metrics/migrations/...`）
- [x] 文档口径统一：补齐启动端口/是否挂载 UI 等不一致描述（已更新 `"README.md"`/`"README_SERVICES.md"`/`"Docs/README.md"`）

### P2：清理无用 debug / test 脚本（待你确认后执行）

> 说明：以下文件均不在 `"app/tests"` 内，不会被 pytest 默认执行；它们主要是“手工调试/临时验证”。本轮目标是：把明显无用/重复/高风险的脚本删除或迁移出仓库根目录，减少噪音与误用风险。任何删除操作会在执行前再次向你确认。

#### 建议删除（根目录）

- [ ] `"debug_api.py"`
- [ ] `"debug_videos_api.py"`
- [ ] `"debug_download_api.py"`（包含手工构造 token/外部请求倾向，误用风险更高）
- [ ] `"debug_realtime_api.py"`
- [ ] `"debug_frontend_issue.py"`
- [ ] `"test_curl_debug.py"`
- [ ] `"test_direct_api.py"`
- [ ] `"test_exception_middleware.py"`
- [ ] `"test_simple_upload_debug.py"`
- [ ] `"test_download_api_direct.py"`
- [ ] `"test_download_api_final.py"`

#### 建议删除（抖音专项手工验证，根目录）

- [ ] `"test_douyin_abogus.py"`
- [ ] `"test_douyin_cookie.py"`
- [ ] `"test_douyin_debug.py"`
- [ ] `"test_douyin_direct.py"`
- [ ] `"test_douyin_headers.py"`
- [ ] `"test_douyin_id_extraction.py"`
- [ ] `"test_douyin_latest.py"`
- [ ] `"test_douyin_new_link.py"`
- [ ] `"test_douyin_recent.py"`
- [ ] `"test_douyin_response.py"`
- [ ] `"test_douyin_short_url.py"`
- [ ] `"test_douyin_simple.py"`
- [ ] `"test_douyin_video_fetch.py"`
- [ ] `"test_douyin_with_new_cookie.py"`

#### 建议保留或迁移（再确认）

- [ ] `"test_video_download.py"`（在 `"TEST_REPORT.md"` 中有引用；如果你不再需要手工测试报告，可一起删除并同步文档）
- [ ] `"test_frontend_integration.py"`（在 `"TEST_REPORT.md"` 中有引用；同上）
- [ ] `"test_websocket.py"`（手工验证 ws）
- [ ] `"test_hybrid_crawler.py"` / `"test_new_crawlers.py"`（手工验证爬虫/适配器导入与行为）

#### 其它位置（可选清理）

- [ ] `"scripts/test_video_info.py"`
- [ ] `"scripts/test_exif_time.py"`
- [ ] `"scripts/test_mp4_time.py"`
- [ ] `"scripts/test_filename_time.py"`（演示脚本）
- [ ] `"frontend/public/test_page.html"`（手工页面，可能会进入前端构建产物）

#### 需要同步更新的文档（跟随删除/迁移自动更新）

- [ ] `"scripts/manual_tools.md"`：删掉已移除文件条目
- [ ] `"TEST_REPORT.md"`：若删除 `"test_video_download.py"` 或 `"test_frontend_integration.py"`，需要更新报告口径或删除报告
 
### P3：质量与CI（保证长期可维护）
 
- [x] 新功能/重构补齐测试：以 API（下载/分析/上传）为主线增加单测/集成测试（已补 `/health`、`/`、简化上传、下载任务 CRUD）
- [x] 增加类型检查与 lint（仅幂等校验）：保证本地/CI 一致（已加入 CI：`compileall + flake8(E9/F*) + pytest`）
 
## 执行约束
 
- 所有 git 操作（commit/push/merge/pull）都需要你确认后才会执行
- 任何删除文件/目录操作都需要你确认后才会执行

## P1 盘点结果（待你确认后执行清理）

- `"frontend_backup/"`：当前代码中未发现引用，建议删除或移动到归档目录（需要你确认“删除/移动”）。
- 上传相关接口目前存在多套并行实现：
  - 正式分片上传：`"app/api/v1/endpoints/video_upload.py"`（`"/upload/*"`）
  - 简化上传：`"app/api/v1/endpoints/simple_upload.py"`（`"/simple-upload/simple"`）
  - 最小上传：`"app/api/v1/endpoints/minimal_upload.py"`（已删除）
  - 测试上传：`"app/api/v1/endpoints/test_upload.py"`（已删除）
- 建议口径：
  - 保留：分片上传 +（可选）简化上传
  - 移除或仅开发环境保留：最小上传、测试上传（需要你确认“删除/移动/是否保留为 debug”）

---

## 2026-06-15 项目全面探查计划（待确认执行）

### 关键假设

- 本轮先做审查，不修改业务代码、配置、数据库和运行数据。
- 不访问外网、不下载或安装依赖、不调用外部 API。
- 不执行删除、Git commit/push/pull/merge 等操作。
- 保留当前工作区已有未提交改动，不覆盖或回退用户修改。

### 审查范围

- [x] 盘点目录结构、入口、依赖、配置、文档及 Git 跟踪状态。
- [x] 检查后端错误：异常处理、事务、鉴权、数据一致性、文件路径和异步任务。
- [x] 检查前端错误：类型问题、状态同步、接口契约、重复组件和构建配置。
- [x] 检查冗余：重复路由、废弃脚本、缓存/产物、未引用模块、重复文档和历史遗留入口。
- [x] 检查工程质量：测试布局、CI/PR checks、lint/type-check/build 配置是否一致。
- [x] 执行白名单幂等校验：后端 test/lint/type-check/compile，前端 lint/type-check/build（仅执行项目已有命令）。
- [x] 输出按 P0/P1/P2 分级的问题清单，包含文件位置、影响、证据和最小修改建议。

### 完成标准

- 每个问题均有可定位的文件或命令证据，不仅给出泛化建议。
- 明确区分“确定错误”“潜在风险”“可选优化”“可删除候选”。
- 删除候选只列清单，不执行删除。
- 汇总已执行验证、失败项、未执行项及原因。

### 审查产物

- 详细报告：`"Docs/project-audit-2026-06-15.md"`
- 结论：发现 6 项 P0、6 项 P1，以及若干冗余和维护性优化项。
- 未执行：业务代码修复、文件删除、数据库操作、外网访问、依赖安装和 Git 写操作。

---

## 2026-06-15 分阶段优化计划

- [x] 确认采用安全优先、分阶段优化策略。
- [x] 仅输出计划，不修改业务代码。
- [x] 生成详细实施计划：`"Docs/optimization-plan-2026-06-15.md"`。
- [ ] 阶段 0：建立安全基线。
- [ ] 阶段 1：P0 安全修复。
- [ ] 阶段 2：接口收敛与旧实现隔离。
- [ ] 阶段 3：正确性与事务一致性。
- [ ] 阶段 4：质量门禁与测试体系。
- [ ] 阶段 5：冗余清理。
- [ ] 阶段 6：性能与长期维护。

> 后续只有在用户明确要求开始实施后，才逐阶段执行；删除、安装依赖、数据库操作和 Git 操作仍需单独确认。

---

## 2026-06-15 执行清单（来源：`"docs/optimization-plan-2026-06-15.md"`）

### 阶段 0：建立安全基线（测试先行，不改实现）

- [ ] Task 0.1：新增 `"app/tests/test_route_security_baseline.py"`（枚举高风险路由，断言匿名访问应为 401/403；现状下预期先失败）
- [ ] Task 0.1：新增/更新 `"docs/changelog.md"`（记录“建立安全基线测试”的变更点；不创建 `"Docs/"` 目录，沿用现有 `"docs/"`）
- [ ] Task 0.2：新增 `"app/tests/conftest.py"` + `"app/tests/factories.py"`（测试数据库/用户/管理员/认证头/临时上传目录工厂）
- [ ] Task 0.2：增加“不会触碰真实 `"ai_media_expert.db"` 与 `"uploads"`”的保护性断言/隔离机制

### 阶段 0 验证（白名单幂等校验）

- [ ] `python -m compileall -q "app"`
- [ ] `python -m flake8 "app"`
- [ ] `python -m pytest -q`

### 阶段 1 前置确认（先不执行）

- [ ] 是否允许安装前端依赖（例如 DOMPurify）
- [ ] 管理员是否允许跨用户“查看/删除”文件（两项可分开）
