#!/usr/bin/env python3
"""
为 ai_configs 表添加 upload_api_key 字段。

该字段仅用于 Qwen 文件上传时的百炼上传专用 API Key。
"""

import sys
from pathlib import Path

from sqlalchemy import text

# 添加项目根目录到 Python 路径
sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import SessionLocal


def add_upload_api_key_column() -> bool:
    """为 ai_configs 表添加 upload_api_key 字段。"""
    print("开始添加 upload_api_key 字段...")
    db = SessionLocal()

    try:
        result = db.execute(text("""
            SELECT COUNT(*) AS count
            FROM pragma_table_info('ai_configs')
            WHERE name = 'upload_api_key'
        """))
        count = result.fetchone()[0]

        if count > 0:
            print("✅ upload_api_key 字段已存在，无需添加")
            return True

        db.execute(text("""
            ALTER TABLE ai_configs
            ADD COLUMN upload_api_key VARCHAR(500)
        """))
        db.commit()
        print("✅ 成功添加 upload_api_key 字段")
        return True
    except Exception as exc:
        print(f"❌ 添加字段失败: {exc}")
        db.rollback()
        return False
    finally:
        db.close()


def verify_migration() -> bool:
    """验证迁移结果。"""
    print("\n开始验证迁移结果...")
    db = SessionLocal()

    try:
        result = db.execute(text("""
            SELECT name, type, "notnull", dflt_value
            FROM pragma_table_info('ai_configs')
            WHERE name = 'upload_api_key'
        """))
        field_info = result.fetchone()
        if not field_info:
            print("❌ 未找到 upload_api_key 字段")
            return False

        name, field_type, not_null, default_value = field_info
        print(f"✅ 字段信息: {name} {field_type} (NOT NULL: {bool(not_null)}, DEFAULT: {default_value})")
        return True
    except Exception as exc:
        print(f"❌ 验证失败: {exc}")
        return False
    finally:
        db.close()


def main() -> bool:
    """执行迁移。"""
    print("🚀 开始 ai_configs.upload_api_key 字段迁移\n")

    if not add_upload_api_key_column():
        print("❌ 字段添加失败，终止迁移")
        return False

    if not verify_migration():
        print("❌ 迁移验证失败")
        return False

    print("\n🎉 ai_configs.upload_api_key 字段迁移完成！")
    print("💡 该字段仅用于 Qwen 文件上传专用 Key，不参与模型解析")
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
