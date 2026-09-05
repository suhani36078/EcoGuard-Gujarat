"""
Public Health / Community Risk Agent
──────────────────────────────────────
Assesses environmental exposure risk to nearby communities.

Risk levels: MINIMAL / LOW / MEDIUM / HIGH / CRITICAL

IMPORTANT: This agent assesses *environmental risk indicators only*.
It does NOT provide medical diagnoses, clinical advice, or individual
health assessments of any kind.
"""

from __future__ import annotations

import logging
import math
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ── Health threshold reference values (WHO / CPCB guidelines) ────────────────
# All concentrations in their respective units.

HEALTH_THRESHOLDS: Dict[str, Dict[str, float]] = {
    "pm25": {
        "safe":     12.0,   # µg/m³ — WHO annual guideline
        "moderate": 35.4,   # µg/m³ — 24h standard
        "unhealthy": 55.4,
        "hazardous": 150.4,
    },
    "pm10": {
        "safe":      54.0,
        "moderate":  154.0,
        "unhealthy": 254.0,
        "hazardous": 354.0,
    },
    "so2": {
        "safe":      20.0,   # µg/m³ — WHO 24h
        "moderate":  40.0,
        "unhealthy": 80.0,
        "hazardous": 200.0,
    },
    "no2": {
        "safe":      25.0,   # µg/m³ — WHO annual
        "moderate":  40.0,
        "unhealthy": 80.0,
        "hazardous": 200.0,
    },
    "co": {
        "safe":      4.0,    # mg/m³ — WHO 8h
        "moderate":  7.0,
        "unhealthy": 10.0,
        "hazardous": 30.0,
    },
}

# Parameters that primarily affect air quality (inhalation pathway)
AIR_PARAMS   = {"pm25", "pm10", "so2", "no2", "co"}
# Parameters that primarily affect water (ingestion/contact pathway)
WATER_PARAMS = {"ph", "turbidity", "chemical_level"}

# Risk level thresholds (score 0-100)
RISK_LEVELS = [
    (85, "CRITICAL"),
    (65, "HIGH"),
    (45, "MEDIUM"),
    (25, "LOW"),
    (0,  "MINIMAL"),
]

# Wind direction: degrees where wind blows *toward* a notional residential area
# (default: NW quadrant 270–360; overridable via context)
RESIDENTIAL_WIND_RANGE = (270, 360)


