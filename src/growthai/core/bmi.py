"""BMI calculation and classification.

Reuses the original ``calculate_bmi`` / ``determine_bmi_category`` logic but:

* fixes the classification **boundary gaps** (24.9-25.0 and 29.9-30.0 previously
  fell through to "Obesity");
* separates **adult** cut-offs from **child** classification. For children the
  correct clinical approach is a *BMI-for-age z-score*, not fixed adult numbers —
  so :func:`classify_bmi_for_age` is provided and used by the service layer.
"""

from __future__ import annotations

from growthai.core.domain import BmiCategory

# Age (years) at/after which fixed adult BMI cut-offs are clinically appropriate.
ADULT_AGE_YEARS = 20.0


def calculate_bmi(weight_kg: float, height_m: float) -> float:
    """BMI = weight / height² (kg, m). Same formula as the original script."""
    if height_m <= 0:
        raise ValueError("height_m must be positive")
    return round(weight_kg / (height_m**2), 2)


def classify_bmi_adult(bmi: float) -> BmiCategory:
    """WHO adult BMI classification with **corrected, contiguous** boundaries."""
    if bmi < 18.5:
        return BmiCategory.UNDERWEIGHT
    if bmi < 25.0:  # 18.5 <= bmi < 25.0  (was 24.9 — left a gap)
        return BmiCategory.NORMAL
    if bmi < 30.0:  # 25.0 <= bmi < 30.0  (was 29.9 — left a gap)
        return BmiCategory.OVERWEIGHT
    return BmiCategory.OBESE


def classify_bmi_for_age(z_score: float) -> BmiCategory:
    """Classify a child's BMI from its **BMI-for-age z-score**.

    Bands follow WHO guidance for 5-19 year olds:

    ======================  ====================
    z-score                 category
    ======================  ====================
    z < -2                  Underweight (thinness)
    -2 <= z <= +1           Normal weight
    +1 < z <= +2            Overweight
    z > +2                  Obesity
    ======================  ====================
    """
    if z_score < -2.0:
        return BmiCategory.UNDERWEIGHT
    if z_score <= 1.0:
        return BmiCategory.NORMAL
    if z_score <= 2.0:
        return BmiCategory.OVERWEIGHT
    return BmiCategory.OBESE


def classify(bmi: float, age_years: float, z_score: float) -> BmiCategory:
    """Age-aware entry point: z-score for children, adult cut-offs at 20+."""
    if age_years >= ADULT_AGE_YEARS:
        return classify_bmi_adult(bmi)
    return classify_bmi_for_age(z_score)
