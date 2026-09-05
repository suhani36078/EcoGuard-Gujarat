"""
Data Quality Agent
─────────────────────
Checks data completeness, consistency, and flags suspicious readings.
Adds confidence scores and data trust indicators to every pipeline run.
"""

from __future__ import annotations
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

EXPECTED_PARAMS = ["pm25", "pm10", "so2", "no2", "co", "temperature", "humidity"]
WATER_PARAMS = ["ph", "turbidity", "chemical_level"]

BOUNDS = {
    "pm25": (0, 500),
    "pm10": (0, 600),
    "so2": (0, 400),
    "no2": (0, 400),
    "co": (0, 50),
    "temperature": (-10, 55),
    "humidity": (0, 100),
    "ph": (0, 14),
    "turbidity": (0, 1000),
    "chemical_level": (0, 500),
}


class DataQualityAgent:
    """
    Evaluates incoming sensor data for:
    - Missing values
    - Out-of-range values
    - Sudden spikes (vs recent history)
    - Assigns a data confidence score (0-1)
    """

    name = "DataQualityAgent"

    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        try:
            issues: List[str] = []
            confidence = 1.0

            # Check for missing expected params
            missing = [p for p in EXPECTED_PARAMS if context.get(p) is None]
            if missing:
                issues.append(f"Missing: {', '.join(missing)}")
                confidence -= 0.05 * len(missing)

            # Check bounds
            for param, (lo, hi) in BOUNDS.items():
                val = context.get(param)
                if val is not None:
                    if not (lo <= val <= hi):
                        issues.append(f"{param}={val} out of physical bounds [{lo},{hi}]")
                        confidence -= 0.1

            # Check for anomalous spikes vs recent history
            history = context.get("history", [])
            if history:
                param = context.get("parameter")
                value = context.get("value")
                if param and value:
                    recent = [h.get(param) for h in history[-10:] if h.get(param) is not None]
                    if recent:
                        avg = sum(recent) / len(recent)
                        if avg > 0 and abs(value - avg) / avg > 5.0:
                            issues.append(f"{param} spike: {value:.1f} vs avg {avg:.1f} (>500% change)")
                            confidence -= 0.15

            confidence = max(0.1, min(1.0, confidence))
            context["data_quality_issues"] = issues
            context["data_confidence"] = round(confidence, 2)
            context["data_quality_status"] = "PASS" if not issues else ("WARN" if confidence > 0.5 else "FAIL")
            context["data_source_note"] = "DEMO/SIMULATED — Not official government sensor data"

            if issues:
                logger.debug("[DataQualityAgent] Issues: %s | Confidence: %.2f", issues, confidence)
            else:
                logger.debug("[DataQualityAgent] No issues | Confidence: %.2f", confidence)

        except Exception as exc:
            logger.warning("[DataQualityAgent] Failed: %s", exc)
            context.setdefault("data_confidence", 0.75)

        return context


# Module-level singleton
data_quality_agent = DataQualityAgent()
