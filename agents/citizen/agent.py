"""
Citizen Assistant Agent
─────────────────────────
Answers pollution-related questions from citizens in plain language.
Specialized for Gujarat district/city specific queries.
"""

from __future__ import annotations
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class CitizenAssistantAgent:
    """
    Processes citizen queries about pollution status, health advice,
    and what actions to take. Returns friendly, actionable responses.
    """

    name = "CitizenAssistantAgent"

    HEALTH_THRESHOLDS = {
        "pm25": {"moderate": 35, "poor": 75, "very_poor": 115, "severe": 150},
        "pm10": {"moderate": 50, "poor": 100, "very_poor": 250, "severe": 350},
        "so2":  {"moderate": 40, "poor": 80,  "very_poor": 120, "severe": 200},
        "no2":  {"moderate": 40, "poor": 80,  "very_poor": 120, "severe": 200},
        "co":   {"moderate": 4,  "poor": 8,   "very_poor": 12,  "severe": 17},
    }

    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich context with citizen-friendly health advisory."""
        try:
            health_category = self._categorize_health_impact(context)
            advisory = self._generate_advisory(context, health_category)
            context["citizen_health_category"] = health_category
            context["citizen_advisory"] = advisory
            logger.debug("[CitizenAssistantAgent] Category=%s", health_category)
        except Exception as exc:
            logger.warning("[CitizenAssistantAgent] Failed: %s", exc)
        return context

    def _categorize_health_impact(self, context: Dict[str, Any]) -> str:
        param = context.get("parameter", "")
        value = context.get("value", 0)
        thresholds = self.HEALTH_THRESHOLDS.get(param, {})

        if not thresholds or not value:
            return "GOOD"

        if value >= thresholds.get("severe", float("inf")):
            return "SEVERE"
        if value >= thresholds.get("very_poor", float("inf")):
            return "VERY_POOR"
        if value >= thresholds.get("poor", float("inf")):
            return "POOR"
        if value >= thresholds.get("moderate", float("inf")):
            return "MODERATE"
        return "GOOD"

    def _generate_advisory(self, context: Dict[str, Any], category: str) -> str:
        location = context.get("location", "your area")
        param = context.get("parameter", "pollutant")
        value = context.get("value", 0)

        base = f"{param.upper()} level is {value:.1f} in {location}. "

        advisories = {
            "SEVERE": (
                base + "SEVERE health risk. Stay indoors. Close all windows and doors. "
                "Use air purifier if available. Avoid outdoor activities completely. "
                "Vulnerable groups (children, elderly, respiratory patients) should seek medical attention if symptomatic. "
                "Report to GPCB: 1800-233-5500."
            ),
            "VERY_POOR": (
                base + "VERY POOR conditions. Avoid all outdoor activities. "
                "Wear N99/P100 respirator if going outside is unavoidable. "
                "Keep indoor air filtered. Monitor for symptoms: coughing, eye irritation, shortness of breath."
            ),
            "POOR": (
                base + "POOR air quality. Sensitive groups should stay indoors. "
                "Healthy adults should limit prolonged outdoor activity. "
                "Wear N95 mask if going outside. Avoid exercise near roads or industrial areas."
            ),
            "MODERATE": (
                base + "MODERATE pollution. Unusually sensitive people may experience mild discomfort. "
                "Consider reducing prolonged outdoor activities. "
                "Children and elderly should limit extended outdoor time."
            ),
            "GOOD": (
                base + "Pollution within acceptable range. "
                "No special precautions needed for healthy adults. "
                "Continue normal activities."
            ),
        }
        return advisories.get(category, advisories["GOOD"])


# Module-level singleton
citizen_assistant_agent = CitizenAssistantAgent()
