import pandas as pd

from models.diff_models import BBox, DiffType
from services.diff_service import generate_diff_report
from services.parser_service import ParsedDocument, ParsedTable


def _table(data, page: int = 1) -> ParsedTable:
    return ParsedTable(
        dataframe=pd.DataFrame(data),
        bbox=BBox(page=page, x0=10.0, y0=10.0, x1=300.0, y1=180.0),
        caption="Premium Table",
        header_rows=1,
    )


def test_generate_diff_report_detects_table_cell_change():
    old_doc = ParsedDocument(
        pages=1,
        paragraphs=[],
        tables=[_table({"項目": ["保費"], "數值": ["0.216%"]})],
        raw_json={},
    )
    new_doc = ParsedDocument(
        pages=1,
        paragraphs=[],
        tables=[_table({"項目": ["保費"], "數值": ["0.195%"]})],
        raw_json={},
    )

    report = generate_diff_report(
        project_id="p001",
        old_filename="old.pdf",
        new_filename="new.pdf",
        old_doc=old_doc,
        new_doc=new_doc,
    )

    assert report.total_diffs == 1
    assert report.items[0].diff_type == DiffType.NUMBER_MODIFIED
    assert "Table 1" in report.items[0].context
