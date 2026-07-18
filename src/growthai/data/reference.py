"""Growth reference-data engine (WHO / CDC / IAP).

The original CSVs are *messy*:

* ``Age`` mixes ``"0Months"`` … ``"23Months"`` and ``"2Years"`` … ``"20Years"``;
* ``weight`` looks like ``"7.3 lb. (3.31 kg)"``;
* ``height``/``hight`` looks like ``'19.4"" (49.2 cm)'`` (and the column is even
  misspelled differently between the male and female files).

This module turns all of that into a clean numeric table keyed by *age in months*,
then serves **median** values plus **z-score / percentile** estimates. Because the
source provides a median curve (not full LMS tables), z-scores are approximated
using an age-scaled coefficient of variation — clearly documented and centralized
so it can later be swapped for real WHO LMS parameters (see ROADMAP).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm

from growthai.config import get_settings
from growthai.core.domain import Gender, Standard
from growthai.core.exceptions import ReferenceDataError, UnsupportedStandardError
from growthai.data.lms import get_lms_provider
from growthai.logging_conf import get_logger

logger = get_logger("data.reference")

_KG_RE = re.compile(r"([\d.]+)\s*kg", re.IGNORECASE)
_CM_RE = re.compile(r"([\d.]+)\s*cm", re.IGNORECASE)
_AGE_RE = re.compile(r"([\d.]+)\s*(month|year)", re.IGNORECASE)

# Approximate biological coefficient of variation (SD / mean) for anthropometry.
# Height varies far less than weight/BMI. Used only until real LMS tables land.
_CV = {"height": 0.04, "weight": 0.12, "bmi": 0.13}

# Multipliers applied to the WHO baseline median to synthesize CDC / IAP curves
# when dedicated files are not present. Kept explicit and auditable.
_STANDARD_SCALE = {
    Standard.WHO: {"height": 1.000, "weight": 1.000},
    Standard.CDC: {"height": 1.005, "weight": 1.020},  # CDC runs slightly heavier
    Standard.IAP: {"height": 0.985, "weight": 0.955},  # Indian Academy of Pediatrics
}


def parse_age(raw: str) -> float | None:
    """'0Months' -> 0.0, '2Years' -> 24.0. Returns None if unparseable."""
    m = _AGE_RE.search(str(raw))
    if not m:
        return None
    value, unit = float(m.group(1)), m.group(2).lower()
    return value if unit.startswith("month") else value * 12.0


def _extract(pattern: re.Pattern[str], raw: str) -> float | None:
    m = pattern.search(str(raw))
    return float(m.group(1)) if m else None


@dataclass(frozen=True, slots=True)
class ReferencePoint:
    """One median reference row on the age axis."""

    age_months: float
    height_cm: float
    weight_kg: float

    @property
    def bmi(self) -> float:
        return round(self.weight_kg / ((self.height_cm / 100.0) ** 2), 2)


class ReferenceDataService:
    """Loads and serves growth-reference lookups for a given standard.

    Instances are cheap; construction parses the CSV once. Use
    :func:`get_reference_service` for a cached, shared instance.
    """

    def __init__(self, standard: Standard = Standard.WHO, datasets_dir: Path | None = None):
        if standard not in _STANDARD_SCALE:
            raise UnsupportedStandardError(f"Unsupported standard: {standard}")
        self.standard = standard
        self._dir = datasets_dir or get_settings().datasets_dir
        self._tables: dict[Gender, pd.DataFrame] = {}
        for gender in Gender:
            self._tables[gender] = self._load(gender)

    # ---- loading -------------------------------------------------------

    def _source_path(self, gender: Gender) -> Path:
        candidates = [
            self._dir / "who" / f"{gender.value}_0-20.csv",
            self._dir / f"{gender.value}0-20 csv.csv",
            get_settings().datasets_dir.parent / f"{gender.value}0-20 csv.csv",
        ]
        for path in candidates:
            if path.exists():
                return path
        raise ReferenceDataError(
            f"No reference CSV for {gender.value}; looked in {[str(c) for c in candidates]}"
        )

    def _load(self, gender: Gender) -> pd.DataFrame:
        path = self._source_path(gender)
        raw = pd.read_csv(path)
        # Column names differ across files ('height' vs 'hight'); locate by position/order.
        cols = {c.lower().strip(): c for c in raw.columns}
        age_col = cols.get("age", raw.columns[0])
        weight_col = cols.get("weight", raw.columns[1])
        height_col = next(
            (cols[c] for c in ("height", "hight") if c in cols), raw.columns[2]
        )

        rows = []
        for _, r in raw.iterrows():
            age = parse_age(r[age_col])
            kg = _extract(_KG_RE, r[weight_col])
            cm = _extract(_CM_RE, r[height_col])
            if age is None or kg is None or cm is None:
                continue
            scale = _STANDARD_SCALE[self.standard]
            rows.append(
                {
                    "age_months": age,
                    "weight_kg": round(kg * scale["weight"], 3),
                    "height_cm": round(cm * scale["height"], 2),
                }
            )
        df = pd.DataFrame(rows).sort_values("age_months").reset_index(drop=True)
        if df.empty:
            raise ReferenceDataError(f"Parsed zero rows from {path}")
        df["bmi"] = (df["weight_kg"] / (df["height_cm"] / 100.0) ** 2).round(2)
        logger.info("Loaded %d %s reference points for %s", len(df), self.standard.value, gender.value)
        return df

    # ---- lookups -------------------------------------------------------

    def table(self, gender: Gender) -> pd.DataFrame:
        return self._tables[gender].copy()

    def median(self, gender: Gender, age_months: float, metric: str) -> float:
        """Linearly-interpolated median for a metric at an arbitrary age."""
        if metric not in {"height_cm", "weight_kg", "bmi"}:
            raise ReferenceDataError(f"Unknown metric: {metric}")
        df = self._tables[gender]
        return float(np.interp(age_months, df["age_months"], df[metric]))

    def reference_point(self, gender: Gender, age_months: float) -> ReferencePoint:
        return ReferencePoint(
            age_months=age_months,
            height_cm=round(self.median(gender, age_months, "height_cm"), 2),
            weight_kg=round(self.median(gender, age_months, "weight_kg"), 3),
        )

    def z_score(self, gender: Gender, age_months: float, metric_key: str, value: float) -> float:
        """z-score of ``value`` vs the age distribution.

        ``metric_key`` is one of 'height', 'weight', 'bmi'. Prefers the exact
        WHO **LMS** method when official tables are installed (see
        :mod:`growthai.data.lms`); otherwise falls back to a documented
        log-normal approximation around the age median.
        """
        lms = get_lms_provider()
        if lms.available(gender, metric_key):
            table = lms.table(gender, metric_key)
            assert table is not None
            return table.z_score(age_months, value)

        median_map = {"height": "height_cm", "weight": "weight_kg", "bmi": "bmi"}
        median = self.median(gender, age_months, median_map[metric_key])
        if median <= 0 or value <= 0:
            return 0.0
        sigma_log = _CV[metric_key]
        return float(np.log(value / median) / sigma_log)

    @property
    def uses_lms(self) -> bool:
        """True when the exact WHO LMS engine is backing z-scores."""
        return get_lms_provider().is_active

    def percentile(self, gender: Gender, age_months: float, metric_key: str, value: float) -> float:
        """Percentile (0-100) corresponding to the z-score."""
        z = self.z_score(gender, age_months, metric_key, value)
        return round(float(norm.cdf(z) * 100.0), 1)


@lru_cache(maxsize=len(Standard))
def get_reference_service(standard: Standard | str = Standard.WHO) -> ReferenceDataService:
    """Cached factory — one parsed service per standard."""
    std = Standard(standard) if not isinstance(standard, Standard) else standard
    return ReferenceDataService(std)
