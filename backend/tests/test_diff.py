from models.diff_models import BBox, DiffType
from services.diff_service import generate_diff_report
from services.parser_service import ParsedDocument, ParsedParagraph


def _paragraph(text: str, page: int = 1, y0: float = 100.0, y1: float = 120.0) -> ParsedParagraph:
    return ParsedParagraph(
        text=text,
        bbox=BBox(page=page, x0=10.0, y0=y0, x1=200.0, y1=y1),
    )


def test_generate_diff_report_detects_number_change():
    old_doc = ParsedDocument(
        pages=1,
        paragraphs=[_paragraph("Monthly fee 0.216%")],
        tables=[],
        raw_json={},
    )
    new_doc = ParsedDocument(
        pages=1,
        paragraphs=[_paragraph("Monthly fee 0.195%")],
        tables=[],
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
    assert report.items[0].id == "d001"


def test_generate_diff_report_detects_added_paragraph():
    old_doc = ParsedDocument(
        pages=1,
        paragraphs=[_paragraph("Clause A")],
        tables=[],
        raw_json={},
    )
    new_doc = ParsedDocument(
        pages=1,
        paragraphs=[_paragraph("Clause A"), _paragraph("Clause B", page=1, y0=80, y1=95)],
        tables=[],
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
    assert report.items[0].diff_type == DiffType.ADDED
