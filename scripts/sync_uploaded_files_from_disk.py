from __future__ import annotations

import os
import sqlite3
from pathlib import Path


def sync_uploaded_files_from_disk(
    db_path: Path = Path("ai_media_expert.db"),
    uploads_dir: Path = Path("uploads/videos"),
    user_id: int = 1,
) -> None:
    if not db_path.exists():
        raise FileNotFoundError(f"db not found: {db_path}")
    if not uploads_dir.exists():
        raise FileNotFoundError(f"uploads dir not found: {uploads_dir}")

    video_files = sorted([p for p in uploads_dir.glob("*.mp4") if p.is_file()])
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT id, saved_filename, file_path, file_size, user_id FROM uploaded_files")
    rows = cur.fetchall()

    by_saved: dict[str, sqlite3.Row] = {}
    for r in rows:
        if r["saved_filename"]:
            by_saved[str(r["saved_filename"])] = r

    inserted = 0
    updated = 0
    for f in video_files:
        filename = f.name
        rel_path = str(Path("uploads/videos") / filename)
        size = f.stat().st_size

        existing = by_saved.get(filename)
        if existing:
            if existing["file_path"] != rel_path or int(existing["file_size"] or 0) != size or str(existing["user_id"] or "") != str(user_id):
                cur.execute(
                    "UPDATE uploaded_files SET file_path = ?, file_size = ?, user_id = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (rel_path, size, user_id, existing["id"]),
                )
                updated += 1
            continue

        cur.execute(
            "INSERT INTO uploaded_files (original_filename, saved_filename, file_size, content_type, file_path, user_id) VALUES (?, ?, ?, ?, ?, ?)",
            (filename, filename, size, "video/mp4", rel_path, user_id),
        )
        inserted += 1

    cur.execute("SELECT id, file_path, file_size FROM uploaded_files WHERE file_size > 0 AND file_path IS NOT NULL")
    candidates = cur.fetchall()
    orphaned = 0
    for r in candidates:
        try:
            if not r["file_path"] or not os.path.isfile(r["file_path"]) or os.path.getsize(r["file_path"]) <= 0:
                cur.execute("UPDATE uploaded_files SET file_size = 0, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (r["id"],))
                orphaned += 1
        except OSError:
            cur.execute("UPDATE uploaded_files SET file_size = 0, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (r["id"],))
            orphaned += 1

    conn.commit()
    conn.close()

    print(f"Disk videos: {len(video_files)}")
    print(f"uploaded_files inserted: {inserted}")
    print(f"uploaded_files updated: {updated}")
    print(f"uploaded_files orphaned(file missing -> file_size=0): {orphaned}")


if __name__ == "__main__":
    sync_uploaded_files_from_disk()
