"""
Prediction Agent
─────────────────
Uses trend analysis to predict near-future pollution risk.
Provides district-level and factory-level pollution forecasts.
"""

from __future__ import annotations
import logging
import math
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class PredictionAgent:
    """
    Analyzes pollution trends and produces risk predictions.
    Uses linear regression on historical data when available,
    otherwise falls back to rule-based trend analysis.
    """

    name = "PredictionAgent"

    POLLUTION_LIMITS = {
        "pm25": 60, "pm10": 100, "so2": 80, "no2": 80, "co": 10,
        "turbidity": 10, "chemical_level": 50,
    }

    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        try:
            history = context.get("history", [])
            param = context.get("parameter", "pm25")
            value = context.get("value", 0.0)

            # Extract historical values for this parameter
            hist_vals = [h.get(param) for h in history[-48:] if h.get(param) is not None]

            if len(hist_vals) >= 6:
                predicted = self._linear_trend_predict(hist_vals, horizons=[1, 3, 6])
                trend_dir = self._get_trend_direction(hist_vals)
                confidence = min(0.85, 0.5 + len(hist_vals) * 0.005)
                model = "LinearRegression"
            else:
                # Simple extrapolation based on current vs limit
                limit = self.POLLUTION_LIMITS.get(param, 100)
                ratio = (value / limit) if limit else 0
                predicted = {
                    "1h": round(value * 1.02, 2),
                    "3h": round(value * 1.05, 2),
                    "6h": round(value * 1.07, 2),
                }
                trend_dir = "increasing" if ratio > 0.8 else "stable"
                confidence = 0.45
                model = "SimpleExtrapolation"

            limit = self.POLLUTION_LIMITS.get(param, 100)
            will_exceed = predicted.get("6h", value) > limit

            context["prediction"] = {
                "parameter": param,
                "current_value": value,
                "predicted_1h": predicted.get("1h"),
                "predicted_3h": predicted.get("3h"),
                "predicted_6h": predicted.get("6h"),
                "trend_direction": trend_dir,
                "will_exceed_limit_6h": will_exceed,
                "confidence": round(confidence, 2),
                "model": model,
                "limit": limit,
            }

            logger.debug("[PredictionAgent] %s trend=%s 6h=%.1f", param, trend_dir, predicted.get("6h", 0))
        except Exception as exc:
            logger.warning("[PredictionAgent] Failed: %s", exc)
        return context

    def _linear_trend_predict(self, values: List[float], horizons: List[int]) -> Dict[str, float]:
        n = len(values)
        x_mean = (n - 1) / 2
        y_mean = sum(values) / n
        numerator = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(values))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        slope = numerator / denominator if denominator != 0 else 0

        results = {}
        for h in horizons:
            predicted = max(0, values[-1] + slope * h)
            results[f"{h}h"] = round(predicted, 2)
        return results

    def _get_trend_direction(self, values: List[float]) -> str:
        if len(values) < 4:
            return "stable"
        recent_avg = sum(values[-4:]) / 4
        earlier_avg = sum(values[-8:-4]) / 4 if len(values) >= 8 else sum(values[:4]) / 4
        if earlier_avg == 0:
            return "stable"
        change_pct = (recent_avg - earlier_avg) / earlier_avg * 100
        if change_pct > 8:
            return "increasing"
        if change_pct < -8:
            return "decreasing"
        return "stable"


# Module-level singleton
prediction_agent = PredictionAgent()
