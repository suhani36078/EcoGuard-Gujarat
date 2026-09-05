"""
Factory Risk Profiling Agent
──────────────────────────────
Calculates a composite risk score 0–100 for a factory using a weighted
combination of six sub-scores:

  current_pollution_score   25 %
  violation_frequency       20 %
  violation_severity        20 %
  anomaly_score             15 %
  pollution_trend           10 %
  predicted_pollution       10 %

Output: risk_score, risk_level (LOW / MEDIUM / HIGH / CRITICAL),
        score_breakdown, explanation.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ── Weights must sum to 1.0 ──────────────────────────────────────────────────
WEIGHTS = {
    "current_pollution_score": 0.25,
    "violation_frequency":     0.20,
    "violation_severity":      0.20,
    "anomaly_score":           0.15,
    "pollution_trend":         0.10,
    "predicted_pollution":     0.10,
}

# Risk level thresholds
RISK_LEVELS = [
    (80, "CRITICAL"),
    (60, "HIGH"),
    (40, "MEDIUM"),
    (0,  "LOW"),
]

# Severity → numeric score mapping
SEVERITY_SCORES = {
    "CRITICAL": 100,
    "HIGH":     75,
    "MEDIUM":   50,
    "LOW":      25,
    None:       0,
}

# Trend → numeric score mapping (higher = worse)
TREND_SCORES = {
    "increasing": 80,
    "stable":     40,
    "decreasing": 10,
    "unknown":    40,
}


class FactoryRiskAgent:
    """
    Calculates a comprehensive risk profile for an industrial facility.
    """

    name = "FactoryRiskAgent"

    # ── public interface ─────────────────────────────────────────────────────

    def calculate_risk(
        self,
        factory_id: str,
        current_reading: Dict[str, Any],
        violations: Optional[List[Dict[str, Any]]] = None,
        anomaly_score: float = 0.0,
        forecast: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Compute the risk profile for *factory_id*.

        Parameters
        ----------
        factory_id      : str
        current_reading : dict – latest sensor reading (contains monitoring status etc.)
        violations      : list of past violation dicts (recent history)
        anomaly_score   : float 0-100 from AnomalyDetectionAgent
        forecast        : dict from ForecastingAgent

        Returns
        -------
        {
            factory_id, risk_score, risk_level,
            score_breakdown, explanation, calculated_at
        }
        """
        violations = violations or []
        forecast   = forecast   or {}

        # ── compute sub-scores ───────────────────────────────────────────────
        sub_scores = {
            "current_pollution_score": self._current_pollution_score(current_reading),
            "violation_frequency":     self._violation_frequency_score(violations),
            "violation_severity":      self._violation_severity_score(violations),
            "anomaly_score":           self._clamp(anomaly_score),
            "pollution_trend":         self._trend_score(forecast),
            "predicted_pollution":     self._predicted_pollution_score(forecast),
        }

        # ── weighted sum ─────────────────────────────────────────────────────
        risk_score = sum(sub_scores[k] * WEIGHTS[k] for k in WEIGHTS)
        risk_score = round(min(100.0, max(0.0, risk_score)), 1)

        risk_level = self._risk_level(risk_score)
        explanation = self._build_explanation(risk_score, risk_level, sub_scores, violations)

        logger.info("[%s] factory=%s score=%.1f level=%s", self.name, factory_id, risk_score, risk_level)

        return {
            "factory_id":    factory_id,
            "risk_score":    risk_score,
            "risk_level":    risk_level,
            "score_breakdown": {k: round(v, 1) for k, v in sub_scores.items()},
            "weights":       WEIGHTS,
            "explanation":   explanation,
            "calculated_at": datetime.utcnow().isoformat(),
        }

    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Supervisor-compatible process() method."""
        factory_id    = context.get("factory_id", "UNKNOWN")
        violations    = context.get("violations", [])
        anomaly_score = context.get("anomaly_score") or 0.0
        forecast      = context.get("forecast", {})

        result = self.calculate_risk(factory_id, context, violations, anomaly_score, forecast)
        context["risk_score"]     = result["risk_score"]
        context["risk_level"]     = result["risk_level"]
        context["risk_breakdown"] = result["score_breakdown"]
        context["risk_result"]    = result
        return context

    # ── sub-score calculators ────────────────────────────────────────────────

    def _current_pollution_score(self, reading: Dict[str, Any]) -> float:
        """Convert current monitoring status + exceedance to 0-100."""
        status = reading.get("current_status", "NORMAL")
        exc    = reading.get("exceedance_percent") or 0.0

        if status == "CRITICAL":
            base = 70.0
        elif status == "WARNING":
            base = 40.0
        else:
            base = 10.0

        # Boost for high exceedance
        boost = min(30.0, float(exc) * 0.3)
        return self._clamp(base + boost)

    def _violation_frequency_score(self, violations: List[Dict[str, Any]]) -> float:
        """Score based on number of recent violations (last 30 by default)."""
        n = len(violations)
        if n == 0:
            return 0.0
        if n >= 20:
            return 100.0
        # Linear 0→100 for 0→20 violations
        return self._clamp(n * 5.0)

    def _violation_severity_score(self, violations: List[Dict[str, Any]]) -> float:
        """Average severity score of recent violations."""
        if not violations:
            return 0.0
        scores = [SEVERITY_SCORES.get(v.get("severity"), 0) for v in violations]
        return self._clamp(sum(scores) / len(scores))

    def _trend_score(self, forecast: Dict[str, Any]) -> float:
        trend = forecast.get("trend_direction", "unknown")
        return float(TREND_SCORES.get(trend, 40))

    def _predicted_pollution_score(self, forecast: Dict[str, Any]) -> float:
        """
        Convert the 4h predicted value into a 0-100 score by comparing
        it against well-known PM2.5 reference scale (applies best-effort).
        """
        p4h = forecast.get("predicted_4h")
        if p4h is None:
            return 40.0  # neutral when no forecast

        # Use PM2.5 reference (60 µg/m³ = limit, 120 = severe)
        limit = 60.0
        ratio = float(p4h) / limit
        return self._clamp(ratio * 60.0)  # 100% of limit → 60 score

    # ── helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _clamp(value: float) -> float:
        return float(max(0.0, min(100.0, value)))

    @staticmethod
    def _risk_level(score: float) -> str:
        for threshold, level in RISK_LEVELS:
            if score >= threshold:
                return level
        return "LOW"

    def _build_explanation(
        self,
        score: float,
        level: str,
        sub_scores: Dict[str, float],
        violations: List[Dict[str, Any]],
    ) -> str:
        lines = [f"Overall risk score: {score:.1f}/100 — {level}."]

        drivers = sorted(sub_scores.items(), key=lambda x: x[1], reverse=True)
        top = [k for k, v in drivers if v >= 50]
        if top:
            readable = [k.replace("_", " ").title() for k in top]
            lines.append(f"Primary risk drivers: {', '.join(readable)}.")

        if violations:
            recent_severe = [v for v in violations if v.get("severity") in ("CRITICAL", "HIGH")]
            if recent_severe:
                lines.append(
                    f"{len(recent_severe)} high/critical severity violation(s) in recent history."
                )

        if level == "CRITICAL":
            lines.append("Immediate regulatory intervention and factory shutdown review recommended.")
        elif level == "HIGH":
            lines.append("Urgent inspection and corrective action required.")
        elif level == "MEDIUM":
            lines.append("Enhanced monitoring and proactive maintenance advised.")
        else:
            lines.append("Continue routine monitoring.")

        return " ".join(lines)


# ── Module-level singleton ───────────────────────────────────────────────────
factory_risk_agent = FactoryRiskAgent()
