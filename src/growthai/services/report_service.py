"""ReportService — assembles the smart medical report (feature #6).

Pulls together the growth analysis, nutrition plan, risk report and charts into
a single Jinja2 context, renders the hospital-grade template and writes both an
HTML file (always) and a PDF (when WeasyPrint is available). Returns the paths
and a flag telling callers which formats were produced.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from growthai.config import get_settings
from growthai.core.domain import Measurement, Standard
from growthai.logging_conf import get_logger
from growthai.reports.pdf import (
    fig_to_data_uri,
    html_to_pdf,
    qr_data_uri,
    render_html,
)
from growthai.services.growth_service import GrowthAnalysis, GrowthService
from growthai.services.nutrition_service import NutritionService
from growthai.services.risk_service import RiskService
from growthai.viz import charts

logger = get_logger("services.report")

_PILL_CLASS = {
    "Underweight": "underweight", "Normal Weight": "normal",
    "Overweight": "overweight", "Obesity": "obesity",
}


@dataclass
class ReportResult:
    report_id: str
    html_path: Path
    pdf_path: Path | None
    pdf_generated: bool


class ReportService:
    """Builds patient reports from a measurement."""

    def __init__(self, standard: Standard = Standard.WHO):
        self.standard = standard
        self.growth = GrowthService(standard)
        self.nutrition = NutritionService()
        self.risk = RiskService()

    def build_context(self, name: str, m: Measurement, doctor_notes: str = "") -> dict:
        analysis: GrowthAnalysis = self.growth.analyze(m)
        a = analysis.assessment
        plan = self.nutrition.recommend(m, a.category)
        risk = self.risk.assess(m, a.category, a.z_score, analysis.forecasts)
        report_id = uuid.uuid4().hex[:10].upper()

        # Charts -> PNG data URIs (light theme reads better on white paper).
        chart_uris = {
            "gauge": fig_to_data_uri(charts.bmi_gauge(a.bmi, a.category.value, dark=False)),
            "percentile": fig_to_data_uri(charts.percentile_curve(m, self.standard, "height_cm", dark=False)),
            "forecast": fig_to_data_uri(
                charts.growth_forecast_chart(m, self.growth.forecaster, "height_cm", dark=False)
            ),
        }

        return {
            "report_id": report_id,
            "date": datetime.now().strftime("%B %d, %Y %H:%M"),
            "standard": self.standard.value,
            "patient": {
                "name": name,
                "age_years": round(m.age_years, 1),
                "gender": m.gender.value,
                "height_cm": m.height_cm,
                "weight_kg": m.weight_kg,
            },
            "assessment": {
                "bmi": a.bmi,
                "category": a.category.value,
                "category_class": _PILL_CLASS.get(a.category.value, "normal"),
                "z_score": round(a.z_score, 2),
                "percentile": a.percentile,
            },
            "forecasts": [f.as_dict() for f in analysis.forecasts],
            "explanation": analysis.explanation.as_dict(),
            "risk": {
                "overall_level": risk.overall_level.value,
                "overall_class": risk.overall_level.value.lower(),
                "risks": [r.as_dict() for r in risk.risks],
            },
            "nutrition": plan.as_dict(),
            "charts": chart_uris,
            "doctor_notes": doctor_notes,
            "qr_data_uri": qr_data_uri(f"GrowthAI|{report_id}|{name}|BMI{a.bmi}|{a.category.value}"),
        }

    def generate(self, name: str, m: Measurement, doctor_notes: str = "") -> ReportResult:
        context = self.build_context(name, m, doctor_notes)
        html = render_html("report_template.html", context)

        out_dir = get_settings().reports_dir
        report_id = context["report_id"]
        html_path = out_dir / f"report_{report_id}.html"
        html_path.write_text(html, encoding="utf-8")

        pdf_path = out_dir / f"report_{report_id}.pdf"
        pdf_ok = html_to_pdf(html, pdf_path)

        logger.info("Report %s generated (pdf=%s)", report_id, pdf_ok)
        return ReportResult(
            report_id=report_id,
            html_path=html_path,
            pdf_path=pdf_path if pdf_ok else None,
            pdf_generated=pdf_ok,
        )
