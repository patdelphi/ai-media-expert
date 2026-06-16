"""本地管理员密码重置脚本

用途：
  - 在本地 SQLite 数据库中，将指定用户的 hashed_password 重置为新密码（会使用项目内的密码哈希算法）。

注意：
  - 仅用于本地开发/演示环境
  - 会对数据库执行写操作（事务内）
"""

from __future__ import annotations

import argparse
import sqlite3
from typing import Iterable

from app.core.security import get_password_hash


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Reset local admin passwords in SQLite DB.")
    parser.add_argument(
        "--db",
        default="ai_media_expert.db",
        help="SQLite DB file path (default: ai_media_expert.db).",
    )
    parser.add_argument("--password", required=True, help="New password.")
    parser.add_argument(
        "--user-ids",
        nargs="+",
        type=int,
        required=True,
        help="Target user ids.",
    )
    return parser.parse_args()


def chunk_placeholders(count: int) -> str:
    return ",".join(["?"] * count)


def reset_passwords(db_path: str, user_ids: Iterable[int], password: str) -> int:
    hashed_password = get_password_hash(password)
    ids = list(user_ids)
    placeholders = chunk_placeholders(len(ids))
    sql = f"UPDATE users SET hashed_password=? WHERE id IN ({placeholders})"

    conn = sqlite3.connect(db_path)
    try:
        conn.execute("BEGIN")
        cur = conn.cursor()
        cur.execute(sql, [hashed_password, *ids])
        updated = int(cur.rowcount or 0)
        conn.commit()
        return updated
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def main() -> None:
    args = parse_args()
    updated = reset_passwords(args.db, args.user_ids, args.password)
    print(f"updated_rows={updated}")


if __name__ == "__main__":
    main()
