"""
ML Preprocessing Module
─────────────────────────
Converts raw sensor reading dicts into engineered feature matrices
suitable for anomaly detection, forecasting, and risk scoring models.

Features produced per reading:
  Time:    hour_of_day, day_of_week, is_weekend, hour_sin, hour_cos
  Lag:     lag_1, lag_3, lag_6  (per target parameter)
  Rolling: rolling_mean_3, rolling_std_3, rolling_mean_6
"""

from __future__ import annotations

import math
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

# All numeric sensor parameters available in a reading
ALL_PARAMS = [
    "pm25", "pm10", "so2", "no2", "co",
    "temperature", "humidity", "wind_speed",
    "ph", "turbidity", "chemical_level",
    "production_activity",
]

# Minimum history required for full feature set
MIN_READINGS = 7


class PollutionPreprocessor:
    """
    Transforms lists of sensor reading dicts into numpy feature matrices.

    Usage
    -----
    pp = PollutionPreprocessor()
    X_train, y_train = pp.prepare_features(readings, target_param="pm25")
    X_all = pp.build_multivariate_matrix(readings)
    """

    # ── public interface ─────────────────────────────────────────────────────

    def prepare_features(
        self,
        readings: List[Dict[str, Any]],
        target_param: str,
    ) -> Tuple[Any, Any]:
        """
        Build (X_train, y_train) for supervised forecasting of *target_param*.

        Features per sample:
          hour_of_day, day_of_week, is_weekend, hour_sin, hour_cos,
          lag_1, lag_3, lag_6,
          rolling_mean_3, rolling_std_3, rolling_mean_6,
          production_activity

        Parameters
        ----------
        readings     : list of reading dicts, sorted oldest → newest
        target_param : str  e.g. "pm25"

        Returns
        -------
        (X, y) as numpy arrays, or (None, None) if not enough data
        """
        import numpy as np

        values = self._extract(readings, target_param)
        if len(values) < MIN_READINGS:
            return None, None

        X_rows, y_vals = [], []
        for i in range(6, len(values)):
            row = self._make_row(readings, values, i, target_param)
            X_rows.append(row)
            y_vals.append(values[i])

        if not X_rows:
            return None, None

        return np.array(X_rows, dtype=float), np.array(y_vals, dtype=float)

    def build_multivariate_matrix(
        self,
        readings: List[Dict[str, Any]],
    ):
        """
        Build a multivariate feature matrix from all sensor parameters.
        Used for anomaly detection (Isolation Forest).

        Returns np.ndarray of shape (n_readings, n_features).
        """
        import numpy as np

        feature_params = ["pm25", "pm10", "so2", "no2", "co",
                          "turbidity", "chemical_level"]

        rows = []
        for r in readings:
            row = [float(r.get(p) or 0) for p in feature_params]
            rows.append(row)

        return np.array(rows, dtype=float)

    def get_feature_names(self, target_param: str = "pm25") -> List[str]:
        """Return the ordered feature name list matching prepare_features output."""
        return [
            "hour_of_day", "day_of_week", "is_weekend",
            "hour_sin", "hour_cos",
            "lag_1", "lag_3", "lag_6",
            "rolling_mean_3", "rolling_std_3", "rolling_mean_6",
            "production_activity",
        ]

    def scale_reading(self, reading: Dict[str, Any]) -> Dict[str, Any]:
        """
        Return a normalised version of a single reading dict.
        Values are min-max scaled using typical sensor ranges.
        """
        RANGES = {
            "pm25":           (0, 300),
            "pm10":           (0, 500),
            "so2":            (0, 200),
            "no2":            (0, 200),
            "co":             (0, 50),
            "temperature":    (-20, 60),
            "humidity":       (0, 100),
            "wind_speed":     (0, 50),
            "ph":             (0, 14),
            "turbidity":      (0, 500),
            "chemical_level": (0, 200),
        }
        out = {}
        for param, (lo, hi) in RANGES.items():
            val = reading.get(param)
            if val is not None:
                rng = hi - lo
                out[param] = round((float(val) - lo) / rng, 4) if rng > 0 else 0.0
        return out

    # ── feature construction ─────────────────────────────────────────────────

    def _make_row(
        self,
        readings: List[Dict[str, Any]],
        values: List[float],
        idx: int,
        target_param: str,
    ) -> List[float]:
        # Time features from reading timestamp
        ts = readings[idx].get("timestamp")
        hour, dow, is_wknd, h_sin, h_cos = self._time_features(ts)

        lag1 = values[idx - 1]
        lag3 = values[idx - 3]
        lag6 = values[idx - 6]

        win3 = values[idx - 3:idx]
        win6 = values[idx - 6:idx]

        roll_mean_3 = sum(win3) / len(win3)
        roll_std_3  = _std(win3)
        roll_mean_6 = sum(win6) / len(win6)

        prod = float(readings[idx].get("production_activity") or 1.0)

        return [
            hour, dow, is_wknd, h_sin, h_cos,
            lag1, lag3, lag6,
            roll_mean_3, roll_std_3, roll_mean_6,
            prod,
        ]

    @staticmethod
    def _extract(readings: List[Dict[str, Any]], param: str) -> List[float]:
        vals = []
        for r in readings:
            v = r.get(param)
            if v is not None:
                try:
                    vals.append(float(v))
                except (TypeError, ValueError):
                    pass
        return vals

    @staticmethod
    def _time_features(ts: Any) -> Tuple[float, float, float, float, float]:
        """Return (hour, day_of_week, is_weekend, hour_sin, hour_cos)."""
        try:
            if isinstance(ts, str):
                dt = datetime.fromisoformat(ts)
            elif isinstance(ts, datetime):
                dt = ts
            else:
                dt = datetime.utcnow()
        except (ValueError, TypeError):
            dt = datetime.utcnow()

        hour    = float(dt.hour)
        dow     = float(dt.weekday())        # 0=Mon … 6=Sun
        is_wknd = 1.0 if dt.weekday() >= 5 else 0.0
        h_sin   = math.sin(2 * math.pi * hour / 24)
        h_cos   = math.cos(2 * math.pi * hour / 24)
        return hour, dow, is_wknd, h_sin, h_cos


# ── helpers ──────────────────────────────────────────────────────────────────

def _std(values: List[float]) -> float:
    if len(values) < 2:
        return 0.0
    mu = sum(values) / len(values)
    return math.sqrt(sum((v - mu) ** 2 for v in values) / len(values))


# ── Module-level singleton ───────────────────────────────────────────────────
preprocessor = PollutionPreprocessor()
