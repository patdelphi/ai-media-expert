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
