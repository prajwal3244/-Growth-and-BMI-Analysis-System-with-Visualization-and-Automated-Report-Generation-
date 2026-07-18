"""Tests for the WHO LMS engine and population analytics."""

from __future__ import annotations

import math

import pandas as pd
import pytest

from growthai.core.domain import Gender, Standard
from growthai.data.lms import LMSProvider, LMSTable
from growthai.data.reference import get_reference_service
from growthai.services.analytics_service import AnalyticsService


def test_lms_zscore_matches_closed_form():
    # L=1, M=16, S=0.1 -> z = ((X/M)^1 - 1)/(1*0.1) = (X/16 - 1)*10
    t = LMSTable(pd.DataFrame({"age_months": [60, 120], "L": [1.0, 1.0], "M": [16.0, 16.0], "S": [0.1, 0.1]}))
    assert t.z_score(90, 16.0) == pytest.approx(0.0)
    assert t.z_score(90, 17.6) == pytest.approx(1.0, abs=1e-6)
    assert t.percentile(90, 16.0) == pytest.approx(50.0, abs=0.1)


def test_lms_handles_l_equals_zero_branch():
    t = LMSTable(pd.DataFrame({"age_months": [60, 120], "L": [0.0, 0.0], "M": [16.0, 16.0], "S": [0.1, 0.1]}))
    # z = ln(X/M)/S; choose X so ln(X/M)=0.1 -> z=1
    assert t.z_score(90, 16 * math.exp(0.1)) == pytest.approx(1.0, abs=1e-6)


def test_lms_table_requires_columns():
    with pytest.raises(ValueError):
        LMSTable(pd.DataFrame({"age_months": [1], "M": [16.0]}))


def test_lms_provider_inactive_without_files(tmp_path):
    provider = LMSProvider(lms_dir=tmp_path)  # empty dir
    assert provider.is_active is False
    assert provider.available(Gender.MALE, "bmi") is False


def test_reference_falls_back_without_lms():
    svc = get_reference_service(Standard.WHO)
    # No official LMS files committed -> approximation is used, but still works.
    assert svc.uses_lms is False
    assert isinstance(svc.z_score(Gender.MALE, 120, "bmi", 17.0), float)


def test_analytics_synthetic_cohort_is_reasonable():
    svc = AnalyticsService(Standard.WHO)
    insights = svc.insights(n=300)
    assert insights.is_synthetic is True
    assert insights.count == 300
    assert 12 < insights.average_bmi < 30
    # Categories should sum back to the cohort size.
    assert sum(insights.category_distribution().values()) == 300
    assert set(insights.gender_average_bmi()) <= {"male", "female"}


def test_analytics_uses_stored_data_when_available():
    svc = AnalyticsService(Standard.WHO)
    stored = pd.DataFrame(
        {
            "gender": ["male"] * 15,
            "age_years": [8.0] * 15,
            "bmi": [16.0] * 15,
            "category": ["Normal Weight"] * 15,
        }
    )
    insights = svc.insights(stored=stored)
    assert insights.is_synthetic is False
    assert insights.count == 15
