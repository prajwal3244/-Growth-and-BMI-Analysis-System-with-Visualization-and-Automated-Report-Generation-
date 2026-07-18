"""Tests for the ML forecaster and the nutrition/risk services."""

from __future__ import annotations

from growthai.core.domain import BmiCategory, Gender, Measurement, Standard
from growthai.services.growth_service import GrowthService
from growthai.services.nutrition_service import NutritionService
from growthai.services.risk_service import RiskLevel, RiskService


def _child() -> Measurement:
    return Measurement(age_months=96, height_cm=128, weight_kg=26, gender=Gender.MALE)


def test_forecast_projects_future_growth():
    svc = GrowthService(Standard.WHO)
    analysis = svc.analyze(_child())
    assert len(analysis.forecasts) == 2
    six_mo, one_yr = analysis.forecasts
    # Children grow: later forecast should be taller than the earlier one.
    assert one_yr.height_cm > six_mo.height_cm > _child().height_cm
    assert 0 <= one_yr.confidence <= 100


def test_model_comparison_reports_all_models():
    svc = GrowthService(Standard.WHO)
    comparison = svc.forecaster.model_comparison()
    names = {row["name"] for row in comparison["height_cm"]}
    assert {"RandomForest", "GradientBoosting", "LinearRegression"}.issubset(names)


def test_explanation_present_and_confident():
    svc = GrowthService(Standard.WHO)
    analysis = svc.analyze(_child())
    ex = analysis.explanation
    assert ex.summary
    assert ex.drivers
    assert 0 <= ex.confidence <= 100


def test_nutrition_scales_with_bmi_category():
    m = _child()
    ns = NutritionService()
    normal = ns.daily_calories(m, BmiCategory.NORMAL)
    obese = ns.daily_calories(m, BmiCategory.OBESE)
    under = ns.daily_calories(m, BmiCategory.UNDERWEIGHT)
    assert under > normal > obese
    plan = ns.recommend(m, BmiCategory.NORMAL)
    assert len(plan.weekly_meal_plan) == 7
    assert plan.protein_g > 0 and plan.water_ml >= 1000


def test_risk_report_flags_obesity_and_respects_worst_case():
    m = Measurement(age_months=144, height_cm=150, weight_kg=62, gender=Gender.FEMALE)
    svc = GrowthService(Standard.WHO)
    analysis = svc.analyze(m)
    a = analysis.assessment
    report = RiskService().assess(m, a.category, a.z_score, analysis.forecasts)
    obesity = next(r for r in report.risks if r.name == "Obesity")
    assert obesity.level is RiskLevel.HIGH
    # A HIGH individual risk must not be diluted to an overall LOW.
    assert report.overall_level is not RiskLevel.LOW
    assert all(r.explanation for r in report.risks)
