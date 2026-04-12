from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from api.task_store import TASK_STORE
from config import settings
from models.database import get_checklist, get_comparison_report, get_review_counts, get_review_logs
from services.export_service import (
    export_annotated_pdf,
    export_review_excel,
    export_review_log_csv,
    export_review_log_json,
    export_review_report_pdf,
)

router = APIRouter(prefix="/api/export", tags=["export"])


def _resolve_new_pdf_path(task_id: str, filename: str) -> Path | None:
    direct = settings.new_upload_dir / f"{task_id}_{Path(filename).name}"
    if direct.exists():
        return direct

    candidates = list(settings.new_upload_dir.glob(f"{task_id}_*.pdf"))
    return candidates[0] if candidates else None


def _load_report(comparison_id: str):
    state = TASK_STORE.get(comparison_id)
    if state and state.result:
        return state.result
    return get_comparison_report(comparison_id)


def _report_date_tag(created_at: str) -> str:
    return created_at.split("T", 1)[0].replace("-", "")


def _download_name(prefix: str, comparison_id: str, created_at: str, extension: str) -> str:
    return f"{prefix}_{comparison_id}_{_report_date_tag(created_at)}.{extension}"


@router.get("/{comparison_id}/pdf")
async def export_pdf(comparison_id: str):
    report = _load_report(comparison_id)
    if not report:
        raise HTTPException(status_code=404, detail="Comparison not found")

    source_pdf = _resolve_new_pdf_path(comparison_id, report.new_filename)
    if not source_pdf:
        raise HTTPException(status_code=404, detail="Source PDF not found")

    output = settings.export_dir / f"{comparison_id}_annotated.pdf"
    try:
        exported = export_annotated_pdf(str(source_pdf), report.items, str(output))
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return FileResponse(
        exported,
        media_type="application/pdf",
        filename=_download_name("差異標註版", comparison_id, report.created_at, "pdf"),
    )


@router.get("/{comparison_id}/excel")
async def export_excel(comparison_id: str):
    report = _load_report(comparison_id)
    if not report:
        raise HTTPException(status_code=404, detail="Comparison not found")

    checklist = get_checklist(comparison_id)
    review_counts = get_review_counts(comparison_id)
    output = settings.export_dir / f"{comparison_id}_review.xlsx"
    exported = export_review_excel(
        comparison_id,
        report,
        checklist=checklist,
        review_counts=review_counts,
        output_path=str(output),
    )
    media = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return FileResponse(
        exported,
        media_type=media,
        filename=_download_name("差異檢核明細", comparison_id, report.created_at, "xlsx"),
    )


@router.get("/{comparison_id}/report")
async def export_report(comparison_id: str):
    report = _load_report(comparison_id)
    if not report:
        raise HTTPException(status_code=404, detail="Comparison not found")

    checklist = get_checklist(comparison_id)
    review_counts = get_review_counts(comparison_id)
    output = settings.export_dir / f"{comparison_id}_report.pdf"
    try:
        exported = export_review_report_pdf(
            comparison_id,
            report,
            checklist=checklist,
            review_counts=review_counts,
            output_path=str(output),
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return FileResponse(
        exported,
        media_type="application/pdf",
        filename=_download_name("差異檢核報告", comparison_id, report.created_at, "pdf"),
    )


@router.get("/{comparison_id}/log")
async def export_log(comparison_id: str):
    report = _load_report(comparison_id)
    if not report:
        raise HTTPException(status_code=404, detail="Comparison not found")

    checklist = get_checklist(comparison_id)
    review_counts = get_review_counts(comparison_id)
    review_logs = get_review_logs(comparison_id)
    output = settings.export_dir / f"{comparison_id}_log.json"
    exported = export_review_log_json(
        comparison_id,
        report,
        checklist=checklist,
        review_counts=review_counts,
        review_logs=review_logs,
        output_path=str(output),
    )
    return FileResponse(
        exported,
        media_type="application/json",
        filename=_download_name("完整審核Log", comparison_id, report.created_at, "json"),
    )


@router.get("/{comparison_id}/log-csv")
async def export_log_csv(comparison_id: str):
    report = _load_report(comparison_id)
    if not report:
        raise HTTPException(status_code=404, detail="Comparison not found")

    checklist = get_checklist(comparison_id)
    review_logs = get_review_logs(comparison_id)
    output = settings.export_dir / f"{comparison_id}_log.csv"
    exported = export_review_log_csv(
        comparison_id,
        report,
        checklist=checklist,
        review_logs=review_logs,
        output_path=str(output),
    )
    return FileResponse(
        exported,
        media_type="text/csv; charset=utf-8",
        filename=_download_name("審核Log", comparison_id, report.created_at, "csv"),
    )
