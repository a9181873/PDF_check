import re
import unicodedata
from dataclasses import dataclass
from difflib import SequenceMatcher
from itertools import zip_longest

from models.diff_models import DiffItem, DiffType, BBox
from services.parser_service import ParsedDocument, ParsedParagraph, ParsedTable

NUMBER_PATTERN = re.compile(r"\d+(?:\.\d+)?%?")


def _normalize(text: str) -> str:
    return " ".join(text.split())

def refine_bbox_for_text(full_text: str, full_bbox, start_idx: int, end_idx: int):
    if not full_text or end_idx <= start_idx or not full_bbox:
        return full_bbox
    height = full_bbox.y1 - full_bbox.y0
    if height > 25:
        # Multiline, interpolation will be stretched
        return full_bbox
    length = len(full_text)
    frac_start = start_idx / length
    frac_end = end_idx / length
    width = full_bbox.x1 - full_bbox.x0
    from models.diff_models import BBox
    return BBox(
        page=full_bbox.page,
        x0=full_bbox.x0 + width * frac_start,
        y0=full_bbox.y0,
        x1=full_bbox.x0 + width * frac_end,
        y1=full_bbox.y1
    )

def _contains_number(text: str | None) -> bool:
    if not text:
        return False
    return bool(NUMBER_PATTERN.search(text))

def is_meaningful_diff(old_val: str | None, new_val: str | None) -> bool:
    v1 = unicodedata.normalize('NFKC', (old_val or "").strip())
    v2 = unicodedata.normalize('NFKC', (new_val or "").strip())
    return v1 != v2


def _guess_diff_type(old_value: str | None, new_value: str | None) -> DiffType:
    if old_value and new_value:
        if _contains_number(old_value) or _contains_number(new_value):
            return DiffType.NUMBER_MODIFIED
        return DiffType.TEXT_MODIFIED
    if old_value and not new_value:
        return DiffType.DELETED
    return DiffType.ADDED


@dataclass
class TextToken:
    text: str
    paragraph: ParsedParagraph
    start_char_idx: int
    end_char_idx: int

def _tokenize_paragraphs(paragraphs: list[ParsedParagraph]) -> list[TextToken]:
    tokens = []
    for p in paragraphs:
        for match in re.finditer(r'\S+', p.text):
            tokens.append(TextToken(
                text=match.group(0),
                paragraph=p,
                start_char_idx=match.start(),
                end_char_idx=match.end()
            ))
    return tokens

def _group_tokens_by_paragraph(tokens: list[TextToken]) -> list[list[TextToken]]:
    if not tokens:
        return []
    groups = []
    current_group = [tokens[0]]
    for t in tokens[1:]:
        if t.paragraph is current_group[-1].paragraph:
            current_group.append(t)
        else:
            groups.append(current_group)
            current_group = [t]
    groups.append(current_group)
    return groups

def _get_bbox_for_token_group(group: list[TextToken]) -> tuple[str, BBox | None]:
    if not group:
        return "", None
    p = group[0].paragraph
    full_text = p.text
    full_bbox = p.bbox
    start_idx = group[0].start_char_idx
    end_idx = group[-1].end_char_idx
    
    sub_text = full_text[start_idx:end_idx]
    
    if not full_bbox:
        return sub_text, None
        
    height = full_bbox.y1 - full_bbox.y0
    if height > 35:
        # multiline wrap heavily compromises linear interpolation
        return sub_text, full_bbox
        
    length = max(len(full_text), 1)
    frac_start = start_idx / length
    frac_end = end_idx / length
    width = full_bbox.x1 - full_bbox.x0
    refined_bbox = BBox(
        page=full_bbox.page,
        x0=full_bbox.x0 + width * frac_start,
        y0=full_bbox.y0,
        x1=full_bbox.x0 + width * frac_end,
        y1=full_bbox.y1
    )
    return sub_text, refined_bbox

