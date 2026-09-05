"""
ML Training Pipeline
──────────────────────
Trains and saves:
  1. Anomaly Detection  — Isolation Forest on multi-param sensor data
  2. Forecasting        — Linear Regression per parameter (pm25, pm10, so2, no2, co)
  3. Risk Scoring       — Rule-based calibration with joblib-persisted weights

Models are saved to /ml/models/ using joblib.

Run directly:
    python pollution-platform/ml/training/train_models.py
"""

from __future__ import annotations

import logging
import os
import sys

# Allow imports from the project root
PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import numpy as np

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")

# ── Paths ────────────────────────────────────────────────────────────────────
MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "models")
os.makedirs(MODEL_DIR, exist_ok=True)

# Parameters with dedicated forecasting models
FORECAST_PARAMS = ["pm25", "pm10", "so2", "no2", "co", "turbidity", "chemical_level"]

# Risk weight calibration
RISK_WEIGHTS = {
    "current_pollution_score": 0.25,
    "violation_frequency":     0.20,
    "violation_severity":      0.20,
    "anomaly_score":           0.15,
    "pollution_trend":         0.10,
    "predicted_pollution":     0.10,
}

# Number of synthetic samples used for demonstration training
N_SAMPLES = 500


# ── Synthetic data generators ────────────────────────────────────────────────

def _synthetic_sensor_data(n: int = N_SAMPLES) -> list:
    """Generate synthetic sensor readings for training demonstration."""
    rng = np.random.default_rng(42)
    readings = []
    from datetime import datetime, timedelta

    base_time = datetime(2024, 1, 1)
    for i in range(n):
        ts = base_time + timedelta(hours=i)
        reading = {
            "timestamp":          ts.isoformat(),
            "pm25":               max(0, rng.normal(35, 15)),
            "pm10":               max(0, rng.normal(60, 25)),
            "so2":                max(0, rng.normal(30, 12)),
            "no2":                max(0, rng.normal(40, 15)),
            "co":                 max(0, rng.normal(5, 2)),
            "temperature":        rng.uniform(20, 40),
            "humidity":           rng.uniform(40, 90),
            "wind_speed":         rng.uniform(0, 20),
            "wind_direction":     rng.uniform(0, 360),
            "ph":                 rng.uniform(6.0, 9.0),
            "turbidity":          max(0, rng.normal(5, 3)),
            "chemical_level":     max(0, rng.normal(25, 10)),
            "production_activity":rng.uniform(0.5, 1.5),
        }
        # Inject occasional spikes (5 % of readings)
        if rng.random() < 0.05:
            spike_param = rng.choice(["pm25", "pm10", "so2", "no2"])
            reading[spike_param] = reading[spike_param] * rng.uniform(3, 6)
        readings.append(reading)
    return readings


# ── Training functions ───────────────────────────────────────────────────────

def train_anomaly_detector(readings: list) -> str:
    """Train Isolation Forest and save to model dir."""
    try:
        import joblib
        from sklearn.ensemble import IsolationForest
        from sklearn.preprocessing import StandardScaler
        from sklearn.pipeline import Pipeline
    except ImportError as e:
        logger.error("scikit-learn / joblib required: %s", e)
        return ""

    from ml.preprocessing.preprocessor import PollutionPreprocessor
    pp = PollutionPreprocessor()

    X = pp.build_multivariate_matrix(readings)
    if X.shape[0] < 20:
        logger.warning("Not enough samples for anomaly detector training.")
        return ""

    pipe = Pipeline([
        ("scaler", StandardScaler()),
        ("iforest", IsolationForest(
            n_estimators=100,
            contamination=0.05,
            random_state=42,
        )),
    ])
    pipe.fit(X)

    path = os.path.join(MODEL_DIR, "anomaly_detector.joblib")
    joblib.dump(pipe, path)
    logger.info("Saved anomaly detector → %s  (trained on %d samples)", path, X.shape[0])
    return path


def train_forecasting_models(readings: list) -> Dict[str, str]:
    """Train per-parameter Linear Regression forecasting models."""
    try:
        import joblib
        from sklearn.linear_model import LinearRegression
        from sklearn.preprocessing import StandardScaler
        from sklearn.pipeline import Pipeline
    except ImportError as e:
        logger.error("scikit-learn / joblib required: %s", e)
        return {}

    from ml.preprocessing.preprocessor import PollutionPreprocessor
    pp = PollutionPreprocessor()

    paths = {}
    for param in FORECAST_PARAMS:
        X, y = pp.prepare_features(readings, param)
        if X is None or len(X) < 10:
            logger.warning("Skipping %s — not enough data (%s samples).", param, len(readings))
            continue

        pipe = Pipeline([
            ("scaler", StandardScaler()),
            ("lr",     LinearRegression()),
        ])
        pipe.fit(X, y)

        score = pipe.score(X, y)
        path  = os.path.join(MODEL_DIR, f"forecast_{param}.joblib")
        joblib.dump(pipe, path)
        paths[param] = path
        logger.info("Saved forecast/%s → %s  (R²=%.3f, samples=%d)", param, path, score, len(X))

    return paths


def save_risk_weights() -> str:
    """Persist risk scoring weights so the agent can load them at runtime."""
    try:
        import joblib
    except ImportError as e:
        logger.error("joblib required: %s", e)
        return ""

    path = os.path.join(MODEL_DIR, "risk_weights.joblib")
    joblib.dump(RISK_WEIGHTS, path)
    logger.info("Saved risk weights → %s", path)
    return path


def load_model(model_name: str):
    """
    Load a trained model from the models directory.

    Parameters
    ----------
    model_name : str  e.g. "anomaly_detector", "forecast_pm25", "risk_weights"

    Returns
    -------
    Loaded joblib object, or None if not found.
    """
    try:
        import joblib
    except ImportError:
        logger.error("joblib is not installed.")
        return None

    path = os.path.join(MODEL_DIR, f"{model_name}.joblib")
    if not os.path.exists(path):
        logger.warning("Model file not found: %s", path)
        return None

    model = joblib.load(path)
    logger.info("Loaded model: %s", path)
    return model


def train_all() -> Dict[str, Any]:
    """
    Run the full training pipeline on synthetic data.
    Returns a summary dict with saved paths and metadata.
    """
    logger.info("=" * 60)
    logger.info("Starting ML training pipeline …")
    logger.info("=" * 60)

    readings = _synthetic_sensor_data(N_SAMPLES)
    logger.info("Generated %d synthetic sensor readings.", len(readings))

    results: Dict[str, Any] = {}

    # 1. Anomaly detection
    anomaly_path = train_anomaly_detector(readings)
    results["anomaly_detector"] = anomaly_path

    # 2. Forecasting models
    forecast_paths = train_forecasting_models(readings)
    results["forecasting_models"] = forecast_paths

    # 3. Risk scoring weights
    risk_path = save_risk_weights()
    results["risk_weights"] = risk_path

    logger.info("=" * 60)
    logger.info("Training complete.")
    logger.info("  Anomaly detector : %s", anomaly_path or "SKIPPED")
    logger.info("  Forecasting      : %d model(s) saved", len(forecast_paths))
    logger.info("  Risk weights     : %s", risk_path or "SKIPPED")
    logger.info("=" * 60)

    return results


# ── type hint for Dict not imported yet above ────────────────────────────────
from typing import Any, Dict   # noqa: E402 – placed here to avoid circular hint


# ── CLI entry-point ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    summary = train_all()
    print("\nSaved models:")
    for k, v in summary.items():
        print(f"  {k}: {v}")
