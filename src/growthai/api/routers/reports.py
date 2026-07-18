"""Report generation & download routes (feature #6)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from growthai.api.schemas import ReportOut, ReportRequest
from growthai.config import get_settings
from growthai.core.domain import Gender, Measurement
from growthai.core.exceptions import InvalidMeasurementError
from growthai.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("", response_model=ReportOut, summary="Generate a smart medical report")
def create_report(req: ReportRequest) -> ReportOut:
    try:
        m = Measurement(
            age_months=req.age_months, height_cm=req.height_cm,
            weight_kg=req.weight_kg, gender=Gender.parse(req.gender),
        )
    except InvalidMeasurementError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    result = ReportService(req.standard).generate(req.name, m, req.doctor_notes)
    fmt = "pdf" if result.pdf_generated else "html"
    return ReportOut(
        report_id=result.report_id,
        html_available=result.html_path.exists(),
        pdf_available=result.pdf_generated,
        download_url=f"/reports/{result.report_id}/download?fmt={fmt}",
    )


@router.get("/{report_id}/download", summary="Download a generated report")
def download(report_id: str, fmt: str = "html") -> FileResponse:
    out_dir = get_settings().reports_dir
    path = out_dir / f"report_{report_id}.{fmt}"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Report not found")
    media = "application/pdf" if fmt == "pdf" else "text/html"
    return FileResponse(str(path), media_type=media, filename=path.name)
