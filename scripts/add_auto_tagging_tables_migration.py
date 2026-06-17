"""自动打标表结构迁移脚本

为正式标签体系与自动打标功能创建一期所需的数据表。
"""

from __future__ import annotations

import os
import sys
import sqlite3
from datetime import datetime
from pathlib import Path


def run_migration(database_path: Path) -> None:
    """执行 SQLite 迁移。"""
    conn = sqlite3.connect(str(database_path))
    try:
        cursor = conn.cursor()
        cursor.executescript(
            """
            CREATE TABLE IF NOT EXISTS video_auto_tag_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                user_id VARCHAR NOT NULL,
                video_file_id INTEGER NOT NULL,
                ai_config_id INTEGER NOT NULL,
                tag_group_ids JSON,
                prompt_version VARCHAR(50),
                prompt_content TEXT NOT NULL,
                transmission_method VARCHAR(20) NOT NULL DEFAULT 'url',
                video_url VARCHAR(1000),
                video_file_path VARCHAR(1000),
                status VARCHAR(20) NOT NULL DEFAULT 'pending',
                progress INTEGER NOT NULL DEFAULT 0,
                request_payload_summary JSON,
                raw_response TEXT,
                structured_summary JSON,
                result_metadata JSON,
                processing_time FLOAT,
                token_usage JSON,
                cost_estimate FLOAT,
                error_message TEXT,
                debug_info JSON,
                started_at VARCHAR(50),
                completed_at VARCHAR(50),
                is_active BOOLEAN NOT NULL DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS video_auto_tag_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                task_id INTEGER NOT NULL,
                tag_id INTEGER,
                tag_name VARCHAR(100) NOT NULL,
                tag_group_id INTEGER,
                tag_source VARCHAR(20) NOT NULL,
                match_type VARCHAR(20) NOT NULL DEFAULT 'ai_detected',
                confidence FLOAT NOT NULL DEFAULT 0,
                evidence_text TEXT,
                evidence_start_seconds FLOAT,
                evidence_end_seconds FLOAT,
                reason TEXT,
                is_promoted BOOLEAN NOT NULL DEFAULT 0,
                is_active BOOLEAN NOT NULL DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS uploaded_file_tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                video_file_id INTEGER NOT NULL,
                tag_id INTEGER,
                tag_name_snapshot VARCHAR(100) NOT NULL,
                source VARCHAR(20) NOT NULL,
                confidence FLOAT NOT NULL DEFAULT 1,
                auto_tag_task_id INTEGER,
                revision_id INTEGER,
                is_effective BOOLEAN NOT NULL DEFAULT 1,
                evidence_start_seconds FLOAT,
                evidence_end_seconds FLOAT,
                reason TEXT,
                created_by VARCHAR(20) NOT NULL DEFAULT 'system'
            );

            CREATE TABLE IF NOT EXISTS uploaded_file_tag_revisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                video_file_id INTEGER NOT NULL,
                base_task_id INTEGER,
                revision_number INTEGER NOT NULL DEFAULT 1,
                change_reason TEXT,
                created_by VARCHAR(20) NOT NULL
            );

            CREATE TABLE IF NOT EXISTS uploaded_file_tag_revision_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                revision_id INTEGER NOT NULL,
                tag_id INTEGER,
                tag_name VARCHAR(100) NOT NULL,
                action VARCHAR(20) NOT NULL,
                confidence FLOAT,
                note TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_video_auto_tag_tasks_video_file_id ON video_auto_tag_tasks(video_file_id);
            CREATE INDEX IF NOT EXISTS idx_video_auto_tag_tasks_status ON video_auto_tag_tasks(status);
            CREATE INDEX IF NOT EXISTS idx_video_auto_tag_items_task_id ON video_auto_tag_items(task_id);
            CREATE INDEX IF NOT EXISTS idx_uploaded_file_tags_video_file_id ON uploaded_file_tags(video_file_id);
            CREATE INDEX IF NOT EXISTS idx_uploaded_file_tags_effective ON uploaded_file_tags(video_file_id, is_effective);
            CREATE INDEX IF NOT EXISTS idx_uploaded_file_tag_revisions_video_file_id ON uploaded_file_tag_revisions(video_file_id);
            """
        )

        # 兼容已有 tags 表，按需补字段。
        existing_columns = {
            row[1]
            for row in cursor.execute("PRAGMA table_info('tags')").fetchall()
        }
        if "source_type" not in existing_columns:
            cursor.execute("ALTER TABLE tags ADD COLUMN source_type VARCHAR(20) NOT NULL DEFAULT 'library'")
        if "tag_group_id" not in existing_columns:
            cursor.execute("ALTER TABLE tags ADD COLUMN tag_group_id INTEGER")
        if "is_active" not in existing_columns:
            cursor.execute("ALTER TABLE tags ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT 1")

        conn.commit()
        print("Auto tagging migration completed successfully.")
    finally:
        conn.close()


def _resolve_database_path(argv: list[str]) -> Path:
    """解析数据库文件路径。

    使用方式：
    - python scripts/add_auto_tagging_tables_migration.py "path/to/db"
    - 不传参时：优先使用环境变量 DATABASE_URL（sqlite），否则回退到项目根目录下的 ai_media_expert.db / app.db
    """

    project_root = Path(__file__).resolve().parents[1]

    if len(argv) >= 2 and argv[1].strip():
        return Path(argv[1]).expanduser().resolve()

    database_url = os.getenv("DATABASE_URL", "").strip()
    if database_url.startswith("sqlite:///"):
        raw_path = database_url[len("sqlite:///") :]
        candidate = Path(raw_path)
        if not candidate.is_absolute():
            candidate = (project_root / candidate).resolve()
        return candidate

    preferred = project_root / "ai_media_expert.db"
    if preferred.exists():
        return preferred

    return project_root / "app.db"


if __name__ == "__main__":
    db_path = _resolve_database_path(sys.argv)
    print(
        f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
        f"Running auto-tagging migration on: {db_path}"
    )
    run_migration(db_path)
