"""GrowthAI — AI-powered growth, nutrition, risk & forecasting health platform.

A production-grade evolution of the original *Growth and BMI Analysis System*.
The public surface intentionally re-exports the most common building blocks so
consumers can ``from growthai import analyze, Measurement`` without knowing the
internal module layout.
"""

from __future__ import annotations

__version__ = "1.0.0"

from growthai.core.domain import BmiCategory, Gender, Measurement, Standard

__all__ = ["__version__", "Gender", "Standard", "BmiCategory", "Measurement"]
