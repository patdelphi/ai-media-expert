# 手工脚本清单（不纳入自动化测试）

> 说明：根目录的 `"test_*.py"` / `"debug_*.py"` 为手工调试/验证脚本，默认不参与 pytest 收集；建议逐步迁移到 `"scripts/"` 下并按用途分组。

## 根目录脚本

### debug

- （已清理：重复/过时的 debug 脚本已删除）

### test

- `"test_frontend_integration.py"`
- `"test_hybrid_crawler.py"`
- `"test_new_crawlers.py"`
- `"test_video_download.py"`
- `"test_websocket.py"`

## 已清理

- 已删除未纳入自动化、且无业务引用的抖音专项实验脚本：`"test_douyin_*.py"`
- 已删除时间提取演示脚本：`"scripts/test_video_info.py"`、`"scripts/test_exif_time.py"`、`"scripts/test_mp4_time.py"`、`"scripts/test_filename_time.py"`
