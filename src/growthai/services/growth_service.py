"""GrowthService — the primary orchestration use case.

Given a measurement it produces a full assessment: BMI, age/gender-aware
category, z-score, percentile against a chosen standard, plus forecasts and an
explanation. This is the single entry point the API and dashboard both call,
so the "analyze a child" logic lives in exactly one place.
"""

from __future__ import annotations

from dataclasses import dataclass

from growthai.core.bmi import classify
from growthai.core.domain import GrowthAssessment, Measurement, Standard
from growthai.data.reference import get_reference_service
from growthai.logging_conf import get_logger
from growthai.ml.explain import Explanation, explain_forecast
from growthai.ml.forecast import ForecastPoint, GrowthForecaster

logger = get_logger("services.growth")


@dataclass
class GrowthAnalysis:
    """Everything the UI/API needs about one measurement."""

    measurement: Measurement
    assessment: GrowthAssessment
    forecasts: list[ForecastPoint]
    explanation: Explanation

    def as_dict(self) -> dict[str, object]:
        return {
            "input": {
                "age_months": self.measurement.age_months,
                "age_years": round(self.measurement.age_years, 1),
                "gender": self.measurement.gender.value,
                "height_cm": self.measurement.height_cm,
                "weight_kg": self.measurement.weight_kg,
                "bmi": self.measurement.bmi,
            },
            "assessment": {
                "bmi": self.assessment.bmi,
                "category": self.assessment.category.value,
                "z_score": round(self.assessment.z_score, 2),
                "percentile": self.assessment.percentile,
                "standard": self.assessment.standard.value,
                "height_median_cm": self.assessment.height_median_cm,
                "weight_median_kg": self.assessment.weight_median_kg,
                "is_healthy": self.assessment.is_healthy,
            },
            "forecasts": [f.as_dict() for f in self.forecasts],
            "explanation": self.explanation.as_dict(),
        }


class GrowthService:
    """Assess and forecast growth for a given standard."""

    def __init__(self, standard: Standard = Standard.WHO):
        self.standard = standard
        self._ref = get_reference_service(standard)
        self._forecaster = GrowthForecaster(standard)

    def assess(self, m: Measurement) -> GrowthAssessment:
        z = self._ref.z_score(m.gender, m.age_months, "bmi", m.bmi)
        percentile = self._ref.percentile(m.gender, m.age_months, "bmi", m.bmi)
        category = classify(m.bmi, m.age_years, z)
        ref_point = self._ref.reference_point(m.gender, m.age_months)
        return GrowthAssessment(
            bmi=m.bmi,
            category=category,
            z_score=z,
            percentile=percentile,
            standard=self.standard,
            height_median_cm=ref_point.height_cm,
            weight_median_kg=ref_point.weight_kg,
        )

    def analyze(self, m: Measurement) -> GrowthAnalysis:
        assessment = self.assess(m)
        forecasts = self._forecaster.forecast(m)
        # Explain the furthest horizon (most informative for parents).
        explanation = explain_forecast(self._forecaster, m, forecasts[-1], assessment.category)
        logger.info(
            "Analyzed %s child age=%.0fmo bmi=%.1f -> %s (p%.0f)",
            m.gender.value, m.age_months, m.bmi, assessment.category.value, assessment.percentile,
        )
        return GrowthAnalysis(m, assessment, forecasts, explanation)

    @property
    def forecaster(self) -> GrowthForecaster:
        return self._forecaster

    @property
    def reference(self):
        """Expose the reference-data service (percentile lookups for the UI)."""
        return self._ref
