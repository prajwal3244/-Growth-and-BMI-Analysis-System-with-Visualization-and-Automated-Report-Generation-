"""Growth regressors with transparent model comparison.

Trains RandomForest, GradientBoosting and LinearRegression for a target
(height or weight) and reports honest hold-out metrics so the dashboard can
show *why* a model was chosen. The best model (by R²) is retained for inference.

Design notes
------------
* One :class:`GrowthRegressor` per target keeps responsibilities single (SRP).
* Models are pluggable via ``_MODEL_FACTORY`` — add XGBoost by adding one entry.
* Artifacts persist with joblib so training happens once, not per request.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.base import RegressorMixin
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split

from growthai.config import get_settings
from growthai.core.exceptions import ModelNotTrainedError
from growthai.logging_conf import get_logger
from growthai.ml.features import FEATURE_COLUMNS, build_training_frame

logger = get_logger("ml.models")

_MODEL_FACTORY: dict[str, Callable[[], RegressorMixin]] = {
    "RandomForest": lambda: RandomForestRegressor(
        n_estimators=200, max_depth=12, random_state=42, n_jobs=-1
    ),
    "GradientBoosting": lambda: GradientBoostingRegressor(random_state=42),
    "LinearRegression": lambda: LinearRegression(),
}

# XGBoost is optional (feature #2 marks it optional). Register it only if present.
try:  # pragma: no cover - optional dependency
    from xgboost import XGBRegressor

    _MODEL_FACTORY["XGBoost"] = lambda: XGBRegressor(
        n_estimators=300, max_depth=5, learning_rate=0.05, random_state=42, n_jobs=-1
    )
except Exception:  # noqa: BLE001
    pass


@dataclass
class ModelScore:
    """Hold-out evaluation for one candidate model."""

    name: str
    r2: float
    mae: float

    def as_dict(self) -> dict[str, float | str]:
        return {"name": self.name, "r2": round(self.r2, 4), "mae": round(self.mae, 3)}


@dataclass
class GrowthRegressor:
    """Trains & compares models for a single target column."""

    target: str  # "height_cm" or "weight_kg"
    best_model: RegressorMixin | None = None
    best_name: str = ""
    scores: list[ModelScore] = field(default_factory=list)

    def train(self, frame: pd.DataFrame | None = None) -> GrowthRegressor:
        frame = build_training_frame() if frame is None else frame
        X = frame[FEATURE_COLUMNS].to_numpy()
        y = frame[self.target].to_numpy()
        X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42)

        self.scores = []
        best_r2 = -np.inf
        for name, factory in _MODEL_FACTORY.items():
            model = factory()
            model.fit(X_tr, y_tr)
            preds = model.predict(X_te)
            score = ModelScore(name, r2_score(y_te, preds), mean_absolute_error(y_te, preds))
            self.scores.append(score)
            logger.info("[%s] %s R2=%.4f MAE=%.3f", self.target, name, score.r2, score.mae)
            if score.r2 > best_r2:
                best_r2, self.best_model, self.best_name = score.r2, model, name

        # Refit the winner on ALL data for best inference quality.
        self.best_model = _MODEL_FACTORY[self.best_name]()
        self.best_model.fit(X, y)
        return self

    def predict(self, age_months: float, sex_male: float) -> float:
        if self.best_model is None:
            raise ModelNotTrainedError(f"GrowthRegressor({self.target}) not trained")
        return float(self.best_model.predict([[age_months, sex_male]])[0])

    def feature_importance(self) -> dict[str, float]:
        """Normalized importance of each input feature for the winning model."""
        if self.best_model is None:
            raise ModelNotTrainedError(f"GrowthRegressor({self.target}) not trained")
        if hasattr(self.best_model, "feature_importances_"):
            imp = np.asarray(self.best_model.feature_importances_, dtype=float)
        elif hasattr(self.best_model, "coef_"):
            imp = np.abs(np.asarray(self.best_model.coef_, dtype=float)).ravel()
        else:  # pragma: no cover
            imp = np.ones(len(FEATURE_COLUMNS))
        total = imp.sum() or 1.0
        return {f: round(float(v / total), 4) for f, v in zip(FEATURE_COLUMNS, imp, strict=False)}

    @property
    def best_score(self) -> ModelScore | None:
        return next((s for s in self.scores if s.name == self.best_name), None)

    # ---- persistence ---------------------------------------------------

    def save(self, path: Path) -> None:
        joblib.dump(self, path)

    @classmethod
    def load(cls, path: Path) -> GrowthRegressor:
        return joblib.load(path)


def _artifact_path(target: str) -> Path:
    return get_settings().ml_artifacts_dir / f"growth_{target}.joblib"


def get_growth_regressor(target: str, retrain: bool = False) -> GrowthRegressor:
    """Return a trained regressor, loading from disk when available."""
    path = _artifact_path(target)
    if path.exists() and not retrain:
        try:
            return GrowthRegressor.load(path)
        except Exception:  # noqa: BLE001 - corrupt/old artifact -> retrain
            logger.warning("Could not load %s; retraining", path)
    reg = GrowthRegressor(target=target).train()
    reg.save(path)
    return reg
