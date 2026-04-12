import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from config import settings
from models.diff_models import ChecklistItem, DiffReport

DEFAULT_PROJECT_ID = "default"
DEFAULT_PROJECT_NAME = "Default Project"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def get_connection(db_path: Path | None = None):
    path = db_path or settings.db_path
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def _ensure_column(conn: sqlite3.Connection, table: str, column: str, ddl: str) -> None:
    columns = conn.execute(f"PRAGMA table_info({table})").fetchall()
    names = {row[1] for row in columns}
    if column not in names:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}")


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS comparisons (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                old_filename TEXT NOT NULL,
                new_filename TEXT NOT NULL,
                old_file_path TEXT NOT NULL,
                new_file_path TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                diff_result_json TEXT,
                created_at TEXT NOT NULL,
                completed_at TEXT,
                FOREIGN KEY (project_id) REFERENCES projects(id)
            );

            CREATE TABLE IF NOT EXISTS review_logs (
                id TEXT PRIMARY KEY,
                comparison_id TEXT NOT NULL,
                diff_item_id TEXT NOT NULL,
                action TEXT NOT NULL,
                reviewer TEXT,
                note TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (comparison_id) REFERENCES comparisons(id)
            );

            CREATE TABLE IF NOT EXISTS checklists (
                id TEXT PRIMARY KEY,
                comparison_id TEXT NOT NULL,
                items_json TEXT NOT NULL,
                imported_at TEXT NOT NULL,
                FOREIGN KEY (comparison_id) REFERENCES comparisons(id)
            );
            """
        )
        _ensure_column(conn, "comparisons", "error_message", "TEXT")
        _ensure_column(conn, "comparisons", "old_markdown_path", "TEXT")
        _ensure_column(conn, "comparisons", "new_markdown_path", "TEXT")


def create_project(name: str) -> dict[str, str]:
    now = utc_now_iso()
    project_id = str(uuid.uuid4())
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO projects (id, name, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (project_id, name, now, now),
        )
    return {"id": project_id, "name": name, "created_at": now, "updated_at": now}


def project_exists(project_id: str) -> bool:
    with get_connection() as conn:
        row = conn.execute("SELECT 1 FROM projects WHERE id = ?", (project_id,)).fetchone()
    return bool(row)


def ensure_default_project() -> str:
    now = utc_now_iso()
    with get_connection() as conn:
        row = conn.execute("SELECT id FROM projects WHERE id = ?", (DEFAULT_PROJECT_ID,)).fetchone()
        if row:
            return DEFAULT_PROJECT_ID
        conn.execute(
            "INSERT INTO projects (id, name, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (DEFAULT_PROJECT_ID, DEFAULT_PROJECT_NAME, now, now),
        )
    return DEFAULT_PROJECT_ID


def list_projects() -> list[dict[str, str]]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, name, created_at, updated_at FROM projects ORDER BY created_at DESC"
        ).fetchall()
    return [dict(row) for row in rows]


def create_comparison(
    comparison_id: str,
    project_id: str,
    old_filename: str,
    new_filename: str,
    old_file_path: str,
    new_file_path: str,
) -> None:
    now = utc_now_iso()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO comparisons (
                id, project_id, old_filename, new_filename,
                old_file_path, new_file_path, status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                comparison_id,
                project_id,
                old_filename,
                new_filename,
                old_file_path,
                new_file_path,
                "pending",
                now,
            ),
        )


def update_comparison_status(
    comparison_id: str,
    status: str,
    *,
    error_message: str | None = None,
    completed: bool = False,
) -> None:
    with get_connection() as conn:
        completed_at = utc_now_iso() if completed else None
        conn.execute(
            """
            UPDATE comparisons
            SET status = ?, error_message = ?, completed_at = COALESCE(?, completed_at)
            WHERE id = ?
            """,
            (status, error_message, completed_at, comparison_id),
        )


def save_diff_report(comparison_id: str, report: DiffReport) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE comparisons
            SET status = 'done',
                diff_result_json = ?,
                error_message = NULL,
                completed_at = ?
            WHERE id = ?
            """,
            (report.model_dump_json(), utc_now_iso(), comparison_id),
        )


