"""
Anomaly Detection Agent
────────────────────────
Detects sudden spikes and unusual trends using:
  1. Rolling z-score (statistical method)
  2. Isolation Forest (ML method)

Outputs an anomaly_score 0–100 with an explainable reason.
"""

from __future__ import annotations

import logging
import math
import statistics
from collections import deque
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Window size for rolling statistics
ROLLING_WINDOW = 30

# Z-score threshold to flag as anomaly
Z_THRESHOLD = 2.5

# Parameters checked for anomalies
MONITORED_PARAMS = ["pm25", "pm10", "so2", "no2", "co", "turbidity", "chemical_level", "ph"]


class RollingStats:
    """Maintains a rolling window of values for online z-score calculation."""

    def __init__(self, window: int = ROLLING_WINDOW):
        self.window = window
        self._buf: deque = deque(maxlen=window)

    def push(self, value: float) -> None:
        self._buf.append(value)

    def z_score(self, value: float) -> Optional[float]:
        if len(self._buf) < 5:
            return None
        mu = statistics.mean(self._buf)
        try:
            sigma = statistics.stdev(self._buf)
        except statistics.StatisticsError:
            return None
        if sigma < 1e-6:
            return 0.0
        return abs((value - mu) / sigma)

    @property
    def mean(self) -> Optional[float]:
        return statistics.mean(self._buf) if self._buf else None

    @property
    def stdev(self) -> Optional[float]:
        try:
            return statistics.stdev(self._buf) if len(self._buf) >= 2 else None
        except statistics.StatisticsError:
            return None


