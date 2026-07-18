"""Population analytics page (feature #18).

Shows average BMI, category distribution, age distribution, gender comparison
and the overweight/obesity trend across a cohort. Uses stored analyses when
available, otherwise a clearly-labelled synthetic cohort.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[2] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
_FRONTEND = Path(__file__).resolve().parents[1]
if str(_FRONTEND) not in sys.path:
    sys.path.insert(0, str(_FRONTEND))

import streamlit as st

from _accessibility import accessibility_controls, apply_accessibility
from growthai.core.domain import Standard
from growthai.services.analytics_service import AnalyticsService
from growthai.viz import charts

st.set_page_config(page_title="GrowthAI · Analytics", page_icon="📈", layout="wide")
apply_accessibility(accessibility_controls())

st.title("📈 Population analytics")
st.caption("Aggregate growth & BMI insights across a cohort (feature #18).")

standard = st.sidebar.selectbox("Reference standard", [s.value for s in Standard], index=0)
n = st.sidebar.slider("Synthetic cohort size", 100, 2000, 500, step=100)

svc = AnalyticsService(Standard(standard))
insights = svc.insights(n=n)

if insights.is_synthetic:
    st.info(
        f"Showing a **synthetic cohort** of {insights.count} children generated from the "
        f"{standard} reference curves. Once real analyses are stored via the API, they are used instead."
    )

c1, c2, c3 = st.columns(3)
c1.metric("Cohort size", insights.count)
c2.metric("Average BMI", insights.average_bmi)
obese_share = sum(v for k, v in insights.category_distribution().items() if k in ("Overweight", "Obesity"))
c3.metric("Overweight + obese", f"{100 * obese_share / insights.count:.0f}%")

col1, col2 = st.columns(2)
col1.plotly_chart(charts.category_distribution_pie(insights.category_distribution()), use_container_width=True)
col2.plotly_chart(charts.gender_bmi_comparison(insights.gender_average_bmi()), use_container_width=True)

col3, col4 = st.columns(2)
col3.plotly_chart(
    charts.population_age_distribution(insights.frame["age_years"].tolist()), use_container_width=True
)
trend = insights.obesity_rate_by_age()
col4.plotly_chart(
    charts.obesity_trend(trend["age_band"].tolist(), trend["rate_pct"].tolist()), use_container_width=True
)

with st.expander("View raw cohort data"):
    st.dataframe(insights.frame, use_container_width=True)

st.divider()
st.caption("⚕️ Educational analytics only. Synthetic data is generated from reference curves for demonstration.")
