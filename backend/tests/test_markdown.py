from pathlib import Path

from models.diff_models import BBox
from services.parser_service import ParsedDocument, ParsedParagraph, render_markdown, save_markdown


def _paragraph(text: str, page: int) -> ParsedParagraph:
    return ParsedParagraph(
        text=text,
        bbox=BBox(page=page, x0=0.0, y0=0.0, x1=10.0, y1=10.0),
    )


def test_render_markdown_prefers_existing_markdown_text():
    doc = ParsedDocument(
        pages=1,
        paragraphs=[_paragraph("ignored", 1)],
        tables=[],
        raw_json={},
        markdown_text="## Hello\n\nWorld",
    )

    text = render_markdown(doc, source_name="sample.pdf")
    assert text.startswith("# sample.pdf")
    assert "## Hello" in text


def test_save_markdown_fallback_from_paragraphs(tmp_path: Path):
    doc = ParsedDocument(
        pages=2,
        paragraphs=[_paragraph("Line A", 1), _paragraph("Line B", 2)],
        tables=[],
        raw_json={},
        markdown_text=None,
    )

    output = tmp_path / "result.md"
    saved = save_markdown(doc, output, source_name="demo.pdf")

    assert saved.exists()
    content = saved.read_text(encoding="utf-8")
    assert "# demo.pdf" in content
    assert "## Page 1" in content
    assert "Line A" in content
    assert "## Page 2" in content
    assert "Line B" in content
