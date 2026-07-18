"""Analysis & prediction routes (features #2, #4, #5).

``/analysis`` runs the full pipeline (assessment + forecast + explanation +
risk). It works anonymously for quick demos, and optionally persists results
when an authenticated user passes ``save=true`` with a ``patient_id``.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from growthai.api.schemas import AnalyzeRequest
from growthai.core.domain import Gender, Measurement, Standard
from growthai.core.exceptions import InvalidMeasurementError
from growthai.db import models
from growthai.db.session import get_db
from growthai.services.growth_service import GrowthService
from growthai.services.nutrition_service import NutritionService
from growthai.services.risk_service import RiskService

router = APIRouter(prefix="/analysis", tags=["analysis"])


def _measurement(req: AnalyzeRequest) -> Measurement:
    try:
        return Measurement(
            age_months=req.age_months,
            height_cm=req.height_cm,
            weight_kg=req.weight_kg,
            gender=Gender.parse(req.gender),
        )
    except InvalidMeasurementError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("", summary="Full growth analysis: assessment, forecast, risk, nutrition")
def analyze(req: AnalyzeRequest, db: Session = Depends(get_db)) -> dict:
    m = _measurement(req)
    growth = GrowthService(req.standard)
    analysis = growth.analyze(m)
    a = analysis.assessment
    nutrition = NutritionService().recommend(m, a.category)
    risk = RiskService().assess(m, a.category, a.z_score, analysis.forecasts)

    payload = analysis.as_dict()
    payload["nutrition"] = nutrition.as_dict()
    payload["risk"] = risk.as_dict()
    payload["model_comparison"] = growth.forecaster.model_comparison()

    if req.save and req.patient_id:
        _persist(db, req.patient_id, m, analysis, risk.overall_level.value)
    return payload


@router.get("/model-comparison", summary="ML model leaderboard (R2 / MAE)")
def model_comparison(standard: Standard = Standard.WHO) -> dict:
    return GrowthService(standard).forecaster.model_comparison()


def _persist(db: Session, patient_id: int, m: Measurement, analysis, overall_risk: str) -> None:
    patient = db.get(models.Patient, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    meas = models.Measurement(
        patient_id=patient_id, age_months=m.age_months, height_cm=m.height_cm, weight_kg=m.weight_kg
    )
    db.add(meas)
    db.flush()
    a = analysis.assessment
    row = models.Analysis(
        measurement_id=meas.id, bmi=a.bmi, category=a.category.value, z_score=a.z_score,
        percentile=a.percentile, standard=a.standard.value, overall_risk=overall_risk,
    )
    db.add(row)
    db.flush()
    for f in analysis.forecasts:
        db.add(models.Prediction(
            analysis_id=row.id, horizon=f.horizon_label, height_cm=f.height_cm,
            weight_kg=f.weight_kg, bmi=f.bmi, confidence=f.confidence,
        ))
    db.commit()
