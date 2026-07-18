"""RiskService — AI health-risk analysis (feature #4).

Estimates multiple health risks with a Low/Medium/High score and, crucially, a
plain-language explanation for *every* risk (explainable by design). Risk logic
is rule-based and transparent — appropriate for a health context where a black
box would be irresponsible. Where a forecast is available, future-obesity risk
uses the projected BMI trajectory, not just today's snapshot.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from growthai.core.domain import BmiCategory, Measurement
from growthai.ml.forecast import ForecastPoint


class RiskLevel(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"

    @property
    def score(self) -> int:
        return {"Low": 1, "Medium": 2, "High": 3}[self.value]


@dataclass(frozen=True, slots=True)
class Risk:
    """A single named risk with level, numeric score and explanation."""

    name: str
    level: RiskLevel
    explanation: str

    def as_dict(self) -> dict[str, object]:
        return {"name": self.name, "level": self.level.value, "explanation": self.explanation}


@dataclass
class RiskReport:
    """Aggregated risk profile with an overall score."""

    risks: list[Risk]
    overall_level: RiskLevel
    overall_score: float

    def as_dict(self) -> dict[str, object]:
        return {
            "overall_level": self.overall_level.value,
            "overall_score": round(self.overall_score, 2),
            "risks": [r.as_dict() for r in self.risks],
        }


class RiskService:
    """Transparent, rule-based multi-risk assessment."""

    def assess(
        self,
        m: Measurement,
        category: BmiCategory,
        z_score: float,
        forecasts: list[ForecastPoint] | None = None,
    ) -> RiskReport:
        risks = [
            self._obesity(category, z_score),
            self._underweight(category, z_score),
            self._malnutrition(category, z_score, m),
            self._growth_delay(z_score, m),
            self._lifestyle(m),
            self._future_obesity(category, forecasts),
        ]
        avg = sum(r.level.score for r in risks) / len(risks)
        highs = sum(1 for r in risks if r.level is RiskLevel.HIGH)

        # Average alone can hide a single serious risk, which is unsafe in a
        # health context. The overall level therefore also respects the worst
        # findings: any HIGH lifts the floor to MEDIUM; two or more mean HIGH.
        base = RiskLevel.LOW if avg < 1.67 else RiskLevel.MEDIUM if avg < 2.34 else RiskLevel.HIGH
        if highs >= 2:
            overall = RiskLevel.HIGH
        elif highs == 1 and base is RiskLevel.LOW:
            overall = RiskLevel.MEDIUM
        else:
            overall = base
        return RiskReport(risks=risks, overall_level=overall, overall_score=avg)

    # ---- individual risk rules (each explainable) ----------------------

    def _obesity(self, category: BmiCategory, z: float) -> Risk:
        if category is BmiCategory.OBESE:
            level = RiskLevel.HIGH
        elif category is BmiCategory.OVERWEIGHT:
            level = RiskLevel.MEDIUM
        else:
            level = RiskLevel.LOW
        return Risk(
            "Obesity",
            level,
            f"BMI-for-age z-score is {z:+.1f} ({category.value}). "
            "z-scores above +2 indicate obesity, +1 to +2 overweight.",
        )

    def _underweight(self, category: BmiCategory, z: float) -> Risk:
        level = RiskLevel.HIGH if z < -3 else RiskLevel.MEDIUM if category is BmiCategory.UNDERWEIGHT else RiskLevel.LOW
        return Risk(
            "Underweight",
            level,
            f"z-score {z:+.1f}. Below -2 is thinness, below -3 is severe thinness.",
        )

    def _malnutrition(self, category: BmiCategory, z: float, m: Measurement) -> Risk:
        level = RiskLevel.HIGH if z < -3 else RiskLevel.MEDIUM if z < -2 else RiskLevel.LOW
        return Risk(
            "Malnutrition",
            level,
            "Weight-for-age well below the median can signal acute or chronic "
            f"undernutrition; current z-score {z:+.1f}.",
        )

    def _growth_delay(self, z: float, m: Measurement) -> Risk:
        # Uses BMI z as a proxy here; height-for-age z would refine this further.
        level = RiskLevel.MEDIUM if z < -2 else RiskLevel.LOW
        return Risk(
            "Growth delay",
            level,
            "Persistent tracking below the 3rd percentile warrants paediatric "
            "review for growth faltering.",
        )

    def _lifestyle(self, m: Measurement) -> Risk:
        # School-age children carry higher lifestyle risk (screen time, diet).
        level = RiskLevel.MEDIUM if m.age_years >= 10 else RiskLevel.LOW
        return Risk(
            "Lifestyle",
            level,
            "Screen time, sedentary behaviour and dietary patterns rise in "
            "school-age years; encourage 60 min/day of activity.",
        )

    def _future_obesity(self, category: BmiCategory, forecasts: list[ForecastPoint] | None) -> Risk:
        if not forecasts:
            level = RiskLevel.MEDIUM if category in (BmiCategory.OVERWEIGHT, BmiCategory.OBESE) else RiskLevel.LOW
            reason = "Based on current BMI category (no forecast available)."
        else:
            future = forecasts[-1]
            if future.bmi >= 30 or (future.bmi >= 25 and future.height_percentile < 50):
                level = RiskLevel.HIGH
            elif future.bmi >= 23:
                level = RiskLevel.MEDIUM
            else:
                level = RiskLevel.LOW
            reason = (
                f"Projected BMI by {future.horizon_label} is {future.bmi:.1f}. "
                "Overweight children have a higher chance of adult obesity."
            )
        return Risk("Future obesity", level, reason)
