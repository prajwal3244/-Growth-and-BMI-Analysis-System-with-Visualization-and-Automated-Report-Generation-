"""WHO LMS reference engine.

The WHO Child Growth Standards express each anthropometric distribution, at each
age, with three parameters:

* **L** — Box-Cox power (skewness),
* **M** — median,
* **S** — coefficient of variation.

An individual's exact z-score is then::

    z = ((value / M) ** L - 1) / (L * S)          for L != 0
    z = ln(value / M) / S                         for L == 0

This is the clinically correct method and replaces the median-only log-normal
approximation used elsewhere in the engine. It activates automatically whenever
official WHO LMS tables are present in ``datasets/who/lms/`` (one CSV per
gender+metric with columns ``age_months,L,M,S``). If they are absent, callers
fall back to the approximation - exactly like the optional LLM providers.

Download the official tables with ``python scripts/fetch_who_lms.py`` (see
``datasets/who/lms/README.md``). No reference constants are bundled or invented.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm

from growthai.config import get_settings
from growthai.core.domain import Gender
from growthai.logging_conf import get_logger

logger = get_logger("data.lms")

# Metric -> file stem. Files live in datasets/who/lms/<gender>_<metric>.csv
_METRIC_FILE = {"bmi": "bmi_for_age", "height": "height_for_age", "weight": "weight_for_age"}
_REQUIRED_COLUMNS = {"age_months", "L", "M", "S"}


@dataclass(frozen=True, slots=True)
class LMSPoint:
    age_months: float
    L: float
    M: float
    S: float


class LMSTable:
    """An interpolatable LMS table for one gender+metric."""

    def __init__(self, frame: pd.DataFrame):
        missing = _REQUIRED_COLUMNS - set(frame.columns)
        if missing:
            raise ValueError(f"LMS table missing columns: {missing}")
        self._df = frame.sort_values("age_months").reset_index(drop=True)

    def lms(self, age_months: float) -> LMSPoint:
        df = self._df
        return LMSPoint(
            age_months=age_months,
            L=float(np.interp(age_months, df["age_months"], df["L"])),
            M=float(np.interp(age_months, df["age_months"], df["M"])),
            S=float(np.interp(age_months, df["age_months"], df["S"])),
        )

    def z_score(self, age_months: float, value: float) -> float:
        p = self.lms(age_months)
        if value <= 0 or p.M <= 0 or p.S == 0:
            return 0.0
        if abs(p.L) < 1e-7:
            return float(np.log(value / p.M) / p.S)
        return float(((value / p.M) ** p.L - 1.0) / (p.L * p.S))

    def percentile(self, age_months: float, value: float) -> float:
        return round(float(norm.cdf(self.z_score(age_months, value)) * 100.0), 1)

    def median(self, age_months: float) -> float:
        return self.lms(age_months).M


class LMSProvider:
    """Loads whatever official LMS tables are available on disk."""

    def __init__(self, lms_dir: Path | None = None):
        self._dir = lms_dir or (get_settings().datasets_dir / "who" / "lms")
        self._tables: dict[tuple[Gender, str], LMSTable] = {}
        self._load_all()

    def _load_all(self) -> None:
        if not self._dir.exists():
            return
        for gender in Gender:
            for metric, stem in _METRIC_FILE.items():
                path = self._dir / f"{gender.value}_{stem}.csv"
                if path.exists():
                    try:
                        self._tables[(gender, metric)] = LMSTable(pd.read_csv(path))
                        logger.info("Loaded WHO LMS %s/%s from %s", gender.value, metric, path.name)
                    except Exception as exc:  # noqa: BLE001
                        logger.warning("Skipping bad LMS file %s (%s)", path, exc)

    def available(self, gender: Gender, metric: str) -> bool:
        return (gender, metric) in self._tables

    def table(self, gender: Gender, metric: str) -> LMSTable | None:
        return self._tables.get((gender, metric))

    @property
    def is_active(self) -> bool:
        return bool(self._tables)


@lru_cache(maxsize=1)
def get_lms_provider() -> LMSProvider:
    """Cached provider; re-import to reload after adding files."""
    provider = LMSProvider()
    if provider.is_active:
        logger.info("WHO LMS engine active (%d tables)", len(provider._tables))
    else:
        logger.info("WHO LMS tables not found; using log-normal approximation")
    return provider
