"""GrowthAI dashboard (feature #1).

A polished, dark-mode Streamlit interface that calls the domain services
directly (no HTTP round-trip needed for the demo) and renders the same Plotly
charts used in the API and PDF. Run with:

    streamlit run frontend/streamlit_app.py

The app is intentionally single-file for portability but organized into clear
sections (sidebar inputs -> KPI cards -> tabs). It shares the medical palette
with the charts module for a consistent brand.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Make the src/ package importable when run via `streamlit run`.
_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import streamlit as st

from _accessibility import accessibility_controls, apply_accessibility, speak
from growthai import __version__
from growthai.chatbot.providers import get_chat_provider
from growthai.core.domain import Gender, Measurement, Standard
from growthai.core.exceptions import InvalidMeasurementError
from growthai.services.growth_service import GrowthService
from growthai.services.nutrition_service import NutritionService
from growthai.services.risk_service import RiskService
from growthai.viz import charts

st.set_page_config(page_title="GrowthAI - Health Intelligence", page_icon="🩺", layout="wide")

# ---- theme / CSS ----------------------------------------------------------
TEAL, NAVY, AMBER, RED, GREEN = "#12b3a6", "#0f2b46", "#f5a524", "#e5484d", "#30a46c"
st.markdown(
    f"""
    <style>
      .stApp {{ background: linear-gradient(160deg,#0b1622 0%, #0f2233 100%); }}
      .block-container {{ padding-top: 1.5rem; }}
      h1,h2,h3,h4 {{ font-family: 'Inter','Segoe UI',sans-serif; }}
      .hero {{ display:flex; align-items:center; gap:14px; }}
      .hero .logo {{ font-size:34px; font-weight:800; color:#e8f6f4; letter-spacing:-1px; }}
      .hero .logo span {{ color:{TEAL}; }}
      .hero .tag {{ color:#8b98a5; font-size:13px; letter-spacing:2px; }}
      .kpi {{ background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.08);
             border-radius:16px; padding:16px 18px; }}
      .kpi .k {{ color:#8b98a5; font-size:11px; text-transform:uppercase; letter-spacing:1px; }}
      .kpi .v {{ color:#fff; font-size:28px; font-weight:700; }}
      .pill {{ display:inline-block; padding:3px 12px; border-radius:999px; font-weight:700;
              font-size:13px; color:#fff; }}
      .low,.normal {{ background:{GREEN}; }} .medium,.overweight,.underweight {{ background:{AMBER}; }}
      .high,.obesity {{ background:{RED}; }}
      .card {{ background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.08);
              border-radius:16px; padding:18px; }}
    </style>
    """,
    unsafe_allow_html=True,
)

_PILL = {"Underweight": "underweight", "Normal Weight": "normal", "Overweight": "overweight", "Obesity": "obesity"}


def kpi(col, label: str, value: str) -> None:
    col.markdown(f'<div class="kpi"><div class="k">{label}</div><div class="v">{value}</div></div>', unsafe_allow_html=True)


# ---- header ---------------------------------------------------------------
st.markdown(
    f'<div class="hero"><div class="logo">Growth<span>AI</span></div>'
    f'<div class="tag">HEALTH INTELLIGENCE PLATFORM &nbsp;·&nbsp; v{__version__}</div></div>',
    unsafe_allow_html=True,
)
st.caption("AI-powered growth analysis, forecasting, nutrition & risk intelligence for children and young adults.")

# ---- sidebar inputs -------------------------------------------------------
with st.sidebar:
    st.header("👶 Child details")
    name = st.text_input("Name", "Aarav Sharma")
    gender_label = st.radio("Gender", ["Male", "Female"], horizontal=True)
    age_unit = st.radio("Age unit", ["Years", "Months"], horizontal=True)
    age_val = st.number_input("Age", min_value=0.0, max_value=240.0, value=8.0, step=0.5)
    age_months = age_val if age_unit == "Months" else age_val * 12
    height_cm = st.number_input("Height (cm)", min_value=30.0, max_value=230.0, value=128.0, step=0.5)
    weight_kg = st.number_input("Weight (kg)", min_value=1.0, max_value=300.0, value=26.0, step=0.5)
    standard = st.selectbox("Reference standard", [s.value for s in Standard], index=0)
    st.caption("Switch between WHO, CDC and IAP (Indian) standards.")
    go = st.button("🔬 Analyze", use_container_width=True, type="primary")

# Accessibility panel (feature #19) - large fonts, color-blind mode, text-to-speech.
a11y = accessibility_controls()
apply_accessibility(a11y)

gender = Gender.MALE if gender_label == "Male" else Gender.FEMALE

# ---- run analysis ---------------------------------------------------------
try:
    measurement = Measurement(age_months=age_months, height_cm=height_cm, weight_kg=weight_kg, gender=gender)
except InvalidMeasurementError as exc:
    st.error(f"Invalid input: {exc}")
    st.stop()

std = Standard(standard)
growth = GrowthService(std)
analysis = growth.analyze(measurement)
a = analysis.assessment
nutrition = NutritionService().recommend(measurement, a.category)
risk = RiskService().assess(measurement, a.category, a.z_score, analysis.forecasts)

# ---- KPI row --------------------------------------------------------------
c1, c2, c3, c4, c5 = st.columns(5)
kpi(c1, "BMI", f"{a.bmi}")
c2.markdown(f'<div class="kpi"><div class="k">Category</div><div class="v"><span class="pill {_PILL[a.category.value]}">{a.category.value}</span></div></div>', unsafe_allow_html=True)
kpi(c3, "Percentile", f"{a.percentile:.0f}")
kpi(c4, "BMI z-score", f"{a.z_score:+.2f}")
c5.markdown(f'<div class="kpi"><div class="k">Overall risk</div><div class="v"><span class="pill {risk.overall_level.value.lower()}">{risk.overall_level.value}</span></div></div>', unsafe_allow_html=True)

st.write("")

# ---- tabs -----------------------------------------------------------------
t_over, t_forecast, t_risk, t_nutrition, t_explain, t_chat = st.tabs(
    ["📊 Overview", "🔮 Forecast", "⚠️ Risk", "🥗 Nutrition", "🧠 Explainable AI", "💬 Assistant"]
)

with t_over:
    col1, col2 = st.columns(2)
    col1.plotly_chart(charts.bmi_gauge(a.bmi, a.category.value), use_container_width=True)
    percentiles = {
        "Height": growth.reference.percentile(gender, age_months, "height", height_cm),
        "Weight": growth.reference.percentile(gender, age_months, "weight", weight_kg),
        "BMI": a.percentile,
    }
    col2.plotly_chart(charts.health_radar(percentiles), use_container_width=True)
    metric = st.selectbox("Percentile curve metric", ["height_cm", "weight_kg", "bmi"], format_func=lambda m: {"height_cm": "Height", "weight_kg": "Weight", "bmi": "BMI"}[m])
    st.plotly_chart(charts.percentile_curve(measurement, std, metric), use_container_width=True)

with t_forecast:
    st.subheader("AI growth forecast")
    fc = st.columns(len(analysis.forecasts))
    for col, f in zip(fc, analysis.forecasts):
        col.markdown(
            f'<div class="card"><div class="k" style="color:#8b98a5">{f.horizon_label}</div>'
            f'<div style="font-size:22px;color:#fff;font-weight:700">{f.height_cm:.0f} cm · {f.weight_kg:.0f} kg</div>'
            f'<div style="color:{TEAL}">BMI {f.bmi:.1f} · confidence {f.confidence:.0f}%</div></div>',
            unsafe_allow_html=True,
        )
    fmetric = st.selectbox("Forecast metric", ["height_cm", "weight_kg", "bmi"], key="fm", format_func=lambda m: {"height_cm": "Height", "weight_kg": "Weight", "bmi": "BMI"}[m])
    st.plotly_chart(charts.growth_forecast_chart(measurement, growth.forecaster, fmetric), use_container_width=True)
    st.markdown("##### Model comparison (why we trust the forecast)")
    st.dataframe(growth.forecaster.model_comparison()["height_cm"], use_container_width=True)

with t_risk:
    st.plotly_chart(charts.risk_bar(risk), use_container_width=True)
    for r in risk.risks:
        st.markdown(f'**{r.name}** — <span class="pill {r.level.value.lower()}">{r.level.value}</span>', unsafe_allow_html=True)
        st.caption(r.explanation)

with t_nutrition:
    d = nutrition.as_dict()["daily_targets"]
    cols = st.columns(5)
    for col, (k, v) in zip(cols, d.items()):
        kpi(col, k.replace("_", " ").replace(" g", "").replace(" kcal", "").replace(" ml", ""), str(v))
    st.markdown("##### Lifestyle")
    st.json(nutrition.as_dict()["lifestyle"])
    st.markdown("##### Recommended foods")
    for food in nutrition.food_suggestions:
        st.markdown(f"- {food}")
    st.markdown("##### Weekly meal plan")
    st.dataframe(nutrition.weekly_meal_plan, use_container_width=True)

with t_explain:
    ex = analysis.explanation
    st.info(ex.summary)
    speak(ex.summary, a11y["tts"])  # read the result aloud when enabled (feature #19)
    st.plotly_chart(charts.feature_importance_bar(ex.feature_importance), use_container_width=True)
    st.markdown("##### Why this prediction")
    for driver in ex.drivers:
        st.markdown(f"- {driver}")
    st.caption(f"SHAP available: {ex.shap_available} · Confidence: {ex.confidence:.0f}%")

with t_chat:
    st.subheader("💬 AI health assistant")
    st.caption("Grounded in WHO/CDC guidelines · works fully offline.")
    if "chat" not in st.session_state:
        st.session_state.chat = []
    for role, msg in st.session_state.chat:
        with st.chat_message(role):
            st.markdown(msg)
    prompt = st.chat_input("Ask about BMI, nutrition, height, sleep, risk…")
    if prompt:
        st.session_state.chat.append(("user", prompt))
        with st.chat_message("user"):
            st.markdown(prompt)
        resp = get_chat_provider().ask(prompt)
        answer = resp.answer + (f"\n\n*Sources: {', '.join(resp.sources)}*" if resp.sources else "")
        st.session_state.chat.append(("assistant", answer))
        with st.chat_message("assistant"):
            st.markdown(answer)

st.divider()
_method = "WHO LMS (exact)" if growth.reference.uses_lms else "log-normal approximation"
st.caption(
    f"Reference method: **{_method}** · Standard: **{std.value}**. "
    "Add official WHO LMS tables to `datasets/who/lms/` to enable exact z-scores."
)
st.caption("⚕️ GrowthAI is an educational decision-support tool, not a medical device. Always consult a paediatrician.")