def save_comparison_report_state(comparison_id: str, report: DiffReport) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE comparisons
            SET diff_result_json = ?
            WHERE id = ?
            """,
            (report.model_dump_json(), comparison_id),
        )


def save_markdown_paths(
    comparison_id: str,
    *,
    old_markdown_path: str | None,
    new_markdown_path: str | None,
) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE comparisons
            SET old_markdown_path = ?, new_markdown_path = ?
            WHERE id = ?
            """,
            (old_markdown_path, new_markdown_path, comparison_id),
        )


def get_markdown_paths(comparison_id: str) -> dict[str, str | None] | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT old_markdown_path, new_markdown_path FROM comparisons WHERE id = ?",
            (comparison_id,),
        ).fetchone()
    if not row:
        return None
    return {
        "old_markdown_path": row["old_markdown_path"],
        "new_markdown_path": row["new_markdown_path"],
    }


def save_comparison_error(comparison_id: str, error_message: str) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE comparisons
            SET status = 'error',
                error_message = ?,
                completed_at = ?
            WHERE id = ?
            """,
            (error_message, utc_now_iso(), comparison_id),
        )


def get_comparison(comparison_id: str) -> dict | None:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM comparisons WHERE id = ?", (comparison_id,)).fetchone()
    return dict(row) if row else None


def get_comparison_report(comparison_id: str) -> DiffReport | None:
    row = get_comparison(comparison_id)
    if not row or not row.get("diff_result_json"):
        return None
    payload = row["diff_result_json"]
    if isinstance(payload, str):
        data = json.loads(payload)
    else:
        data = payload
    return DiffReport.model_validate(data)


def list_project_comparisons(project_id: str) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, project_id, old_filename, new_filename, status,
                   created_at, completed_at, error_message,
                   old_markdown_path, new_markdown_path
            FROM comparisons
            WHERE project_id = ?
            ORDER BY created_at DESC
            """,
            (project_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def add_review_log(
    comparison_id: str,
    diff_item_id: str,
    action: str,
    reviewer: str | None,
    note: str | None,
) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO review_logs (
                id, comparison_id, diff_item_id, action, reviewer, note, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid.uuid4()),
                comparison_id,
                diff_item_id,
                action,
                reviewer,
                note,
                utc_now_iso(),
            ),
        )


def get_latest_review_actions(comparison_id: str) -> dict[str, str]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT diff_item_id, action
            FROM review_logs
            WHERE comparison_id = ?
            ORDER BY created_at DESC, rowid DESC
            """,
            (comparison_id,),
        ).fetchall()

    latest: dict[str, str] = {}
    for row in rows:
        diff_item_id = row["diff_item_id"]
        if diff_item_id not in latest:
            latest[diff_item_id] = row["action"]
    return latest


def get_review_counts(comparison_id: str) -> dict[str, int]:
    latest = get_latest_review_actions(comparison_id)
    counts = {"confirmed": 0, "flagged": 0, "skipped": 0}
    for action in latest.values():
        if action in counts:
            counts[action] += 1
    return counts


def get_review_logs(comparison_id: str) -> list[dict[str, str | None]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, comparison_id, diff_item_id, action, reviewer, note, created_at
            FROM review_logs
            WHERE comparison_id = ?
            ORDER BY created_at ASC, rowid ASC
            """,
            (comparison_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def save_checklist(comparison_id: str, items: list[ChecklistItem]) -> None:
    payload = json.dumps([item.model_dump(mode="json") for item in items], ensure_ascii=False)
    imported_at = utc_now_iso()
    checklist_id = str(uuid.uuid4())
    with get_connection() as conn:
        existing = conn.execute(
            "SELECT id FROM checklists WHERE comparison_id = ?",
            (comparison_id,),
        ).fetchone()
        if existing:
            conn.execute(
                """
                UPDATE checklists
                SET items_json = ?, imported_at = ?
                WHERE comparison_id = ?
                """,
                (payload, imported_at, comparison_id),
            )
            return

        conn.execute(
            """
            INSERT INTO checklists (id, comparison_id, items_json, imported_at)
            VALUES (?, ?, ?, ?)
            """,
            (checklist_id, comparison_id, payload, imported_at),
        )


def get_checklist(comparison_id: str) -> list[ChecklistItem]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT items_json FROM checklists WHERE comparison_id = ?",
            (comparison_id,),
        ).fetchone()
    if not row:
        return []
    payload = json.loads(row["items_json"])
    return [ChecklistItem.model_validate(item) for item in payload]
