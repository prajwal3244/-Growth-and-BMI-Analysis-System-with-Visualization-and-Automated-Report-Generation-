# Contributing to GrowthAI

Thanks for your interest in improving GrowthAI! 🩺

## Development setup

```bash
git clone <repo-url> && cd growthai
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
make install-dev
make test
```

## Ground rules

- **Clean architecture**: keep dependencies pointing inward (`core` depends on
  nothing; interfaces depend on services). Don't import FastAPI/Streamlit inside
  `core`, `ml`, `data` or `services`.
- **Type hints + docstrings** on all public functions.
- **Tests required** for new behavior. Run `make test` (target: keep coverage ≥ 85%).
- **Lint clean**: `make lint` (ruff) must pass.
- **No medical claims**: this is decision-support, not a medical device. Keep the
  disclaimer intact and avoid diagnostic language.

## Pull requests

1. Branch from `main`: `git checkout -b feat/short-description`.
2. Make focused commits with clear messages.
3. Ensure `make lint && make test` pass locally.
4. Open a PR describing **what** changed and **why**, linking any issue.

## Good first issues

- Replace the median-only reference with real WHO **LMS** percentile tables.
- Add a React frontend (see ROADMAP).
- Add SHAP visualizations to the Explainable-AI tab.
- Add more languages to the knowledge base.

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the system design.
