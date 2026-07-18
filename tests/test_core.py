"""Tests for core domain and BMI logic (including the original bugs, now fixed)."""

from __future__ import annotations

import pytest

from growthai.core.bmi import classify_bmi_adult, classify_bmi_for_age
from growthai.core.domain import BmiCategory, Gender, Measurement
from growthai.core.exceptions import InvalidMeasurementError


def test_gender_parse_accepts_original_cli_inputs():
    assert Gender.parse("M") is Gender.MALE
    assert Gender.parse("f") is Gender.FEMALE
    assert Gender.parse("Female") is Gender.FEMALE
    with pytest.raises(InvalidMeasurementError):
        Gender.parse("x")


def test_bmi_uses_correct_si_units():
    m = Measurement(age_months=120, height_cm=140, weight_kg=35, gender=Gender.MALE)
    # 35 / 1.4^2 = 17.86
    assert m.bmi == pytest.approx(17.86, abs=0.01)


def test_measurement_rejects_impossible_values():
    with pytest.raises(InvalidMeasurementError):
        Measurement(age_months=300, height_cm=140, weight_kg=35, gender=Gender.MALE)
    with pytest.raises(InvalidMeasurementError):
        Measurement(age_months=120, height_cm=5, weight_kg=35, gender=Gender.MALE)


def test_adult_classification_has_no_boundary_gaps():
    # The original code left 24.9-25.0 and 29.9-30.0 unclassified -> Obesity.
    assert classify_bmi_adult(24.95) is BmiCategory.NORMAL
    assert classify_bmi_adult(25.0) is BmiCategory.OVERWEIGHT
    assert classify_bmi_adult(29.95) is BmiCategory.OVERWEIGHT
    assert classify_bmi_adult(30.0) is BmiCategory.OBESE


def test_child_classification_by_zscore():
    assert classify_bmi_for_age(-2.5) is BmiCategory.UNDERWEIGHT
    assert classify_bmi_for_age(0.0) is BmiCategory.NORMAL
    assert classify_bmi_for_age(1.5) is BmiCategory.OVERWEIGHT
    assert classify_bmi_for_age(2.5) is BmiCategory.OBESE
