from pathlib import Path

from config import settings
from models.database import (
    add_review_log,
    create_comparison,
    ensure_default_project,
    get_checklist,
    get_review_counts,
    get_review_logs,
    init_db,
    save_checklist,
)
from models.diff_models import CheckStatus, ChecklistItem


def _prepare_temp_db(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(settings, "db_path", tmp_path / "app.db")


def _create_comparison_record(comparison_id: str) -> None:
    create_comparison(
        comparison_id=comparison_id,
        project_id=ensure_default_project(),
        old_filename="old.pdf",
        new_filename="new.pdf",
        old_file_path="/tmp/old.pdf",
        new_file_path="/tmp/new.pdf",
    )


def test_review_counts_use_latest_action(monkeypatch, tmp_path: Path):
    _prepare_temp_db(monkeypatch, tmp_path)
    init_db()
    comparison_id = "cmp-review"
    _create_comparison_record(comparison_id)

    add_review_log(comparison_id, "d001", "confirmed", "alice", None)
    add_review_log(comparison_id, "d001", "flagged", "bob", "recheck")
    add_review_log(comparison_id, "d002", "confirmed", "alice", None)

    counts = get_review_counts(comparison_id)

    assert counts["confirmed"] == 1
    assert counts["flagged"] == 1
    assert counts["skipped"] == 0


def test_checklist_round_trip_persists_to_sqlite(monkeypatch, tmp_path: Path):
    _prepare_temp_db(monkeypatch, tmp_path)
    init_db()
    comparison_id = "cmp-checklist"
    _create_comparison_record(comparison_id)

    save_checklist(
        comparison_id,
        [
            ChecklistItem(
                item_id="C001",
                check_type="number",
                search_keyword="保單利率",
                expected_old="0.216%",
                expected_new="0.195%",
                status=CheckStatus.CONFIRMED,
                matched_diff_id="d001",
                note="verified",
            )
        ],
    )

    items = get_checklist(comparison_id)

    assert len(items) == 1
    assert items[0].item_id == "C001"
    assert items[0].status == CheckStatus.CONFIRMED
    assert items[0].matched_diff_id == "d001"


def test_review_logs_return_full_timeline(monkeypatch, tmp_path: Path):
    _prepare_temp_db(monkeypatch, tmp_path)
    init_db()
    comparison_id = "cmp-log"
    _create_comparison_record(comparison_id)

    add_review_log(comparison_id, "d001", "flagged", "alice", "needs check")
    add_review_log(comparison_id, "d001", "confirmed", "bob", "approved")

    logs = get_review_logs(comparison_id)

    assert len(logs) == 2
    assert logs[0]["action"] == "flagged"
    assert logs[0]["reviewer"] == "alice"
    assert logs[1]["action"] == "confirmed"
    assert logs[1]["note"] == "approved"
