import os
import subprocess
import tempfile
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import pandas as pd

from models.diff_models import BBox

DEFAULT_PAGE_WIDTH_PT = 595.0
DEFAULT_PAGE_HEIGHT_PT = 842.0


@dataclass
class ParsedParagraph:
    text: str
    bbox: BBox
    style: str | None = None


@dataclass
class ParsedTable:
    dataframe: pd.DataFrame
    bbox: BBox
    caption: str | None = None
    header_rows: int = 1


@dataclass
class ParsedDocument:
    pages: int
    paragraphs: list[ParsedParagraph]
    tables: list[ParsedTable]
    raw_json: dict
    markdown_text: str | None = None


def _to_bottom_left_bbox(page_number: int, page_height: float, block_bbox: list[float]) -> BBox:
    x0, y0_top, x1, y1_top = block_bbox
    y0 = page_height - y1_top
    y1 = page_height - y0_top
    return BBox(page=page_number, x0=x0, y0=y0, x1=x1, y1=y1)


def _synthetic_paragraph_bbox(page: int, line_index: int, total_lines: int) -> BBox:
    line_height = DEFAULT_PAGE_HEIGHT_PT / max(total_lines, 1)
    y_top = line_index * line_height
    y_bottom = min((line_index + 1) * line_height, DEFAULT_PAGE_HEIGHT_PT)
    return BBox(
        page=page,
        x0=0.0,
        y0=DEFAULT_PAGE_HEIGHT_PT - y_bottom,
        x1=DEFAULT_PAGE_WIDTH_PT,
        y1=DEFAULT_PAGE_HEIGHT_PT - y_top,
    )


def _bbox_from_docling(
    *,
    page_no: int,
    bbox_obj,
    page_height: float,
) -> BBox:
    x0 = float(getattr(bbox_obj, "l", 0.0))
    y_top = float(getattr(bbox_obj, "t", 0.0))
    x1 = float(getattr(bbox_obj, "r", 0.0))
    y_bottom = float(getattr(bbox_obj, "b", 0.0))
    coord_origin = str(getattr(getattr(bbox_obj, "coord_origin", None), "value", "")).upper()

    if "TOP" in coord_origin:
        y0 = page_height - y_bottom
        y1 = page_height - y_top
    else:
        y0 = y_bottom
        y1 = y_top
    return BBox(page=page_no, x0=x0, y0=y0, x1=x1, y1=y1)


@lru_cache(maxsize=1)
def _get_docling_converter():
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions, TesseractCliOcrOptions
    from docling.document_converter import DocumentConverter, PdfFormatOption

    lang_env = os.getenv("OCR_LANGS", "eng")
    langs = [lang.strip() for lang in lang_env.split(",") if lang.strip()]

    options = PdfPipelineOptions()
    options.do_ocr = True
    options.ocr_options = TesseractCliOcrOptions(
        lang=langs or ["eng"],
        force_full_page_ocr=True,
    )

    return DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=options),
        }
    )


