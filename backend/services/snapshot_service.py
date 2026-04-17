"""
Snapshot service: renders PDF pages with diff overlays and saves audit artifacts.

After each comparison, generates:
  runtime/snapshots/{task_id}/
    metadata.json          - comparison params, diff counts, timestamp
    old_page_{n}.png       - old PDF pages with magenta diff boxes drawn
    new_page_{n}.png       - new PDF pages with magenta diff boxes drawn
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import fitz  # PyMuPDF

from models.diff_models import DiffReport

_logger = logging.getLogger(__name__)

# Render resolution (DPI). 150 gives ~A4 at 1240×1754 px — readable, reasonable size.
_DEFAULT_DPI = 150
_SCALE = _DEFAULT_DPI / 72.0

# Magenta (R, G, B) in 0..1 range used for diff rectangle annotations
_DIFF_STROKE = (1.0, 0.0, 1.0)
_DIFF_FILL = (1.0, 0.0, 1.0)
_DIFF_OPACITY = 0.35


def generate_comparison_snapshots(
    task_id: str,
    old_pdf_path: str,
    new_pdf_path: str,
    report: DiffReport,
    snapshot_base_dir: Path,
) -> Path:
    """Render both PDFs with diff overlays and save PNGs + metadata JSON.

    Returns the path to the created snapshot directory.
    """
    snap_dir = snapshot_base_dir / task_id
    snap_dir.mkdir(parents=True, exist_ok=True)

    _render_pdf(old_pdf_path, report, bbox_side="old", snap_dir=snap_dir, prefix="old")
    _render_pdf(new_pdf_path, report, bbox_side="new", snap_dir=snap_dir, prefix="new")

    metadata = {
        "task_id": task_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "old_filename": report.old_filename,
        "new_filename": report.new_filename,
        "total_diffs": report.total_diffs,
        "render_dpi": _DEFAULT_DPI,
        "highlight_color": "#FF00FF",
    }
    (snap_dir / "metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    return snap_dir


def _render_pdf(
    pdf_path: str,
    report: DiffReport,
    bbox_side: str,
    snap_dir: Path,
    prefix: str,
) -> None:
    try:
        doc = fitz.open(pdf_path)
    except Exception as exc:
        _logger.warning("Snapshot: failed to open %s: %s", pdf_path, exc)
        return

    mat = fitz.Matrix(_SCALE, _SCALE)

    for page_idx in range(len(doc)):
        page_no = page_idx + 1
        page = doc[page_idx]
        page_height = page.rect.height

        # Collect diff bboxes for this page
        for item in report.items:
            bbox = item.old_bbox if bbox_side == "old" else item.new_bbox
            if not bbox or bbox.page != page_no:
                continue

            # Our BBox uses bottom-left origin; fitz uses top-left origin.
            fitz_rect = fitz.Rect(
                bbox.x0,
                page_height - bbox.y1,
                bbox.x1,
                page_height - bbox.y0,
            )
            if fitz_rect.is_empty or fitz_rect.is_infinite:
                continue

            try:
                annot = page.add_rect_annot(fitz_rect)
                annot.set_colors(stroke=_DIFF_STROKE, fill=_DIFF_FILL)
                annot.set_opacity(_DIFF_OPACITY)
                annot.update()
            except Exception as exc:
                _logger.debug(
                    "Snapshot: annot failed page=%d bbox=%s: %s", page_no, fitz_rect, exc
                )

        pix = page.get_pixmap(matrix=mat)
        pix.save(str(snap_dir / f"{prefix}_page_{page_no}.png"))

    doc.close()
