# 手工脚本清单（不纳入自动化测试）

> 说明：根目录的 `"test_*.py"` / `"debug_*.py"` 为手工调试/验证脚本，默认不参与 pytest 收集；建议逐步迁移到 `"scripts/"` 下并按用途分组。

## 根目录脚本

### debug

- `"debug_api.py"`
- `"debug_download_api.py"`
- `"debug_frontend_issue.py"`
- `"debug_realtime_api.py"`
- `"debug_videos_api.py"`

### test

- `"test_curl_debug.py"`
- `"test_direct_api.py"`
- `"test_douyin_abogus.py"`
- `"test_douyin_cookie.py"`
- `"test_douyin_debug.py"`
- `"test_douyin_direct.py"`
- `"test_douyin_headers.py"`
- `"test_douyin_id_extraction.py"`
- `"test_douyin_latest.py"`
- `"test_douyin_new_link.py"`
- `"test_douyin_recent.py"`
- `"test_douyin_response.py"`
- `"test_douyin_short_url.py"`
- `"test_douyin_simple.py"`
- `"test_douyin_video_fetch.py"`
- `"test_douyin_with_new_cookie.py"`
- `"test_download_api_direct.py"`
- `"test_download_api_final.py"`
- `"test_exception_middleware.py"`
- `"test_frontend_integration.py"`
- `"test_hybrid_crawler.py"`
- `"test_new_crawlers.py"`
- `"test_simple_upload_debug.py"`
- `"test_video_download.py"`
- `"test_websocket.py"`