def _parse_via_docling(pdf_path: Path) -> ParsedDocument:
    converter = _get_docling_converter()
    result = converter.convert(str(pdf_path))

    doc_obj = result.document
    page_heights = {}
    for page_no, page_item in getattr(doc_obj, "pages", {}).items():
        size = getattr(page_item, "size", None)
        if size and hasattr(size, "height"):
            page_heights[int(page_no)] = float(size.height)

    paragraphs: list[ParsedParagraph] = []
    for entry in doc_obj.iterate_items():
        item = entry[0]
        prov = getattr(item, "prov", None)
        if not prov:
            continue

        text = ""
        for attr in ("text", "orig", "md_content", "content"):
            value = getattr(item, attr, None)
            if isinstance(value, str) and value.strip():
                text = value.strip()
                break
        if not text:
            continue

        first_prov = prov[0]
        page_no = int(getattr(first_prov, "page_no", 1))
        page_height = page_heights.get(page_no, DEFAULT_PAGE_HEIGHT_PT)

        if type(item).__name__ == "TableItem":
            # Extract individual cells instead of the whole table string
            data = getattr(item, "data", None)
            cells = getattr(data, "table_cells", []) if data else []
            for cell in cells:
                cell_text = str(getattr(cell, "text", "")).strip()
                if not cell_text:
                    continue
                c_prov = getattr(cell, "prov", None)
                if c_prov:
                    c_bbox_obj = getattr(c_prov[0], "bbox", None)
                    if c_bbox_obj:
                        c_page_no = int(getattr(c_prov[0], "page_no", page_no))
                        c_page_height = page_heights.get(c_page_no, DEFAULT_PAGE_HEIGHT_PT)
                        cell_bbox = _bbox_from_docling(page_no=c_page_no, bbox_obj=c_bbox_obj, page_height=c_page_height)
                        paragraphs.append(ParsedParagraph(text=cell_text, bbox=cell_bbox))
            continue

        bbox_obj = getattr(first_prov, "bbox", None)
        if not bbox_obj:
            continue

        bbox = _bbox_from_docling(page_no=page_no, bbox_obj=bbox_obj, page_height=page_height)
        paragraphs.append(ParsedParagraph(text=text, bbox=bbox))

    tables: list[ParsedTable] = []
    for table_item in getattr(doc_obj, "tables", []):
        prov = getattr(table_item, "prov", None)
        if not prov:
            continue
        first_prov = prov[0]
        page_no = int(getattr(first_prov, "page_no", 1))
        bbox_obj = getattr(first_prov, "bbox", None)
        if not bbox_obj:
            continue
        page_height = page_heights.get(page_no, DEFAULT_PAGE_HEIGHT_PT)
        table_bbox = _bbox_from_docling(page_no=page_no, bbox_obj=bbox_obj, page_height=page_height)

        dataframe = pd.DataFrame()
        try:
            dataframe = table_item.export_to_dataframe(doc=doc_obj)
        except Exception:
            try:
                dataframe = table_item.export_to_dataframe()
            except Exception:
                dataframe = pd.DataFrame()

        caption = getattr(table_item, "caption_text", None)
        tables.append(
            ParsedTable(
                dataframe=dataframe,
                bbox=table_bbox,
                caption=caption if isinstance(caption, str) and caption.strip() else None,
                header_rows=1,
            )
        )

    markdown = ""
    if hasattr(doc_obj, "export_to_markdown"):
        markdown = doc_obj.export_to_markdown() or ""

    if not paragraphs and markdown:
        # Safety net: if structured items are missing, keep minimal text lines.
        lines = [line.strip() for line in markdown.splitlines() if line.strip()]
        for line_index, line in enumerate(lines):
            paragraphs.append(
                ParsedParagraph(
                    text=line,
                    bbox=_synthetic_paragraph_bbox(1, line_index, len(lines)),
                )
            )

    return ParsedDocument(
        pages=max(len(getattr(doc_obj, "pages", {})), 1),
        paragraphs=paragraphs,
        tables=tables,
        raw_json={
            "engine": "docling",
            "raw_preview": markdown[:3000],
            "paragraph_count": len(paragraphs),
            "table_count": len(tables),
        },
        markdown_text=markdown or None,
    )


def _parse_via_fitz(pdf_path: Path) -> ParsedDocument:
    import fitz

    paragraphs: list[ParsedParagraph] = []
    raw_pages: list[dict] = []

    with fitz.open(pdf_path) as doc:
        for page_index, page in enumerate(doc, start=1):
            page_dict = page.get_text("dict")
            raw_pages.append(page_dict)
            page_height = float(page.rect.height)

            for block in page_dict.get("blocks", []):
                if block.get("type") != 0:
                    continue

                lines = block.get("lines", [])
                parts: list[str] = []
                for line in lines:
                    for span in line.get("spans", []):
                        text = str(span.get("text", "")).strip()
                        if text:
                            parts.append(text)

                joined = " ".join(parts).strip()
                if not joined:
                    continue

                paragraph_bbox = _to_bottom_left_bbox(
                    page_number=page_index,
                    page_height=page_height,
                    block_bbox=block.get("bbox", [0, 0, 0, 0]),
                )
                paragraphs.append(ParsedParagraph(text=joined, bbox=paragraph_bbox))

        markdown_lines = [paragraph.text for paragraph in paragraphs]
        markdown = "\n\n".join(markdown_lines)
        return ParsedDocument(
            pages=len(doc),
            paragraphs=paragraphs,
            tables=[],
            raw_json={"engine": "pymupdf", "pages": raw_pages},
            markdown_text=markdown or None,
        )


def _parse_via_pdftotext(pdf_path: Path) -> ParsedDocument:
    command = ["pdftotext", "-layout", "-enc", "UTF-8", str(pdf_path), "-"]
    proc = subprocess.run(command, capture_output=True, text=True, check=True)
    text = proc.stdout or ""

    pages_raw = text.split("\f")
    if pages_raw and not pages_raw[-1].strip():
        pages_raw = pages_raw[:-1]

    paragraphs: list[ParsedParagraph] = []
    for page_index, page_text in enumerate(pages_raw, start=1):
        lines = [line.rstrip() for line in page_text.splitlines() if line.strip()]
        for line_index, line in enumerate(lines):
            paragraphs.append(
                ParsedParagraph(
                    text=line.strip(),
                    bbox=_synthetic_paragraph_bbox(page_index, line_index, len(lines)),
                )
            )

    return ParsedDocument(
        pages=max(len(pages_raw), 1),
        paragraphs=paragraphs,
        tables=[],
        raw_json={"engine": "pdftotext", "raw_preview": text[:3000]},
        markdown_text=text or None,
    )


