"""Personalized growth forecasting.

Children tend to *track their percentile channel* — a child on the 75th
percentile at age 6 is most likely near the 75th at age 7. We exploit this
clinically-grounded property: the trained population model gives the expected
median trajectory, and we anchor it to the individual's current ratio-to-model,
projecting that ratio forward. This yields a **personalized** forecast rather
than merely echoing the population median.

Outputs future height, weight, BMI and percentile at arbitrary horizons
(defaults: +6 months and +1 year — feature #2).
"""

from __future__ import annotations

from dataclasses import dataclass

from growthai.core.bmi import calculate_bmi
from growthai.core.domain import Gender, Measurement, Standard
from growthai.data.reference import get_reference_service
from growthai.ml.models import GrowthRegressor, get_growth_regressor


@dataclass(frozen=True, slots=True)
class ForecastPoint:
    """Forecast for a single horizon."""

    horizon_label: str
    age_months: float
    height_cm: float
    weight_kg: float
    bmi: float
    height_percentile: float
    weight_percentile: float
    confidence: float

    def as_dict(self) -> dict[str, float | str]:
        return {
            "horizon": self.horizon_label,
            "age_months": round(self.age_months, 1),
            "height_cm": round(self.height_cm, 1),
            "weight_kg": round(self.weight_kg, 1),
            "bmi": round(self.bmi, 1),
            "height_percentile": self.height_percentile,
            "weight_percentile": self.weight_percentile,
            "confidence": self.confidence,
        }


DEFAULT_HORIZONS: dict[str, float] = {"+6 months": 6.0, "+1 year": 12.0}


class GrowthForecaster:
    """Forecasts an individual's future growth via percentile-channel tracking."""

    def __init__(self, standard: Standard = Standard.WHO, retrain: bool = False):
        self.standard = standard
        self._ref = get_reference_service(standard)
        self.height_model: GrowthRegressor = get_growth_regressor("height_cm", retrain)
        self.weight_model: GrowthRegressor = get_growth_regressor("weight_kg", retrain)

    # ---- confidence ----------------------------------------------------

    @property
    def _base_confidence(self) -> float:
        """Combine the two models' R² into a headline confidence (0-100)."""
        hs = self.height_model.best_score
        ws = self.weight_model.best_score
        r2 = ((hs.r2 if hs else 0.8) + (ws.r2 if ws else 0.8)) / 2.0
        return round(max(0.0, min(1.0, r2)) * 100.0, 1)

    def _horizon_confidence(self, horizon_months: float) -> float:
        """Confidence decays gently with how far ahead we forecast."""
        decay = max(0.6, 1.0 - horizon_months / 60.0)  # -1% per ~7 months, floor 60%
        return round(self._base_confidence * decay, 1)

    # ---- forecasting ---------------------------------------------------

    def _channel_ratio(self, m: Measurement, sex_male: float) -> tuple[float, float]:
        model_h_now = self.height_model.predict(m.age_months, sex_male)
        model_w_now = self.weight_model.predict(m.age_months, sex_male)
        return m.height_cm / model_h_now, m.weight_kg / model_w_now

    def forecast_at(self, m: Measurement, horizon_months: float, label: str) -> ForecastPoint:
        sex_male = 1.0 if m.gender is Gender.MALE else 0.0
        ratio_h, ratio_w = self._channel_ratio(m, sex_male)
        future_age = min(m.age_months + horizon_months, 240.0)

        future_h = self.height_model.predict(future_age, sex_male) * ratio_h
        future_w = self.weight_model.predict(future_age, sex_male) * ratio_w
        future_bmi = calculate_bmi(future_w, future_h / 100.0)

        return ForecastPoint(
            horizon_label=label,
            age_months=future_age,
            height_cm=future_h,
            weight_kg=future_w,
            bmi=future_bmi,
            height_percentile=self._ref.percentile(m.gender, future_age, "height", future_h),
            weight_percentile=self._ref.percentile(m.gender, future_age, "weight", future_w),
            confidence=self._horizon_confidence(horizon_months),
        )

    def forecast(
        self, m: Measurement, horizons: dict[str, float] | None = None
    ) -> list[ForecastPoint]:
        horizons = horizons or DEFAULT_HORIZONS
        return [self.forecast_at(m, months, label) for label, months in horizons.items()]

    def trajectory(self, m: Measurement, months_ahead: int = 24, step: int = 3) -> list[ForecastPoint]:
        """Dense forecast series for plotting a forward growth curve."""
        points = []
        for h in range(step, months_ahead + 1, step):
            points.append(self.forecast_at(m, float(h), f"+{h}mo"))
        return points

    def model_comparison(self) -> dict[str, list[dict[str, float | str]]]:
        """Model-vs-model scoreboard for the dashboard (feature #2: compare models)."""
        return {
            "height_cm": [s.as_dict() for s in self.height_model.scores],
            "weight_kg": [s.as_dict() for s in self.weight_model.scores],
        }
