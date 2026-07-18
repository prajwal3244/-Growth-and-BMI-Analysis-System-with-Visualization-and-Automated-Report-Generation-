"""Interactive Plotly charts (feature #7).

Every function returns a ``plotly.graph_objects.Figure`` so the same chart can be
rendered live in Streamlit, embedded in the API response, or exported to a static
PNG for the PDF report. A shared medical theme keeps them visually consistent.
"""

from __future__ import annotations

import numpy as np
import plotly.graph_objects as go

from growthai.core.domain import Measurement, Standard
from growthai.data.reference import get_reference_service
from growthai.ml.forecast import ForecastPoint, GrowthForecaster
from growthai.services.risk_service import RiskReport

# Medical brand palette (used across dashboard, charts and PDF).
TEAL = "#12b3a6"
NAVY = "#0f2b46"
AMBER = "#f5a524"
RED = "#e5484d"
GREEN = "#30a46c"
GREY = "#8b98a5"

_LEVEL_COLOR = {"Low": GREEN, "Medium": AMBER, "High": RED}


def _base_layout(fig: go.Figure, title: str, height: int = 340, dark: bool = True) -> go.Figure:
    fig.update_layout(
        title=dict(text=title, font=dict(size=16)),
        template="plotly_dark" if dark else "plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=40, r=20, t=50, b=40),
        height=height,
        font=dict(family="Inter, Segoe UI, sans-serif"),
    )
    return fig


def bmi_gauge(bmi: float, category: str, dark: bool = True) -> go.Figure:
    """A gauge of BMI with clinically-shaded bands."""
    color = {"Underweight": AMBER, "Normal Weight": GREEN, "Overweight": AMBER, "Obesity": RED}.get(
        category, TEAL
    )
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=bmi,
            number={"suffix": " kg/m²", "font": {"size": 26}},
            gauge={
                "axis": {"range": [10, 40]},
                "bar": {"color": color, "thickness": 0.3},
                "steps": [
                    {"range": [10, 18.5], "color": "rgba(245,165,36,0.25)"},
                    {"range": [18.5, 25], "color": "rgba(48,163,108,0.30)"},
                    {"range": [25, 30], "color": "rgba(245,165,36,0.30)"},
                    {"range": [30, 40], "color": "rgba(229,72,77,0.30)"},
                ],
                "threshold": {"line": {"color": color, "width": 4}, "value": bmi},
            },
        )
    )
    return _base_layout(fig, f"BMI - {category}", dark=dark)


def health_radar(percentiles: dict[str, float], dark: bool = True) -> go.Figure:
    """Radar of key percentile indicators (height/weight/BMI)."""
    cats = list(percentiles.keys()) + [list(percentiles.keys())[0]]
    vals = list(percentiles.values()) + [list(percentiles.values())[0]]
    fig = go.Figure(
        go.Scatterpolar(r=vals, theta=cats, fill="toself", line=dict(color=TEAL))
    )
    fig.update_polars(radialaxis=dict(range=[0, 100]))
    return _base_layout(fig, "Health indicator radar (percentiles)", dark=dark)


