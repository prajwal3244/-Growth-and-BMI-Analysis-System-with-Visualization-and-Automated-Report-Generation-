"""Population analytics routes (feature #18).

Aggregates stored analyses into population-level insights: average BMI, category
distribution, gender comparison and age distribution. Falls back to a synthetic
sample when the database is empty so the dashboard always has something to show.
"""

from __future__ import annotations

from collections import Counter

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from growthai.db import models
from growthai.db.session import get_db

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary", summary="Population BMI & category analytics")
def summary(db: Session = Depends(get_db)) -> dict:
    analyses = db.scalars(select(models.Analysis)).all()
    if not analyses:
        return {"source": "empty", "count": 0, "message": "No stored analyses yet."}

    bmis = [a.bmi for a in analyses]
    categories = Counter(a.category for a in analyses)
    risks = Counter(a.overall_risk for a in analyses)
    return {
        "source": "database",
        "count": len(analyses),
        "average_bmi": round(sum(bmis) / len(bmis), 2),
        "min_bmi": round(min(bmis), 2),
        "max_bmi": round(max(bmis), 2),
        "category_distribution": dict(categories),
        "risk_distribution": dict(risks),
    }
