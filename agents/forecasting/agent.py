"""
Forecasting Agent
──────────────────
Predicts future pollution levels using Linear Regression with time-based
and lag features.  Forecasts 1h, 2h and 4h horizons.
"""

from __future__ import annotations

import logging
import math
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Parameters for which models are trained / loaded
FORECASTABLE = ["pm25", "pm10", "so2", "no2", "co", "turbidity", "chemical_level"]

# Minimum readings required to attempt a forecast
MIN_READINGS = 10

# Directory where trained models are persisted
MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "ml", "models")


class ForecastingAgent:
    """
    Trains (on-the-fly) or loads a Linear Regression model per parameter and
    returns point-forecasts for the next 1h, 2h and 4h.
    """

    name = "ForecastingAgent"

    def __init__(self):
        # Lazy cache: {parameter: fitted sklearn Pipeline}
        self._models: Dict[str, Any] = {}

    # ── public interface ─────────────────────────────────────────────────────

    def forecast(
        self,
        factory_id: str,
        parameter: str,
        readings: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Predict future pollution levels for *parameter*.

        Parameters
        ----------
        factory_id : str
        parameter  : str  – e.g. "pm25"
        readings   : list of dicts with keys ``timestamp`` and the parameter value

        Returns
        -------
        {
            predicted_1h, predicted_2h, predicted_4h,
            trend_direction, confidence, model_used, parameter, factory_id
        }
        """
        if len(readings) < MIN_READINGS:
            return self._insufficient(factory_id, parameter, len(readings))

        try:
            return self._run_forecast(factory_id, parameter, readings)
        except Exception as exc:
            logger.warning("[%s] Forecast failed for %s/%s: %s", self.name, factory_id, parameter, exc)
            return self._fallback(factory_id, parameter, readings)

    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Supervisor-compatible process() method.
        Expects context to contain ``readings`` (or ``history``) and ``parameter``.
        """
        factory_id = context.get("factory_id", "UNKNOWN")
        parameter  = context.get("parameter", "pm25")
        readings   = context.get("readings") or context.get("history", [])

        result = self.forecast(factory_id, parameter, readings)
        context["forecast"] = result
        context["predicted_1h"]  = result.get("predicted_1h")
        context["predicted_2h"]  = result.get("predicted_2h")
        context["predicted_4h"]  = result.get("predicted_4h")
        context["trend_direction"] = result.get("trend_direction", "stable")
        return context

    # ── core forecast logic ──────────────────────────────────────────────────

    def _run_forecast(
        self,
        factory_id: str,
        parameter: str,
        readings: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        import numpy as np
        from sklearn.linear_model import LinearRegression
        from sklearn.preprocessing import StandardScaler
        from sklearn.pipeline import Pipeline

        values = self._extract_values(readings, parameter)
        if len(values) < MIN_READINGS:
            return self._insufficient(factory_id, parameter, len(values))

        X, y = self._build_features(values)

        model_key = f"{factory_id}_{parameter}"
        if model_key not in self._models:
            pipe = Pipeline([
                ("scaler", StandardScaler()),
                ("lr", LinearRegression()),
            ])
            pipe.fit(X, y)
            self._models[model_key] = pipe
        else:
            pipe = self._models[model_key]
            # Re-fit with latest data to stay current
            pipe.fit(X, y)

        last_values = values[-6:]
        current     = values[-1]

        # Predict 1h, 2h, 4h ahead
        predictions = {}
        for horizon in (1, 2, 4):
            feat = self._future_features(last_values, horizon)
            pred = float(pipe.predict([feat])[0])
            predictions[horizon] = round(max(0.0, pred), 2)

        # Trend: compare mean of last 3 vs mean of prior 3
        if len(values) >= 6:
            recent = sum(values[-3:]) / 3
            older  = sum(values[-6:-3]) / 3
            if recent > older * 1.05:
                trend = "increasing"
            elif recent < older * 0.95:
                trend = "decreasing"
            else:
                trend = "stable"
        else:
            trend = "stable"

        # Confidence: based on how well the model fits (R²)
        try:
            r2 = float(pipe.score(X, y))
            confidence = round(max(0.0, min(1.0, r2)) * 100, 1)
        except Exception:
            confidence = 50.0

        return {
            "factory_id":    factory_id,
            "parameter":     parameter,
            "predicted_1h":  predictions[1],
            "predicted_2h":  predictions[2],
            "predicted_4h":  predictions[4],
            "trend_direction": trend,
            "confidence":    confidence,
            "model_used":    "LinearRegression",
            "current_value": round(current, 2),
            "readings_used": len(values),
        }

    # ── feature engineering ──────────────────────────────────────────────────

    def _extract_values(
        self,
        readings: List[Dict[str, Any]],
        parameter: str,
    ) -> List[float]:
        vals = []
        for r in readings:
            v = r.get(parameter)
            if v is not None:
                try:
                    vals.append(float(v))
                except (TypeError, ValueError):
                    pass
        return vals

    def _build_features(self, values: List[float]):
        """
        Build (X, y) for training.  Features: lag_1, lag_3, lag_6,
        rolling_mean_3, rolling_std_3, index (time proxy).
        """
        import numpy as np

        X_rows, y_vals = [], []
        for i in range(6, len(values)):
            row = self._make_row(values, i)
            X_rows.append(row)
            y_vals.append(values[i])

        return np.array(X_rows, dtype=float), np.array(y_vals, dtype=float)

    def _make_row(self, values: List[float], idx: int) -> List[float]:
        lag1 = values[idx - 1]
        lag3 = values[idx - 3]
        lag6 = values[idx - 6]
        win3 = values[idx - 3:idx]
        roll_mean = sum(win3) / len(win3)
        roll_std  = _std(win3)
        return [lag1, lag3, lag6, roll_mean, roll_std, float(idx)]

    def _future_features(self, last_vals: List[float], horizon: int) -> List[float]:
        extended = list(last_vals)
        for _ in range(horizon):
            roll3 = extended[-3:]
            nxt = sum(roll3) / len(roll3)
            extended.append(nxt)
        n = len(last_vals) + horizon
        return self._make_row(extended, len(extended) - 1)

    # ── fallbacks ────────────────────────────────────────────────────────────

    def _insufficient(self, factory_id: str, parameter: str, count: int) -> Dict[str, Any]:
        return {
            "factory_id":    factory_id,
            "parameter":     parameter,
            "predicted_1h":  None,
            "predicted_2h":  None,
            "predicted_4h":  None,
            "trend_direction": "unknown",
            "confidence":    0.0,
            "model_used":    "none",
            "error":         f"Insufficient data: {count} readings (need {MIN_READINGS}).",
        }

    def _fallback(self, factory_id: str, parameter: str, readings: List[Dict]) -> Dict[str, Any]:
        """Simple moving-average fallback when sklearn fails."""
        values = self._extract_values(readings, parameter)
        if not values:
            return self._insufficient(factory_id, parameter, 0)
        avg = sum(values[-5:]) / min(5, len(values))
        return {
            "factory_id":    factory_id,
            "parameter":     parameter,
            "predicted_1h":  round(avg, 2),
            "predicted_2h":  round(avg, 2),
            "predicted_4h":  round(avg, 2),
            "trend_direction": "stable",
            "confidence":    30.0,
            "model_used":    "moving_average_fallback",
        }


# ── helpers ──────────────────────────────────────────────────────────────────

def _std(values: List[float]) -> float:
    if len(values) < 2:
        return 0.0
    mu = sum(values) / len(values)
    variance = sum((v - mu) ** 2 for v in values) / len(values)
    return math.sqrt(variance)


# ── Module-level singleton ───────────────────────────────────────────────────
forecasting_agent = ForecastingAgent()
