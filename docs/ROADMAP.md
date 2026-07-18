# Roadmap

Legend: ✅ shipped · 🚧 in progress · 🔭 planned

## Shipped (this repository)
- ✅ Clean-architecture foundation, config, logging, packaging
- ✅ Fixed & clinically-improved BMI + age/gender z-score classification
- ✅ Multi-standard reference engine (WHO · CDC · IAP) with runtime switching
- ✅ AI growth forecasting (RandomForest / GradientBoosting / LinearRegression) with model comparison
- ✅ 6-month & 1-year growth forecasts with confidence
- ✅ Explainable AI: feature importance + natural-language explanations (+ optional SHAP)
- ✅ Nutrition intelligence: calories, macros, water, sleep, activity, screen time, meal plans
- ✅ Multi-risk analysis with Low/Medium/High scoring and explanations
- ✅ Interactive Plotly charts: gauge, radar, percentile curve, growth timeline, forecast
- ✅ Hospital-grade PDF report with QR code
- ✅ Offline RAG health assistant over WHO guidelines + pluggable LLM adapter
- ✅ FastAPI backend: JWT auth, CRUD, Swagger docs
- ✅ SQLAlchemy models (SQLite dev / Postgres prod)
- ✅ Streamlit dashboard: dark mode, cards, charts, analytics, chatbot
- ✅ **WHO LMS reference engine** (exact L/M/S z-scores) with auto-activation + fetch script
- ✅ **Population analytics dashboard** (avg BMI, category/age distribution, gender, obesity trend)
- ✅ **Accessibility**: large fonts, color-blind-safe palette, offline text-to-speech, dark mode
- ✅ Pytest suite (33 tests), Docker, docker-compose, GitHub Actions CI

## Planned
- 🔭 React + Next.js public frontend (Streamlit becomes clinician/admin console)
- 🔭 Ship the full official WHO LMS tables via `scripts/fetch_who_lms.py` in CI
- 🔭 Wearable & IoT integration: Google Fit, Apple Health, smart scales
- 🔭 Mobile app (React Native / Flutter)
- 🔭 Multi-language support + speech-to-text input
- 🔭 Population analytics warehouse + admin BI dashboards
- 🔭 Model registry + MLflow experiment tracking
- 🔭 Cloud deploy templates: Render, Railway, Azure, AWS

## Non-goals
- This is **not** a medical device and must not be used for diagnosis. See the disclaimer in the README.
