"""
Supervisor Agent
─────────────────
Orchestrates the full multi-agent pipeline:

  new_reading → MonitoringAgent →
    (if WARNING / CRITICAL)
      → AnomalyAgent
      → ComplianceAgent
      → ForecastingAgent
      → EffluentAgent          (if water params present)
      → FactoryRiskAgent
      → CommunityHealthAgent
      → InvestigationAgent
      → AlertAgent
      → return enriched context

All steps are defensive: a failing sub-agent logs a warning and the
pipeline continues with whatever data is already in context.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any, Dict

logger = logging.getLogger(__name__)

# Water quality parameters — EffluentAgent is invoked only when these are present
WATER_PARAMS = {"ph", "turbidity", "chemical_level"}


class SupervisorAgent:
    """
    Runs the complete agent pipeline on an event context dict and
    returns the enriched context with a final alert_level.
    """

    name = "SupervisorAgent"

    # ── public interface ─────────────────────────────────────────────────────

    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute all agents in sequence and return the final context."""
        if not context.get("event_id"):
            context["event_id"] = f"EVT-{uuid.uuid4().hex[:8].upper()}"
        if not context.get("timestamp"):
            context["timestamp"] = datetime.utcnow().isoformat()

        logger.info("[%s] Pipeline start  event=%s", self.name, context["event_id"])

        # ── Step 1: Monitoring ───────────────────────────────────────────────
        context = self._run(context, "MonitoringAgent",
                            "agents.monitoring.agent", "monitoring_agent")

        status = context.get("current_status", "NORMAL")

        # ── Steps 2-9 only triggered for WARNING / CRITICAL ─────────────────
        if status in ("WARNING", "CRITICAL"):

            # Step 2: Anomaly detection
            context = self._run(context, "AnomalyAgent",
                                "agents.anomaly.agent", "anomaly_agent")

            # Step 3: Compliance / violation check
            context = self._run(context, "ComplianceAgent",
                                "agents.compliance.agent", "compliance_agent")

            # Step 4: Forecasting
            context = self._run(context, "ForecastingAgent",
                                "agents.forecasting.agent", "forecasting_agent")

            # Step 5: Effluent analysis (water params only)
            if any(context.get(p) is not None for p in WATER_PARAMS):
                context = self._run(context, "EffluentAgent",
                                    "agents.effluent.agent", "effluent_agent")
            else:
                context["effluent_status"] = "NOT_APPLICABLE"

            # Step 6: Factory risk profiling
            context = self._run(context, "FactoryRiskAgent",
                                "agents.risk.agent", "factory_risk_agent")

            # Step 7: Community health risk
            context = self._run(context, "CommunityHealthAgent",
                                "agents.health.agent", "community_health_agent")

            # Step 8: Root cause investigation
            context = self._run(context, "InvestigationAgent",
                                "agents.investigation.agent", "investigation_agent")

            # Step 9: Data quality check
            context = self._run(context, "DataQualityAgent",
                                "agents.data_quality.agent", "data_quality_agent")

            # Step 10: Prediction
            context = self._run(context, "PredictionAgent",
                                "agents.prediction.agent", "prediction_agent")

            # Step 11: Recommendations
            context = self._run(context, "RecommendationAgent",
                                "agents.recommendation.agent", "recommendation_agent")

            # Step 12: Citizen advisory
            context = self._run(context, "CitizenAssistantAgent",
                                "agents.citizen.agent", "citizen_assistant_agent")

            # Step 13: Determine consolidated alert level
            context = self._determine_alert_level(context)

            # Step 14: Alert & escalation
            context = self._run(context, "AlertAgent",
                                "agents.alerts.alert_agent", "alert_agent")

        else:
            # NORMAL reading — just record that everything is fine
            context.setdefault("alert_level", "LOW")
            context.setdefault("risk_score", 0.0)
            context.setdefault("risk_level", "LOW")
            context.setdefault("community_risk", "MINIMAL")

        # Combined narrative (always produced)
        context = self._combine(context)

        logger.info(
            "[%s] Pipeline done   event=%s status=%s alert=%s risk=%.1f",
            self.name,
            context["event_id"],
            context.get("current_status"),
            context.get("alert_level"),
            context.get("risk_score") or 0.0,
        )
        return context

    # ── private helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _run(
        context: Dict[str, Any],
        agent_name: str,
        module_path: str,
        singleton_attr: str,
    ) -> Dict[str, Any]:
        """
        Dynamically import *module_path*, retrieve *singleton_attr* and call
        .process(context).  Logs and continues on any exception.
        """
        try:
            import importlib
            mod   = importlib.import_module(module_path)
            agent = getattr(mod, singleton_attr)
            return agent.process(context)
        except Exception as exc:
            logger.warning("[SupervisorAgent] %s failed: %s", agent_name, exc, exc_info=True)
            return context

    def _determine_alert_level(self, context: Dict[str, Any]) -> Dict[str, Any]:
        status    = context.get("current_status", "NORMAL")
        violation = context.get("violation_status", "COMPLIANT")
        anomaly   = context.get("anomaly_score")  or 0.0
        sev       = context.get("violation_severity")
        community = context.get("community_risk", "MINIMAL")
        risk      = context.get("risk_score") or 0.0

        if (
            (status == "CRITICAL" and sev == "CRITICAL")
            or community == "CRITICAL"
            or risk >= 85
        ):
            level = "CRITICAL"
        elif (
            status == "CRITICAL"
            or (violation == "VIOLATION" and sev in ("HIGH", "CRITICAL"))
            or anomaly >= 80
            or community == "HIGH"
            or risk >= 65
        ):
            level = "HIGH"
        elif (
            status == "WARNING"
            or violation == "VIOLATION"
            or anomaly >= 50
            or community in ("MEDIUM",)
            or risk >= 40
        ):
            level = "MEDIUM"
        else:
            level = "LOW"

        context["alert_level"] = level
        return context

    def _combine(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Build a human-readable combined assessment string."""
        parts = []

        status    = context.get("current_status", "NORMAL")
        violation = context.get("violation_status", "COMPLIANT")
        anomaly   = context.get("anomaly_score")  or 0.0
        community = context.get("community_risk", "MINIMAL")
        risk      = context.get("risk_score")     or 0.0
        forecast  = context.get("forecast") or {}
        effluent  = context.get("effluent_status")

        if status == "CRITICAL":
            parts.append("Critical threshold breach detected.")
        elif status == "WARNING":
            parts.append("Warning threshold approached.")

        if violation == "VIOLATION":
            sev = context.get("violation_severity", "")
            exc = context.get("exceedance_percent", 0.0)
            parts.append(f"{sev} regulatory violation — {exc:.1f}% above limit.")

        if anomaly >= 70:
            parts.append(f"High anomaly score ({anomaly:.1f}/100) — statistically unusual pattern.")
        elif anomaly >= 40:
            parts.append(f"Moderate anomaly ({anomaly:.1f}/100).")

        if risk > 0:
            level = context.get("risk_level", "")
            parts.append(f"Factory risk: {risk:.1f}/100 ({level}).")

        if community in ("CRITICAL", "HIGH", "MEDIUM"):
            parts.append(f"Community environmental risk: {community}.")

        trend = forecast.get("trend_direction")
        if trend == "increasing":
            p1h = forecast.get("predicted_1h")
            if p1h is not None:
                parts.append(f"Pollution trend increasing — forecast 1h: {p1h:.1f}.")

        if effluent and effluent not in ("SAFE", "NOT_APPLICABLE"):
            parts.append(f"Water quality status: {effluent}.")

        if not parts:
            parts.append("All parameters within normal range.")

        context["combined_assessment"] = " ".join(parts)
        return context


# ── Module-level singleton ───────────────────────────────────────────────────
supervisor_agent = SupervisorAgent()