class AnomalyDetectionAgent:
    """
    Detects anomalies in sensor readings using z-score and Isolation Forest.
    Maintains per-factory, per-parameter rolling windows for online detection.
    """

    name = "AnomalyDetectionAgent"

    def __init__(self):
        # _rolling[factory_id][parameter] = RollingStats
        self._rolling: Dict[str, Dict[str, RollingStats]] = {}
        # Isolation Forest models are lazily trained per factory
        self._iso_models: Dict[str, Any] = {}

    # ── public interface ─────────────────────────────────────────────────────

    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fill context["anomaly_score"] and context["anomaly_reason"].
        """
        factory_id = context.get("factory_id", "UNKNOWN")
        parameter  = context.get("parameter")
        value      = context.get("value")

        if value is None or parameter is None:
            context["anomaly_score"] = None
            context["anomaly_reason"] = "Insufficient data."
            return context

        score, reason = self._score_single(factory_id, parameter, float(value))
        context["anomaly_score"] = score
        context["anomaly_reason"] = reason

        logger.info(
            "[%s] factory=%s param=%s value=%s score=%.1f",
            self.name, factory_id, parameter, value, score or 0,
        )
        return context

    def analyze_batch(
        self,
        factory_id: str,
        readings: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Analyze a list of reading dicts.
        Returns a list of anomaly records (only those that exceed Z_THRESHOLD).
        """
        # ── z-score pass ──
        z_anomalies = self._zscore_batch(factory_id, readings)

        # ── Isolation Forest pass ──
        iso_anomalies = self._isolation_forest_batch(factory_id, readings)

        # Merge: take the higher score for each (timestamp, parameter) pair
        merged: Dict[tuple, Dict[str, Any]] = {}
        for a in z_anomalies + iso_anomalies:
            key = (str(a.get("detected_at")), a.get("parameter"))
            existing = merged.get(key)
            if existing is None or a["anomaly_score"] > existing["anomaly_score"]:
                merged[key] = a

        return sorted(merged.values(), key=lambda x: x["anomaly_score"], reverse=True)

    # ── z-score batch ────────────────────────────────────────────────────────

    def _zscore_batch(
        self,
        factory_id: str,
        readings: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        # Build per-param value lists
        param_values: Dict[str, List[float]] = {p: [] for p in MONITORED_PARAMS}
        for r in readings:
            for p in MONITORED_PARAMS:
                v = r.get(p)
                if v is not None:
                    param_values[p].append(float(v))

        anomalies = []
        for p in MONITORED_PARAMS:
            vals = param_values[p]
            if len(vals) < 10:
                continue
            mu    = statistics.mean(vals)
            sigma = statistics.stdev(vals) if len(vals) >= 2 else 1
            if sigma < 1e-6:
                continue
            for r in readings:
                v = r.get(p)
                if v is None:
                    continue
                z = abs((float(v) - mu) / sigma)
                if z >= Z_THRESHOLD:
                    score = min(100.0, round(z * 20, 1))
                    anomalies.append({
                        "factory_id": factory_id,
                        "parameter": p,
                        "anomaly_score": score,
                        "detected_at": r.get("timestamp"),
                        "description": (
                            f"[Z-score] {p.upper()} value {v:.2f} deviates {z:.2f}σ "
                            f"from rolling mean {mu:.2f} (σ={sigma:.2f}). "
                            f"Possible sudden discharge or equipment fault."
                        ),
                        "method": "zscore",
                        "status": "open" if score >= 60 else "reviewed",
                    })
        return anomalies

    # ── Isolation Forest batch ───────────────────────────────────────────────

    def _isolation_forest_batch(
        self,
        factory_id: str,
        readings: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        try:
            import numpy as np
            from sklearn.ensemble import IsolationForest
        except ImportError:
            logger.warning("scikit-learn not installed; skipping Isolation Forest.")
            return []

        # Build feature matrix
        feature_params = ["pm25", "pm10", "so2", "no2", "co"]
        rows = []
        indices = []
        for i, r in enumerate(readings):
            row = [r.get(p, 0) or 0 for p in feature_params]
            if any(v > 0 for v in row):
                rows.append(row)
                indices.append(i)

        if len(rows) < 20:
            return []

        X = np.array(rows, dtype=float)
        model = IsolationForest(contamination=0.05, random_state=42, n_estimators=100)
        preds = model.fit_predict(X)
        scores_raw = model.score_samples(X)

        # Normalize: more negative → higher anomaly score
        min_s, max_s = scores_raw.min(), scores_raw.max()
        range_s = max_s - min_s if max_s != min_s else 1.0

        anomalies = []
        for pos, (pred, raw_score) in enumerate(zip(preds, scores_raw)):
            if pred == -1:  # anomaly
                norm_score = min(100.0, round((1 - (raw_score - min_s) / range_s) * 100, 1))
                r = readings[indices[pos]]
                dominant_param = feature_params[
                    int(np.argmax([abs(X[pos, j] - X[:, j].mean()) for j in range(len(feature_params))]))
                ]
                anomalies.append({
                    "factory_id": factory_id,
                    "parameter": dominant_param,
                    "anomaly_score": norm_score,
                    "detected_at": r.get("timestamp"),
                    "description": (
                        f"[IsolationForest] Reading flagged as anomalous. "
                        f"Primary driver: {dominant_param.upper()} = {r.get(dominant_param):.2f}. "
                        f"Isolation score: {raw_score:.4f}."
                    ),
                    "method": "isolation_forest",
                    "status": "open" if norm_score >= 60 else "reviewed",
                })
        return anomalies

    # ── single-value scoring ─────────────────────────────────────────────────

    def _score_single(
        self,
        factory_id: str,
        parameter: str,
        value: float,
    ) -> tuple[float, str]:
        """Update rolling window and return (score, reason)."""
        if factory_id not in self._rolling:
            self._rolling[factory_id] = {}
        if parameter not in self._rolling[factory_id]:
            self._rolling[factory_id][parameter] = RollingStats(ROLLING_WINDOW)

        roller = self._rolling[factory_id][parameter]
        z = roller.z_score(value)
        roller.push(value)  # push after scoring

        if z is None:
            return 0.0, "Insufficient history for anomaly scoring."

        if z < Z_THRESHOLD:
            return round(z * 10, 1), f"{parameter.upper()}={value} normal (z={z:.2f})."

        score = min(100.0, round(z * 20, 1))
        reason = (
            f"{parameter.upper()} value {value} is {z:.2f}σ from mean "
            f"{roller.mean:.2f}±{roller.stdev:.2f}. "
            f"{'SPIKE detected.' if value > (roller.mean or 0) else 'SUDDEN DROP detected.'}"
        )
        return score, reason


# ── Module-level singleton ───────────────────────────────────────────────────
anomaly_agent = AnomalyDetectionAgent()
