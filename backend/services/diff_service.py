import re
from difflib import SequenceMatcher
from itertools import zip_longest

from models.diff_models import DiffItem, DiffType
from services.parser_service import ParsedDocument, ParsedParagraph, ParsedTable

NUMBER_PATTERN = re.compile(r"\d+(?:\.\d+)?%?")


def _normalize(text: str) -> str:
    return " ".join(text.split())


def _contains_number(text: str | None) -> bool:
    if not text:
        return False
    return bool(NUMBER_PATTERN.search(text))


def _guess_diff_type(old_value: str | None, new_value: str | None) -> DiffType:
    if old_value and new_value:
        if _contains_number(old_value) or _contains_number(new_value):
            return DiffType.NUMBER_MODIFIED
        return DiffType.TEXT_MODIFIED
    if old_value and not new_value:
        return DiffType.DELETED
    return DiffType.ADDED


def diff_paragraphs(
    old_paragraphs: list[ParsedParagraph],
    new_paragraphs: list[ParsedParagraph],
) -> list[DiffItem]:
    old_texts = [_normalize(p.text) for p in old_paragraphs]
    new_texts = [_normalize(p.text) for p in new_paragraphs]

    matcher = SequenceMatcher(a=old_texts, b=new_texts)
    diff_items: list[DiffItem] = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue

        if tag == "replace":
            old_slice = old_paragraphs[i1:i2]
            new_slice = new_paragraphs[j1:j2]
            paired_count = min(len(old_slice), len(new_slice))

            for offset in range(paired_count):
                old_item = old_slice[offset]
                new_item = new_slice[offset]
                confidence = SequenceMatcher(
                    a=_normalize(old_item.text), b=_normalize(new_item.text)
                ).ratio()
                diff_items.append(
                    DiffItem(
                        id="",
                        diff_type=_guess_diff_type(old_item.text, new_item.text),
                        old_value=old_item.text,
                        new_value=new_item.text,
                        old_bbox=old_item.bbox,
                        new_bbox=new_item.bbox,
                        context=f"Page {new_item.bbox.page}",
                        confidence=confidence,
                    )
                )

            for old_extra in old_slice[paired_count:]:
                diff_items.append(
                    DiffItem(
                        id="",
                        diff_type=DiffType.DELETED,
                        old_value=old_extra.text,
                        new_value=None,
                        old_bbox=old_extra.bbox,
                        new_bbox=None,
                        context=f"Page {old_extra.bbox.page}",
                        confidence=0.7,
                    )
                )

            for new_extra in new_slice[paired_count:]:
                diff_items.append(
                    DiffItem(
                        id="",
                        diff_type=DiffType.ADDED,
                        old_value=None,
                        new_value=new_extra.text,
                        old_bbox=None,
                        new_bbox=new_extra.bbox,
                        context=f"Page {new_extra.bbox.page}",
                        confidence=0.7,
                    )
                )

        if tag == "delete":
            for old_item in old_paragraphs[i1:i2]:
                diff_items.append(
                    DiffItem(
                        id="",
                        diff_type=DiffType.DELETED,
                        old_value=old_item.text,
                        new_value=None,
                        old_bbox=old_item.bbox,
                        new_bbox=None,
                        context=f"Page {old_item.bbox.page}",
                        confidence=0.75,
                    )
                )

        if tag == "insert":
            for new_item in new_paragraphs[j1:j2]:
                diff_items.append(
                    DiffItem(
                        id="",
                        diff_type=DiffType.ADDED,
                        old_value=None,
                        new_value=new_item.text,
                        old_bbox=None,
                        new_bbox=new_item.bbox,
                        context=f"Page {new_item.bbox.page}",
                        confidence=0.75,
                    )
                )

    return diff_items


def align_table_headers(old_df, new_df) -> tuple[dict, dict]:
    old_cols = {col: col for col in old_df.columns}
    new_cols = {col: col for col in new_df.columns}
    return old_cols, new_cols


def _normalize_cell(value) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return "" if text.lower() == "nan" else _normalize(text)


def _table_context(table: ParsedTable, index: int) -> str:
    caption = (table.caption or "").strip()
    if caption:
        return f"Table {index} ({caption}) on Page {table.bbox.page}"
    return f"Table {index} on Page {table.bbox.page}"