def diff_paragraphs(
    old_paragraphs: list[ParsedParagraph],
    new_paragraphs: list[ParsedParagraph],
) -> list[DiffItem]:
    old_tokens = _tokenize_paragraphs(old_paragraphs)
    new_tokens = _tokenize_paragraphs(new_paragraphs)

    old_words = [unicodedata.normalize('NFKC', t.text) for t in old_tokens]
    new_words = [unicodedata.normalize('NFKC', t.text) for t in new_tokens]

    matcher = SequenceMatcher(a=old_words, b=new_words, autojunk=False)
    diff_items: list[DiffItem] = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue

        old_slice = old_tokens[i1:i2]
        new_slice = new_tokens[j1:j2]
        
        old_groups = _group_tokens_by_paragraph(old_slice)
        new_groups = _group_tokens_by_paragraph(new_slice)
        
        paired_count = max(len(old_groups), len(new_groups))
        
        for idx in range(paired_count):
            og = old_groups[idx] if idx < len(old_groups) else []
            ng = new_groups[idx] if idx < len(new_groups) else []
            
            old_str, old_bbox = _get_bbox_for_token_group(og)
            new_str, new_bbox = _get_bbox_for_token_group(ng)
            
            if not is_meaningful_diff(old_str, new_str):
                continue
                
            dtype = _guess_diff_type(old_str if old_str else None, new_str if new_str else None)
            
            page_ctx = []
            if og and og[0].paragraph.bbox: page_ctx.append(f"Page {og[0].paragraph.bbox.page}")
            if ng and ng[0].paragraph.bbox: page_ctx.append(f"Page {ng[0].paragraph.bbox.page}")
            ctx = " / ".join(set(page_ctx)) if page_ctx else "N/A"
            
            diff_items.append(
                DiffItem(
                    id="",
                    diff_type=dtype,
                    old_value=old_str if old_str else None,
                    new_value=new_str if new_str else None,
                    old_bbox=old_bbox,
                    new_bbox=new_bbox,
                    context=ctx,
                    confidence=0.85,
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

                if old_cell and new_cell:
                    char_matcher = SequenceMatcher(a=old_cell, b=new_cell)
                    for c_tag, c_i1, c_i2, c_j1, c_j2 in char_matcher.get_opcodes():
                        if c_tag == "equal":
                            continue
                        
                        old_sub = old_cell[c_i1:c_i2] if c_i1 < c_i2 else None
                        new_sub = new_cell[c_j1:c_j2] if c_j1 < c_j2 else None
                        if not is_meaningful_diff(old_sub, new_sub):
                            continue
                        
                        # Use 0-based indexing to find cell bboxes
                        o_cell_bbox = old_table.cell_bboxes.get((row_index - 1, col_index - 1))
                        n_cell_bbox = new_table.cell_bboxes.get((row_index - 1, col_index - 1))

                        old_sub_bbox = refine_bbox_for_text(old_cell, o_cell_bbox, c_i1, c_i2) if o_cell_bbox and old_sub else None
                        new_sub_bbox = refine_bbox_for_text(new_cell, n_cell_bbox, c_j1, c_j2) if n_cell_bbox and new_sub else None

                        diff_items.append(
                            DiffItem(
                                id="",
                                diff_type=_guess_diff_type(old_sub, new_sub),
                                old_value=old_sub,
                                new_value=new_sub,
                                old_bbox=old_sub_bbox,
                                new_bbox=new_sub_bbox,
                                context=f"{context} / row {row_index} col {col_index}",
                                confidence=0.72,
                            )
                        )
                else:
                    if not is_meaningful_diff(old_cell, new_cell):
                        continue

                    o_cell_bbox = old_table.cell_bboxes.get((row_index - 1, col_index - 1))
                    n_cell_bbox = new_table.cell_bboxes.get((row_index - 1, col_index - 1))

                    diff_items.append(
                        DiffItem(
                            id="",
                            diff_type=_guess_diff_type(old_cell or None, new_cell or None),
                            old_value=old_cell or None,
                            new_value=new_cell or None,
                            old_bbox=o_cell_bbox,
                            new_bbox=n_cell_bbox,
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
