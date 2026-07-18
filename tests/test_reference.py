"""Tests for the reference-data engine and multi-standard support."""

from __future__ import annotations

import pytest

from growthai.core.domain import Gender, Standard
from growthai.data.reference import get_reference_service, parse_age


@pytest.mark.parametrize(
    "raw,expected",
    [("0Months", 0.0), ("6Months", 6.0), ("2Years", 24.0), ("20Years", 240.0), ("junk", None)],
)
def test_parse_age(raw, expected):
    assert parse_age(raw) == expected


def test_reference_parses_all_rows():
    svc = get_reference_service(Standard.WHO)
    for gender in Gender:
        df = svc.table(gender)
        assert len(df) >= 40
        assert {"age_months", "height_cm", "weight_kg", "bmi"}.issubset(df.columns)


def test_median_interpolation_is_monotonic_for_height():
    svc = get_reference_service(Standard.WHO)
    h5 = svc.median(Gender.MALE, 60, "height_cm")
    h10 = svc.median(Gender.MALE, 120, "height_cm")
    assert h10 > h5 > 0


def test_zscore_and_percentile_consistency():
    svc = get_reference_service(Standard.WHO)
    median_bmi = svc.median(Gender.MALE, 120, "bmi")
    # A value exactly at the median must have z ~ 0 and percentile ~ 50.
    assert svc.z_score(Gender.MALE, 120, "bmi", median_bmi) == pytest.approx(0.0, abs=1e-6)
    assert svc.percentile(Gender.MALE, 120, "bmi", median_bmi) == pytest.approx(50.0, abs=0.5)


def test_standards_produce_different_curves():
    who = get_reference_service(Standard.WHO)
    iap = get_reference_service(Standard.IAP)
    assert who.median(Gender.MALE, 120, "weight_kg") != iap.median(Gender.MALE, 120, "weight_kg")
