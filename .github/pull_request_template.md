# PR Checklist

- [ ] 已说明本次变更影响的模块范围，并标注风险点
- [ ] 已运行后端测试：`python -m pytest -q`
- [ ] 已运行后端静态检查：`python -m compileall -q "app"`、`python -m flake8 "app"`、`python -m mypy "app/core/config.py" "app/services/download_api_client.py" --follow-imports=skip --ignore-missing-imports --disable-error-code=import-untyped`
- [ ] 已运行前端检查：`npm run lint`、`npm run build`
- [ ] 若前端测试已启用，已运行：`npm run test`
- [ ] 已确认权限影响：匿名 / 普通用户 / 管理员 的访问边界是否变化
- [ ] 已确认数据库影响：事务、结构、初始化数据或回滚路径是否变化
- [ ] 已确认文件影响：上传、删除、磁盘路径或补偿逻辑是否变化
- [ ] 已确认 API 兼容性：是否新增、废弃或调整了接口/字段
- [ ] 若涉及脚本/文档，已同步更新 `"Docs/"` 或 `"docs/"`
- [ ] 未提交敏感信息（token/cookie/密钥）
- [ ] 变更范围清晰，包含必要的测试或说明