def _parse_via_ocr(pdf_path: Path, dpi: int = 200) -> ParsedDocument:
    with tempfile.TemporaryDirectory(prefix="pdf_ocr_") as temp_dir:
        prefix = Path(temp_dir) / "page"
        subprocess.run(
            ["pdftoppm", "-r", str(dpi), "-png", str(pdf_path), str(prefix)],
            check=True,
            capture_output=True,
            text=True,
        )

        images = sorted(Path(temp_dir).glob("page-*.png"))
        if not images:
            raise RuntimeError("No page images generated for OCR")

        paragraphs: list[ParsedParagraph] = []
        raw_snippets: list[str] = []
        for page_idx, image in enumerate(images, start=1):
            proc = subprocess.run(
                ["tesseract", str(image), "stdout", "-l", "eng", "--psm", "6"],
                check=True,
                capture_output=True,
                text=True,
            )
            ocr_text = proc.stdout or ""
            raw_snippets.append(ocr_text[:1200])
            lines = [line.strip() for line in ocr_text.splitlines() if line.strip()]
            for line_index, line in enumerate(lines):
                paragraphs.append(
                    ParsedParagraph(
                        text=line,
                        bbox=_synthetic_paragraph_bbox(page_idx, line_index, len(lines)),
                    )
                )

        markdown = "\n\n".join(paragraph.text for paragraph in paragraphs)
        return ParsedDocument(
            pages=len(images),
            paragraphs=paragraphs,
            tables=[],
            raw_json={"engine": "ocr_tesseract", "raw_preview": "\n".join(raw_snippets)[:3000]},
            markdown_text=markdown or None,
        )


def parse_pdf(file_path: str) -> ParsedDocument:
    pdf_path = Path(file_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {file_path}")

    errors: list[str] = []

    try:
        return _parse_via_docling(pdf_path)
    except ModuleNotFoundError as exc:
        errors.append(f"docling unavailable: {exc}")
    except Exception as exc:  # pragma: no cover - parser runtime errors
        errors.append(f"docling failed: {exc}")

    try:
        return _parse_via_fitz(pdf_path)
    except ModuleNotFoundError as exc:
        errors.append(f"pymupdf unavailable: {exc}")
    except Exception as exc:  # pragma: no cover - parser runtime errors
        errors.append(f"pymupdf failed: {exc}")

    try:
        doc = _parse_via_pdftotext(pdf_path)
        if doc.paragraphs:
            return doc
        errors.append("pdftotext extracted no text")
    except FileNotFoundError as exc:
        errors.append(f"pdftotext binary missing: {exc}")
    except Exception as exc:  # pragma: no cover - parser runtime errors
        errors.append(f"pdftotext failed: {exc}")

    try:
        return _parse_via_ocr(pdf_path)
    except FileNotFoundError as exc:
        errors.append(f"ocr dependencies missing: {exc}")
    except Exception as exc:  # pragma: no cover - parser runtime errors
        errors.append(f"ocr failed: {exc}")

    detail = " | ".join(errors) if errors else "unknown parser error"
    raise RuntimeError(f"Failed to parse PDF '{file_path}': {detail}")


def parse_pdf_fallback(file_path: str) -> ParsedDocument:
    """Fallback parser hook using pdftotext directly."""
    return _parse_via_pdftotext(Path(file_path))


def render_markdown(document: ParsedDocument, source_name: str | None = None) -> str:
    if document.markdown_text and document.markdown_text.strip():
        if source_name:
            return f"# {source_name}\n\n{document.markdown_text.strip()}\n"
        return document.markdown_text.strip() + "\n"

    lines: list[str] = []
    if source_name:
        lines.append(f"# {source_name}")
        lines.append("")

    by_page: dict[int, list[str]] = {}
    for paragraph in document.paragraphs:
        by_page.setdefault(paragraph.bbox.page, []).append(paragraph.text.strip())

    for page in sorted(by_page):
        lines.append(f"## Page {page}")
        lines.append("")
        for paragraph_text in by_page[page]:
            if paragraph_text:
                lines.append(paragraph_text)
                lines.append("")

    return "\n".join(lines).strip() + "\n"


def save_markdown(document: ParsedDocument, output_path: Path, source_name: str | None = None) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    content = render_markdown(document, source_name=source_name)
    output_path.write_text(content, encoding="utf-8")
    return output_path
