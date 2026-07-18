"""Feature engineering & training-data synthesis for growth models.

The raw reference set has only ~43 median points per gender — enough to draw a
curve, but too few (and too clean) to train and *honestly evaluate* regression
models. We therefore synthesize a realistic training frame by sampling, at each
age, a spread of individuals across the percentile range using the reference
engine's log-normal variance model. This is a standard data-augmentation
technique and is fully deterministic (seeded) for reproducibility.

Each row = one simulated individual:  (age_months, sex_male) -> height_cm / weight_kg.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from growthai.core.domain import Gender, Standard
from growthai.data.reference import _CV, get_reference_service

# Percentile z-scores sampled per age to build a spread of individuals.
_Z_GRID = np.array([-2.0, -1.5, -1.0, -0.5, 0.0, 0.5, 1.0, 1.5, 2.0])
_SEED = 42


def build_training_frame(standard: Standard = Standard.WHO, jitter: float = 0.35) -> pd.DataFrame:
    """Return a tidy training frame for growth regression.

    Columns: ``age_months``, ``sex_male`` (0/1), ``height_cm``, ``weight_kg``, ``bmi``.
    ``jitter`` adds small Gaussian noise so models cannot trivially memorize the grid.
    """
    rng = np.random.default_rng(_SEED)
    svc = get_reference_service(standard)
    rows: list[dict[str, float]] = []

    for gender in Gender:
        ref = svc.table(gender)
        sex_male = 1.0 if gender is Gender.MALE else 0.0
        # Interpolate onto a fine monthly axis for a denser, smoother curve.
        ages = np.arange(0, ref["age_months"].max() + 1, 1.0)
        med_h = np.interp(ages, ref["age_months"], ref["height_cm"])
        med_w = np.interp(ages, ref["age_months"], ref["weight_kg"])
        for age, mh, mw in zip(ages, med_h, med_w, strict=False):
            for z in _Z_GRID:
                # Log-normal spread around the median (matches reference.z_score).
                h = mh * float(np.exp(z * _CV["height"]))
                w = mw * float(np.exp(z * _CV["weight"]))
                h += rng.normal(0, jitter)
                w += rng.normal(0, jitter * 0.15)
                rows.append(
                    {
                        "age_months": float(age),
                        "sex_male": sex_male,
                        "height_cm": round(h, 2),
                        "weight_kg": round(max(w, 0.5), 3),
                        "bmi": round(w / ((h / 100.0) ** 2), 2),
                    }
                )
    return pd.DataFrame(rows)


FEATURE_COLUMNS = ["age_months", "sex_male"]
