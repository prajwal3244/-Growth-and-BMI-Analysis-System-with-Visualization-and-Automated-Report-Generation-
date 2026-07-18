"""Domain value objects and enums.

These are the vocabulary of the platform. They are deliberately free of any
framework (no FastAPI, no SQLAlchemy) so the clinical logic stays testable and
reusable across the API, the dashboard and the CLI.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from growthai.core.exceptions import InvalidMeasurementError

# Physiological guard rails — reject obviously impossible inputs early.
MIN_HEIGHT_CM = 30.0
MAX_HEIGHT_CM = 230.0
MIN_WEIGHT_KG = 1.0
MAX_WEIGHT_KG = 300.0
MAX_AGE_MONTHS = 240.0  # 20 years — the range covered by our reference data.


class Gender(str, Enum):
    """Biological sex used for growth-reference lookups."""

    MALE = "male"
    FEMALE = "female"

    @classmethod
    def parse(cls, value: str) -> Gender:
        """Accept 'M'/'F', 'male'/'female' (any case) — mirrors the original CLI."""
        v = value.strip().lower()
        if v in {"m", "male", "boy"}:
            return cls.MALE
        if v in {"f", "female", "girl"}:
            return cls.FEMALE
        raise InvalidMeasurementError(f"Unrecognized gender: {value!r}")


class Standard(str, Enum):
    """Supported growth-reference standards (feature #9)."""

    WHO = "WHO"
    CDC = "CDC"
    IAP = "IAP"


class BmiCategory(str, Enum):
    """BMI classification bands."""

    UNDERWEIGHT = "Underweight"
    NORMAL = "Normal Weight"
    OVERWEIGHT = "Overweight"
    OBESE = "Obesity"


@dataclass(frozen=True, slots=True)
class Measurement:
    """A single anthropometric measurement for one individual.

    ``age_months`` unifies the original CSV's mixed 'NMonths'/'NYears' encoding
    into a single numeric axis (see :func:`growthai.data.reference.parse_age`).
    """

    age_months: float
    height_cm: float
    weight_kg: float
    gender: Gender

    def __post_init__(self) -> None:
        if not (0 <= self.age_months <= MAX_AGE_MONTHS):
            raise InvalidMeasurementError(
                f"age_months must be within 0..{MAX_AGE_MONTHS}, got {self.age_months}"
            )
        if not (MIN_HEIGHT_CM <= self.height_cm <= MAX_HEIGHT_CM):
            raise InvalidMeasurementError(
                f"height_cm must be within {MIN_HEIGHT_CM}..{MAX_HEIGHT_CM}, got {self.height_cm}"
            )
        if not (MIN_WEIGHT_KG <= self.weight_kg <= MAX_WEIGHT_KG):
            raise InvalidMeasurementError(
                f"weight_kg must be within {MIN_WEIGHT_KG}..{MAX_WEIGHT_KG}, got {self.weight_kg}"
            )

    @property
    def age_years(self) -> float:
        return self.age_months / 12.0

    @property
    def height_m(self) -> float:
        return self.height_cm / 100.0

    @property
    def bmi(self) -> float:
        """BMI in kg/m². Reuses the original formula, on correct SI units."""
        return round(self.weight_kg / (self.height_m**2), 2)


@dataclass(frozen=True, slots=True)
class GrowthAssessment:
    """Result of assessing a :class:`Measurement` against a reference standard."""

    bmi: float
    category: BmiCategory
    z_score: float
    percentile: float
    standard: Standard
    height_median_cm: float
    weight_median_kg: float

    @property
    def is_healthy(self) -> bool:
        return self.category is BmiCategory.NORMAL
