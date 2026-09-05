"""
Recommendation Agent
─────────────────────
Generates practical intervention recommendations based on pollution data.
"""

from __future__ import annotations
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class RecommendationAgent:
    """
    Produces actionable recommendations for:
    - Immediate response actions
    - Medium-term interventions
    - Policy-level suggestions
    """

    name = "RecommendationAgent"

    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        try:
            alert_level = context.get("alert_level", "LOW")
            param = context.get("parameter", "")
            violation = context.get("violation_status", "COMPLIANT")
            risk_score = context.get("risk_score", 0.0)
            location = context.get("location", "facility")

            immediate = self._immediate_actions(alert_level, param, violation)
            medium_term = self._medium_term(param, risk_score)
            policy = self._policy_recommendations(context)

            context["recommendations"] = {
                "immediate": immediate,
                "medium_term": medium_term,
                "policy": policy,
                "priority": alert_level,
            }
            logger.debug("[RecommendationAgent] Generated %d recommendations", 
                        len(immediate) + len(medium_term) + len(policy))
        except Exception as exc:
            logger.warning("[RecommendationAgent] Failed: %s", exc)
        return context

    def _immediate_actions(self, alert_level: str, param: str, violation: str) -> List[str]:
        actions = []
        if alert_level in ("CRITICAL", "HIGH"):
            actions.append("Issue immediate public health advisory for affected areas")
            actions.append("Notify GPCB (Gujarat Pollution Control Board) environmental team")
            if violation == "VIOLATION":
                actions.append("Issue Show Cause Notice to violating industrial unit")
                actions.append("Consider temporary production suspension if CRITICAL")
        if alert_level in ("CRITICAL", "HIGH", "MEDIUM"):
            actions.append("Deploy mobile monitoring unit to verify readings")
            actions.append("Alert local health authorities and municipality")
        if param in ("pm25", "pm10"):
            actions.append("Recommend N95/N99 masks for residents in affected radius")
        if param in ("ph", "turbidity", "chemical_level"):
            actions.append("Suspend water intake from affected sources pending testing")
            actions.append("Distribute clean water to affected communities")
        return actions

    def _medium_term(self, param: str, risk_score: float) -> List[str]:
        actions = []
        if risk_score > 60:
            actions.append("Commission independent environmental audit within 30 days")
            actions.append("Upgrade effluent treatment / pollution control equipment")
        if param in ("pm25", "pm10", "so2", "no2"):
            actions.append("Install continuous ambient air quality monitoring station")
            actions.append("Enforce vehicle emission checks in high-traffic zones")
            actions.append("Increase tree plantation and green buffer zones")
        if param in ("ph", "turbidity", "chemical_level"):
            actions.append("Repair/upgrade common effluent treatment plant (CETP)")
            actions.append("Conduct source tracing to identify discharge point")
        actions.append("Schedule monthly GPCB compliance inspection")
        return actions

    def _policy_recommendations(self, context: Dict[str, Any]) -> List[str]:
        suggestions = []
        factory_id = context.get("factory_id", "")
        violations = context.get("violations", [])
        if len(violations) > 3:
            suggestions.append("Classify as Habitual Violator — apply enhanced penalty structure")
            suggestions.append("Require third-party real-time CEMS (Continuous Emission Monitoring)")
        suggestions.append("Integrate real-time sensor data with PRITHVI-X for automated alerts")
        suggestions.append("Establish community grievance redressal mechanism")
        suggestions.append("Review industrial zoning to create residential buffer zones")
        return suggestions


# Module-level singleton
recommendation_agent = RecommendationAgent()