def percentile_curve(
    m: Measurement, standard: Standard = Standard.WHO, metric: str = "height_cm", dark: bool = True
) -> go.Figure:
    """Reference median curve with the child plotted on it (feature #7)."""
    svc = get_reference_service(standard)
    df = svc.table(m.gender)
    label = {"height_cm": "Height (cm)", "weight_kg": "Weight (kg)", "bmi": "BMI"}[metric]
    child_val = {"height_cm": m.height_cm, "weight_kg": m.weight_kg, "bmi": m.bmi}[metric]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["age_months"] / 12, y=df[metric], mode="lines", name=f"{standard.value} median",
            line=dict(color=TEAL, width=3),
        )
    )
    # Shade an approximate normal channel (+/- ~2 z) for context.
    upper = df[metric] * np.exp(2 * 0.05)
    lower = df[metric] * np.exp(-2 * 0.05)
    fig.add_trace(
        go.Scatter(
            x=list(df["age_months"] / 12) + list(df["age_months"][::-1] / 12),
            y=list(upper) + list(lower[::-1]),
            fill="toself", fillcolor="rgba(18,179,166,0.12)",
            line=dict(width=0), name="Typical range", hoverinfo="skip",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[m.age_years], y=[child_val], mode="markers+text", name="This child",
            marker=dict(color=AMBER, size=14, line=dict(color="white", width=2)),
            text=["●"], textposition="top center",
        )
    )
    fig.update_xaxes(title="Age (years)")
    fig.update_yaxes(title=label)
    return _base_layout(fig, f"{label}-for-age ({standard.value})", height=380, dark=dark)


def growth_forecast_chart(
    m: Measurement, forecaster: GrowthForecaster, metric: str = "height_cm", dark: bool = True
) -> go.Figure:
    """Current value + forward forecast trajectory (feature #7: forecast graphs)."""
    traj: list[ForecastPoint] = forecaster.trajectory(m, months_ahead=24, step=3)
    label = {"height_cm": "Height (cm)", "weight_kg": "Weight (kg)", "bmi": "BMI"}[metric]
    getter = {
        "height_cm": lambda p: p.height_cm,
        "weight_kg": lambda p: p.weight_kg,
        "bmi": lambda p: p.bmi,
    }[metric]
    now_val = {"height_cm": m.height_cm, "weight_kg": m.weight_kg, "bmi": m.bmi}[metric]

    ages = [m.age_years] + [p.age_months / 12 for p in traj]
    vals = [now_val] + [getter(p) for p in traj]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[m.age_years], y=[now_val], mode="markers", name="Now",
                             marker=dict(color=AMBER, size=13)))
    fig.add_trace(go.Scatter(x=ages, y=vals, mode="lines+markers", name="Forecast",
                             line=dict(color=TEAL, width=3, dash="dot")))
    fig.update_xaxes(title="Age (years)")
    fig.update_yaxes(title=label)
    return _base_layout(fig, f"{label} forecast (next 24 months)", dark=dark)


def risk_bar(report: RiskReport, dark: bool = True) -> go.Figure:
    """Horizontal risk chart coloured by level."""
    names = [r.name for r in report.risks]
    scores = [r.level.score for r in report.risks]
    colors = [_LEVEL_COLOR[r.level.value] for r in report.risks]
    fig = go.Figure(
        go.Bar(x=scores, y=names, orientation="h", marker_color=colors,
               text=[r.level.value for r in report.risks], textposition="auto")
    )
    fig.update_xaxes(title="Risk level", tickvals=[1, 2, 3], ticktext=["Low", "Medium", "High"], range=[0, 3.3])
    return _base_layout(fig, f"Health risk profile - overall {report.overall_level.value}", dark=dark)


def feature_importance_bar(importance: dict[str, float], dark: bool = True) -> go.Figure:
    """Explainable-AI feature importance chart (feature #5)."""
    labels = {"age_months": "Age", "sex_male": "Sex"}
    names = [labels.get(k, k) for k in importance]
    fig = go.Figure(
        go.Bar(x=list(importance.values()), y=names, orientation="h", marker_color=NAVY)
    )
    fig.update_xaxes(title="Relative importance", range=[0, 1])
    return _base_layout(fig, "Why this prediction (feature importance)", height=260, dark=dark)


def population_age_distribution(ages_years: list[float], dark: bool = True) -> go.Figure:
    """Analytics: age distribution histogram (feature #18)."""
    fig = go.Figure(go.Histogram(x=ages_years, nbinsx=20, marker_color=TEAL))
    fig.update_xaxes(title="Age (years)")
    fig.update_yaxes(title="Count")
    return _base_layout(fig, "Population age distribution", dark=dark)