class CommunityHealthAgent:
    """
    Assesses community-level environmental exposure risk.
    Produces a risk level and explanatory text based on pollutant
    concentrations, duration, wind direction, and proximity factors.

    No medical diagnosis or individual health claims are made.
    """

    name = "CommunityHealthAgent"

    # ── public interface ─────────────────────────────────────────────────────

    def assess(
        self,
        factory_id: str,
        reading: Dict[str, Any],
        duration_hours: float = 1.0,
        distance_km: float = 1.0,
        residential_wind_range: Optional[tuple] = None,
    ) -> Dict[str, Any]:
        """
        Assess community environmental exposure risk.

        Parameters
        ----------
        factory_id             : str
        reading                : latest sensor reading dict
        duration_hours         : how long the current conditions have persisted
        distance_km            : km to nearest residential zone
        residential_wind_range : (min_deg, max_deg) wind toward residential area

        Returns
        -------
        {
            factory_id, risk_level, risk_score,
            pollutant_scores, wind_factor, duration_factor, proximity_factor,
            affected_pathways, explanation
        }
        """
        wind_range = residential_wind_range or RESIDENTIAL_WIND_RANGE

        pollutant_scores   = self._score_pollutants(reading)
        wind_factor        = self._wind_factor(reading.get("wind_direction"), wind_range)
        duration_factor    = self._duration_factor(duration_hours)
        proximity_factor   = self._proximity_factor(distance_km)
        affected_pathways  = self._identify_pathways(reading)

        # Base score: weighted worst pollutant
        if not pollutant_scores:
            base_score = 0.0
        else:
            scores = list(pollutant_scores.values())
            # Weighted: max + 0.3 * second-max
            sorted_scores = sorted(scores, reverse=True)
            base_score = sorted_scores[0]
            if len(sorted_scores) > 1:
                base_score = base_score * 0.7 + sorted_scores[1] * 0.3

        # Apply modifying factors
        risk_score = base_score * wind_factor * duration_factor * proximity_factor
        risk_score = round(min(100.0, max(0.0, risk_score)), 1)

        risk_level  = self._risk_level(risk_score)
        explanation = self._build_explanation(
            risk_level, risk_score, pollutant_scores,
            wind_factor, duration_hours, distance_km, affected_pathways,
        )

        logger.info("[%s] factory=%s risk_level=%s score=%.1f", self.name, factory_id, risk_level, risk_score)

        return {
            "factory_id":       factory_id,
            "risk_level":       risk_level,
            "risk_score":       risk_score,
            "pollutant_scores": {k: round(v, 1) for k, v in pollutant_scores.items()},
            "wind_factor":      round(wind_factor, 2),
            "duration_factor":  round(duration_factor, 2),
            "proximity_factor": round(proximity_factor, 2),
            "affected_pathways": affected_pathways,
            "explanation":      explanation,
            "disclaimer":       (
                "This assessment is an environmental risk indicator only. "
                "It is not a medical diagnosis and does not constitute clinical advice."
            ),
            "assessed_at": datetime.utcnow().isoformat(),
        }

    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Supervisor-compatible process() method."""
        factory_id = context.get("factory_id", "UNKNOWN")
        duration   = context.get("violation_duration_hours") or 1.0
        distance   = context.get("distance_to_residential_km") or 1.0

        result = self.assess(factory_id, context, float(duration), float(distance))
        context["community_risk"]         = result["risk_level"]
        context["community_risk_score"]   = result["risk_score"]
        context["community_health_result"] = result
        return context

    # ── scoring ──────────────────────────────────────────────────────────────

    def _score_pollutants(self, reading: Dict[str, Any]) -> Dict[str, float]:
        scores = {}
        for param, thresholds in HEALTH_THRESHOLDS.items():
            val = reading.get(param)
            if val is None:
                continue
            v = float(val)
            score = self._pollutant_score(v, thresholds)
            scores[param] = score
        return scores

    @staticmethod
    def _pollutant_score(value: float, thresholds: Dict[str, float]) -> float:
        """Map a concentration to a 0-100 risk score using threshold breakpoints."""
        safe      = thresholds["safe"]
        moderate  = thresholds["moderate"]
        unhealthy = thresholds["unhealthy"]
        hazardous = thresholds["hazardous"]

        if value <= safe:
            return round(value / safe * 20, 1)              # 0–20
        if value <= moderate:
            t = (value - safe) / (moderate - safe)
            return round(20 + t * 25, 1)                    # 20–45
        if value <= unhealthy:
            t = (value - moderate) / (unhealthy - moderate)
            return round(45 + t * 20, 1)                    # 45–65
        if value <= hazardous:
            t = (value - unhealthy) / (hazardous - unhealthy)
            return round(65 + t * 20, 1)                    # 65–85
        # Beyond hazardous
        excess_ratio = (value - hazardous) / max(hazardous, 1)
        return min(100.0, round(85 + excess_ratio * 15, 1))

    def _wind_factor(
        self,
        wind_direction: Optional[float],
        residential_range: tuple,
    ) -> float:
        """
        Return a multiplier 0.5–1.2.
        If wind blows toward residential area → 1.2; away → 0.5.
        """
        if wind_direction is None:
            return 1.0  # unknown: assume neutral

        lo, hi = residential_range
        wd = float(wind_direction) % 360

        # Normalize range crossing 360°
        if lo > hi:
            in_range = wd >= lo or wd <= hi
        else:
            in_range = lo <= wd <= hi

        return 1.2 if in_range else 0.7

    def _duration_factor(self, hours: float) -> float:
        """Longer exposure duration → higher factor (max 1.5 at 8h+)."""
        h = max(0.0, float(hours))
        if h <= 0.5:
            return 0.7
        if h <= 1.0:
            return 1.0
        if h <= 4.0:
            return 1.0 + (h - 1.0) / 3.0 * 0.3   # 1.0–1.3
        return min(1.5, 1.3 + (h - 4.0) / 4.0 * 0.2)

    def _proximity_factor(self, distance_km: float) -> float:
        """Closer residential zones → higher factor."""
        d = max(0.1, float(distance_km))
        if d <= 0.5:
            return 1.5
        if d <= 1.0:
            return 1.2
        if d <= 3.0:
            return 1.0
        if d <= 10.0:
            return 0.7
        return 0.4

    def _identify_pathways(self, reading: Dict[str, Any]) -> List[str]:
        pathways = []
        if any(reading.get(p) is not None for p in AIR_PARAMS):
            pathways.append("inhalation (air quality)")
        if any(reading.get(p) is not None for p in WATER_PARAMS):
            pathways.append("water contact / ingestion")
        return pathways

    # ── helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _risk_level(score: float) -> str:
        for threshold, level in RISK_LEVELS:
            if score >= threshold:
                return level
        return "MINIMAL"

    def _build_explanation(
        self,
        level: str,
        score: float,
        pollutant_scores: Dict[str, float],
        wind_factor: float,
        duration_hours: float,
        distance_km: float,
        pathways: List[str],
    ) -> str:
        lines = [
            f"Community environmental exposure risk is {level} (score {score:.1f}/100).",
        ]

        if pollutant_scores:
            top_param = max(pollutant_scores, key=pollutant_scores.get)
            top_score = pollutant_scores[top_param]
            lines.append(
                f"Highest individual pollutant risk: {top_param.upper()} "
                f"(score {top_score:.1f}/100)."
            )

        if wind_factor >= 1.1:
            lines.append("Wind direction is toward nearby residential areas, elevating exposure risk.")
        elif wind_factor <= 0.8:
            lines.append("Wind direction is away from residential areas, reducing exposure risk.")

        if duration_hours >= 4.0:
            lines.append(f"Prolonged exposure duration ({duration_hours:.1f} h) increases cumulative risk.")

        if distance_km <= 0.5:
            lines.append("Residential area is very close (<0.5 km) to the emission source.")

        if pathways:
            lines.append(f"Exposure pathways: {'; '.join(pathways)}.")

        level_advice = {
            "CRITICAL": "Immediate community notification and source mitigation are advised.",
            "HIGH":     "Enhanced monitoring and precautionary advisories for sensitive groups are recommended.",
            "MEDIUM":   "Continued monitoring is recommended. Review source emissions.",
            "LOW":      "Low environmental risk. Routine monitoring is sufficient.",
            "MINIMAL":  "Levels are within acceptable environmental thresholds.",
        }
        lines.append(level_advice.get(level, ""))

        lines.append(
            "NOTE: This is an environmental risk indicator only — not a medical assessment."
        )

        return " ".join(lines)


# ── Module-level singleton ───────────────────────────────────────────────────
community_health_agent = CommunityHealthAgent()
