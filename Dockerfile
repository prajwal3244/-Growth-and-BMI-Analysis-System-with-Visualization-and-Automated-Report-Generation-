# ---- GrowthAI production image -------------------------------------------
# Debian-slim base so WeasyPrint's native GTK/Pango/Cairo libraries are
# available and PDF generation works (unlike bare Windows/macOS hosts).
FROM python:3.11-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# System libraries required by WeasyPrint (PDF) and general builds.
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libpango-1.0-0 libpangocairo-1.0-0 libcairo2 \
        libgdk-pixbuf-2.0-0 libffi-dev shared-mime-info fonts-dejavu \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN pip install -e .

# Pre-train the ML models at build time so the first request is fast.
RUN python -c "from growthai.ml.models import get_growth_regressor; \
    get_growth_regressor('height_cm', retrain=True); \
    get_growth_regressor('weight_kg', retrain=True)"

EXPOSE 8000 8501

# Default: run the API. docker-compose overrides the command for the dashboard.
CMD ["uvicorn", "growthai.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
