from pathlib import Path

import pandas as pd

from models.diff_models import CheckStatus, ChecklistItem, DiffItem

_COLUMN_ALIASES = {
    "item_id": ["item_id", "項目id", "項目編號", "id"],
    "check_type": ["check_type", "核對類型", "類型"],
    "search_keyword": ["search_keyword", "搜尋關鍵字", "關鍵字"],
    "expected_old": ["expected_old", "期望舊值", "舊值"],
    "expected_new": ["expected_new", "期望新值", "新值"],
    "page_hint": ["page_hint", "頁面提示", "頁碼", "page"],
}


def _pick_column(columns: list[str], aliases: list[str]) -> str | None:
    lowered = {c.lower(): c for c in columns}
    for alias in aliases:
        if alias.lower() in lowered:
            return lowered[alias.lower()]
    return None


def _read_file(file_path: str) -> pd.DataFrame:
    path = Path(file_path)
    suffix = path.suffix.lower()
    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(path)
    return pd.read_csv(path)


def import_checklist(file_path: str) -> list[ChecklistItem]:
    df = _read_file(file_path)
    columns = df.columns.tolist()

    resolved = {
        key: _pick_column(columns, aliases)
        for key, aliases in _COLUMN_ALIASES.items()
    }

    items: list[ChecklistItem] = []
    for idx, row in df.iterrows():
        item_id = str(row.get(resolved["item_id"], f"C{idx + 1:03d}")).strip()
        check_type = str(row.get(resolved["check_type"], "general")).strip()
        keyword = str(row.get(resolved["search_keyword"], "")).strip()
        expected_old = row.get(resolved["expected_old"]) if resolved["expected_old"] else None
        expected_new = row.get(resolved["expected_new"]) if resolved["expected_new"] else None
        page_hint = row.get(resolved["page_hint"]) if resolved["page_hint"] else None

        items.append(
            ChecklistItem(
                item_id=item_id,
                check_type=check_type,
                search_keyword=keyword,
                expected_old=None if pd.isna(expected_old) else str(expected_old),
                expected_new=None if pd.isna(expected_new) else str(expected_new),
                page_hint=None if pd.isna(page_hint) else int(page_hint),
            )
        )

    return items


def auto_match(checklist: list[ChecklistItem], diff_items: list[DiffItem]) -> list[ChecklistItem]:
    updated: list[ChecklistItem] = []

    for item in checklist:
        keyword = item.search_keyword.lower().strip()
        matched = None

        for diff in diff_items:
            haystack = " ".join(filter(None, [diff.old_value, diff.new_value, diff.context])).lower()
            if keyword and keyword in haystack:
                matched = diff
                break

        if not matched:
            item.status = CheckStatus.MISSING
            updated.append(item)
            continue

        item.matched_diff_id = matched.id
        old_ok = item.expected_old is None or (matched.old_value or "") == item.expected_old
        new_ok = item.expected_new is None or (matched.new_value or "") == item.expected_new

        if old_ok and new_ok:
            item.status = CheckStatus.CONFIRMED
        else:
            item.status = CheckStatus.ANOMALY

        updated.append(item)

    return updated
