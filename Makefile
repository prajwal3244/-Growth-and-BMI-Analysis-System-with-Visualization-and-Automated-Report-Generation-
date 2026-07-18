.PHONY: help install install-dev test lint format run-api run-dashboard docker-up docker-down train clean

help:
	@echo "GrowthAI - common commands"
	@echo "  make install-dev    Install dev + runtime dependencies (editable)"
	@echo "  make test           Run the test suite with coverage"
	@echo "  make lint           Ruff lint"
	@echo "  make run-api        Start the FastAPI backend (http://localhost:8000/docs)"
	@echo "  make run-dashboard  Start the Streamlit dashboard (http://localhost:8501)"
	@echo "  make docker-up      Start API + dashboard + Postgres via docker compose"
	@echo "  make train          (Re)train and cache the ML models"

install:
	pip install -r requirements.txt && pip install -e .

install-dev:
	pip install -r requirements-dev.txt && pip install -e .

test:
	pytest

lint:
	ruff check src tests

format:
	ruff check --fix src tests

run-api:
	uvicorn growthai.api.main:app --reload --port 8000

run-dashboard:
	streamlit run frontend/streamlit_app.py

docker-up:
	docker compose up --build

docker-down:
	docker compose down

train:
	python -c "from growthai.ml.models import get_growth_regressor as g; g('height_cm', retrain=True); g('weight_kg', retrain=True); print('models trained')"

clean:
	rm -rf .pytest_cache .ruff_cache .mypy_cache htmlcov coverage.xml *.db ml/artifacts/*.joblib