def _table_dataframe_rows(table: ParsedTable) -> list[list[str]]:
    df = table.dataframe.copy()
    if df.empty and len(df.columns) == 0:
        return []

    df.columns = [_normalize_cell(col) for col in df.columns]
    rows: list[list[str]] = []
    header = [_normalize_cell(col) for col in df.columns]
    if any(header):
        rows.append(header)

    for _, row in df.iterrows():
        rows.append([_normalize_cell(value) for value in row.tolist()])
    return rows


def diff_tables(old_tables: list[ParsedTable], new_tables: list[ParsedTable]) -> list[DiffItem]:
    diff_items: list[DiffItem] = []

    for table_index, (old_table, new_table) in enumerate(
        zip_longest(old_tables, new_tables),
        start=1,
    ):
        if old_table and not new_table:
            context = _table_context(old_table, table_index)
            diff_items.append(
                DiffItem(
                    id="",
                    diff_type=DiffType.DELETED,
                    old_value=f"{context} removed",
                    new_value=None,
                    old_bbox=old_table.bbox,
                    new_bbox=None,
                    context=context,
                    confidence=0.8,
                )
            )
            continue

        if new_table and not old_table:
            context = _table_context(new_table, table_index)
            diff_items.append(
                DiffItem(
                    id="",
                    diff_type=DiffType.ADDED,
                    old_value=None,
                    new_value=f"{context} added",
                    old_bbox=None,
                    new_bbox=new_table.bbox,
                    context=context,
                    confidence=0.8,
                )
            )
            continue

        if not old_table or not new_table:
            continue

        context = _table_context(new_table, table_index)
        old_rows = _table_dataframe_rows(old_table)
        new_rows = _table_dataframe_rows(new_table)

        for row_index, (old_row, new_row) in enumerate(
            zip_longest(old_rows, new_rows, fillvalue=[]),
            start=1,
        ):
            for col_index, (old_cell, new_cell) in enumerate(
                zip_longest(old_row, new_row, fillvalue=""),
                start=1,
            ):
                if old_cell == new_cell:
                    continue

                diff_items.append(
                    DiffItem(
                        id="",
                        diff_type=_guess_diff_type(old_cell or None, new_cell or None),
                        old_value=old_cell or None,
                        new_value=new_cell or None,
                        old_bbox=old_table.bbox if old_cell else None,
                        new_bbox=new_table.bbox if new_cell else None,
                        context=f"{context} / row {row_index} col {col_index}",
                        confidence=0.72,
                    )
                )

    return diff_items


def diff_pixels(
    old_pdf_path: str,
    new_pdf_path: str,
    threshold: int = 30,
    min_area: int = 200,
) -> list[DiffItem]:
    # Pixel fallback intentionally disabled in base MVP.
    _ = (old_pdf_path, new_pdf_path, threshold, min_area)
    return []


def _sort_key(item: DiffItem) -> tuple[int, float]:
    bbox = item.new_bbox or item.old_bbox
    if not bbox:
        return (99999, 0.0)
    return (bbox.page, -bbox.y1)


def merge_diff_results(
    text_diffs: list[DiffItem],
    table_diffs: list[DiffItem],
    pixel_diffs: list[DiffItem] | None,
) -> list[DiffItem]:
    merged = [*text_diffs, *table_diffs]
    if pixel_diffs:
        merged.extend(pixel_diffs)

    merged = sorted(merged, key=_sort_key)
    for index, item in enumerate(merged, start=1):
        item.id = f"d{index:03d}"
    return merged


def generate_diff_report(
    project_id: str,
    old_filename: str,
    new_filename: str,
    old_doc: ParsedDocument,
    new_doc: ParsedDocument,
):
    from datetime import datetime, timezone

    from models.diff_models import DiffReport

    text_diffs = diff_paragraphs(old_doc.paragraphs, new_doc.paragraphs)
    table_diffs = diff_tables(old_doc.tables, new_doc.tables)
    merged_items = merge_diff_results(text_diffs, table_diffs, pixel_diffs=None)

    return DiffReport(
        project_id=project_id,
        old_filename=old_filename,
        new_filename=new_filename,
        created_at=datetime.now(timezone.utc).isoformat(),
        total_diffs=len(merged_items),
        items=merged_items,
    )
