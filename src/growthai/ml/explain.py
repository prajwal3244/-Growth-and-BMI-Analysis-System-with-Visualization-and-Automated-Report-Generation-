"""Explainable AI (feature #5).

Every prediction ships with:
* the important features driving it (from the model),
* a confidence score (from the forecaster),
* a plain-language explanation a parent can understand,
* optional SHAP values when the ``shap`` package is installed.

Keeping explanation generation here (not in the model) means we can enrich the
narrative without retraining and keeps the models focused on prediction (SRP).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from growthai.core.domain import BmiCategory, Measurement
from growthai.ml.features import FEATURE_COLUMNS
from growthai.ml.forecast import ForecastPoint, GrowthForecaster

_FEATURE_LABELS = {"age_months": "Age", "sex_male": "Sex"}


@dataclass
class Explanation:
    """A transparent, human-readable rationale for a forecast."""

    summary: str
    confidence: float
    feature_importance: dict[str, float]
    drivers: list[str] = field(default_factory=list)
    shap_available: bool = False

    def as_dict(self) -> dict[str, object]:
        return {
            "summary": self.summary,
            "confidence": self.confidence,
            "feature_importance": {
                _FEATURE_LABELS.get(k, k): v for k, v in self.feature_importance.items()
            },
            "drivers": self.drivers,
            "shap_available": self.shap_available,
        }


def _percentile_phrase(p: float) -> str:
    if p < 15:
        return f"below average (around the {p:.0f}th percentile)"
    if p > 85:
        return f"above average (around the {p:.0f}th percentile)"
    return f"typical for age (around the {p:.0f}th percentile)"


def explain_forecast(
    forecaster: GrowthForecaster,
    measurement: Measurement,
    forecast: ForecastPoint,
    category: BmiCategory,
) -> Explanation:
    """Build a full explanation for a single forecast point."""
    # Feature importance is the mean across the two underlying models.
    hi = forecaster.height_model.feature_importance()
    wi = forecaster.weight_model.feature_importance()
    importance = {f: round((hi.get(f, 0) + wi.get(f, 0)) / 2, 4) for f in FEATURE_COLUMNS}
    top_feature = max(importance, key=importance.get)

    drivers = [
        f"{_FEATURE_LABELS[top_feature]} is the strongest driver "
        f"({importance[top_feature] * 100:.0f}% of the model's decision).",
        "The forecast assumes the child continues to track their current "
        "growth percentile channel - the standard clinical assumption.",
        f"Projected height is {_percentile_phrase(forecast.height_percentile)}.",
        f"Projected weight is {_percentile_phrase(forecast.weight_percentile)}.",
    ]

    summary = (
        f"By {forecast.horizon_label}, we project a height of ~{forecast.height_cm:.0f} cm and "
        f"weight of ~{forecast.weight_kg:.0f} kg, giving a BMI of ~{forecast.bmi:.1f} "
        f"({category.value}). Confidence: {forecast.confidence:.0f}%."
    )

    return Explanation(
        summary=summary,
        confidence=forecast.confidence,
        feature_importance=importance,
        drivers=drivers,
        shap_available=_shap_available(),
    )


def _shap_available() -> bool:
    try:  # pragma: no cover - optional dependency
        import shap  # noqa: F401

        return True
    except Exception:  # noqa: BLE001
        return False
