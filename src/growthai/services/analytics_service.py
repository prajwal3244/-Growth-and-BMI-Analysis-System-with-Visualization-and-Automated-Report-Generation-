"""Population analytics (feature #18).

Produces population-level insights: average BMI, age distribution, BMI-category
distribution, gender comparison and obesity trend by age. When the database has
stored analyses it uses them; otherwise it generates a *clearly-labelled*
synthetic cohort from the reference engine so the analytics dashboard is never
empty in a demo.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from growthai.core.bmi import classify
from growthai.core.domain import Gender, Standard
from growthai.data.reference import get_reference_service

_SEED = 7


@dataclass
class PopulationInsights:
    frame: pd.DataFrame
    is_synthetic: bool

    @property
    def count(self) -> int:
        return len(self.frame)

    @property
    def average_bmi(self) -> float:
        return round(float(self.frame["bmi"].mean()), 2)

    def category_distribution(self) -> dict[str, int]:
        return self.frame["category"].value_counts().to_dict()

    def gender_average_bmi(self) -> dict[str, float]:
        return {g: round(float(v), 2) for g, v in self.frame.groupby("gender")["bmi"].mean().items()}

    def obesity_rate_by_age(self) -> pd.DataFrame:
        df = self.frame.copy()
        df["age_band"] = (df["age_years"] // 2 * 2).astype(int)
        df["is_obese"] = df["category"].isin(["Overweight", "Obesity"])
        out = df.groupby("age_band")["is_obese"].mean().reset_index()
        out["rate_pct"] = (out["is_obese"] * 100).round(1)
        return out[["age_band", "rate_pct"]]


class AnalyticsService:
    """Builds population insights from stored data or a synthetic cohort."""

    def __init__(self, standard: Standard = Standard.WHO):
        self.standard = standard
        self._ref = get_reference_service(standard)

    def synthetic_cohort(self, n: int = 500) -> pd.DataFrame:
        """Generate a realistic, seeded cohort spanning ages 2-19."""
        rng = np.random.default_rng(_SEED)
        rows = []
        genders = [Gender.MALE, Gender.FEMALE]
        for _ in range(n):
            gender = genders[int(rng.integers(0, 2))]
            age_months = float(rng.uniform(24, 228))
            # Sample around the reference median with realistic spread.
            med_h = self._ref.median(gender, age_months, "height_cm")
            med_w = self._ref.median(gender, age_months, "weight_kg")
            height = med_h * float(np.exp(rng.normal(0, 0.045)))
            weight = med_w * float(np.exp(rng.normal(0.02, 0.14)))  # slight positive skew
            bmi = round(weight / ((height / 100) ** 2), 2)
            z = self._ref.z_score(gender, age_months, "bmi", bmi)
            category = classify(bmi, age_months / 12, z).value
            rows.append(
                {
                    "gender": gender.value,
                    "age_years": round(age_months / 12, 1),
                    "height_cm": round(height, 1),
                    "weight_kg": round(weight, 1),
                    "bmi": bmi,
                    "category": category,
                }
            )
        return pd.DataFrame(rows)

    def insights(self, stored: pd.DataFrame | None = None, n: int = 500) -> PopulationInsights:
        if stored is not None and len(stored) >= 10:
            return PopulationInsights(stored, is_synthetic=False)
        return PopulationInsights(self.synthetic_cohort(n), is_synthetic=True)
