"""
Root Cause Investigation Agent
────────────────────────────────
Investigates pollution incidents by:
  1. Summarizing the current incident
  2. Analysing pre-incident readings for leading indicators
  3. Correlating with production activity
  4. Comparing with similar historical incidents
  5. Proposing likely root causes with confidence levels

Output schema:
{
    incident_summary        : str
    evidence                : [str, ...]
    pre_incident_pattern    : str
    production_correlation  : str
    historical_comparison   : str
    possible_causes         : [{cause, confidence, explanation}, ...]
    confidence_level        : float  0-1
    recommended_investigation : str
    recommended_action      : str
}
"""

from __future__ import annotations

import logging
import statistics
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ── Cause catalogue ──────────────────────────────────────────────────────────
# Each entry: (id, label, conditions_fn)
# conditions_fn(context) → confidence 0-1 or None to skip

CAUSE_CATALOGUE = [
    {
        "id":    "equipment_failure",
        "cause": "Equipment or sensor failure",
        "explanation": (
            "Sudden, isolated spike in a single parameter without corresponding "
            "changes in correlated parameters often indicates equipment malfunction "
            "or sensor error rather than a real process change."
        ),
    },
    {
        "id":    "process_upset",
        "cause": "Unplanned process upset / operational error",
        "explanation": (
            "Multi-parameter rise coinciding with elevated production activity "
            "suggests a process control failure, raw material substitution, or "
            "operator error during a high-throughput period."
        ),
    },
    {
        "id":    "maintenance_bypass",
        "cause": "Pollution control equipment bypass or failure",
        "explanation": (
            "Rapid multi-pollutant increase without proportional production change "
            "points to pollution control equipment (scrubber, ETP) being offline, "
            "bypassed, or underperforming."
        ),
    },
    {
        "id":    "scheduled_discharge",
        "cause": "Scheduled / batch discharge event",
        "explanation": (
            "Periodic spikes aligned with shift changes or batch cycles suggest "
            "known but inadequately treated batch discharge practices."
        ),
    },
    {
        "id":    "raw_material_change",
        "cause": "Change in raw material quality or composition",
        "explanation": (
            "Gradual drift in baseline levels followed by a sudden spike may "
            "indicate a switch to lower-grade or contaminated raw materials."
        ),
    },
    {
        "id":    "wastewater_overflow",
        "cause": "Effluent treatment plant overflow or failure",
        "explanation": (
            "Simultaneous rise in pH deviation, turbidity and chemical levels "
            "strongly indicates ETP overflow or containment failure."
        ),
    },
]


class InvestigationAgent:
    """
    Investigates the root cause of a pollution incident using available
    sensor readings, historical data, and production activity.
    """

    name = "InvestigationAgent"

    # ── public interface ─────────────────────────────────────────────────────

    def investigate(
        self,
        factory_id: str,
        parameter: str,
        current_value: float,
        current_reading: Dict[str, Any],
        history: Optional[List[Dict[str, Any]]] = None,
        similar_incidents: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Investigate a pollution incident.

        Parameters
        ----------
        factory_id        : str
        parameter         : str  — the flagged parameter
        current_value     : float
        current_reading   : full reading dict (may contain status keys)
        history           : recent readings (newest last)
        similar_incidents : past incidents for comparison

        Returns
        -------
        Full investigation report dict.
        """
        history           = history or []
        similar_incidents = similar_incidents or []

        incident_summary     = self._summarize_incident(factory_id, parameter, current_value, current_reading)
        evidence             = self._gather_evidence(current_reading, history)
        pre_pattern          = self._analyze_pre_pattern(parameter, history)
        prod_correlation     = self._analyze_production(current_reading, history)
        historical_comparison= self._compare_historical(parameter, current_value, similar_incidents)

        # Score causes
        scored_causes = self._score_causes(
            parameter, current_reading, history, pre_pattern, prod_correlation,
        )

        # Overall confidence: max cause confidence
        confidence_level = max((c["confidence"] for c in scored_causes), default=0.3)

        recommended_investigation = self._recommend_investigation(scored_causes, parameter)
        recommended_action        = self._recommend_action(current_reading, scored_causes)

        logger.info("[%s] factory=%s param=%s top_cause=%s conf=%.2f",
                    self.name, factory_id, parameter,
                    scored_causes[0]["cause"] if scored_causes else "none",
                    confidence_level)

        return {
            "factory_id":               factory_id,
            "parameter":                parameter,
            "incident_summary":         incident_summary,
            "evidence":                 evidence,
            "pre_incident_pattern":     pre_pattern,
            "production_correlation":   prod_correlation,
            "historical_comparison":    historical_comparison,
            "possible_causes":          scored_causes,
            "confidence_level":         round(confidence_level, 2),
            "recommended_investigation":recommended_investigation,
            "recommended_action":       recommended_action,
            "investigated_at":          datetime.utcnow().isoformat(),
        }

    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Supervisor-compatible process() method."""
        factory_id    = context.get("factory_id", "UNKNOWN")
        parameter     = context.get("parameter", "pm25")
        current_value = context.get("value") or 0.0

        result = self.investigate(
            factory_id, parameter, float(current_value),
            context,
            context.get("history", []),
            context.get("similar_incidents", []),
        )
        context["investigation"] = result
        return context

    # ── investigation steps ──────────────────────────────────────────────────

    def _summarize_incident(
        self,
        factory_id: str,
        parameter: str,
        value: float,
        reading: Dict[str, Any],
    ) -> str:
        status  = reading.get("current_status", "UNKNOWN")
        sev     = reading.get("violation_severity", "")
        exc     = reading.get("exceedance_percent") or 0.0
        anomaly = reading.get("anomaly_score") or 0.0

        lines = [
            f"Factory {factory_id} reported a {status} event for {parameter.upper()} "
            f"at {value:.2f} units."
        ]
        if exc > 0:
            lines.append(f"This exceeds the regulatory limit by {exc:.1f}% (severity: {sev}).")
        if anomaly >= 50:
            lines.append(f"Anomaly detection score: {anomaly:.1f}/100 — statistically unusual.")
        return " ".join(lines)

    def _gather_evidence(
        self,
        reading: Dict[str, Any],
        history: List[Dict[str, Any]],
    ) -> List[str]:
        evidence = []

        # Current state evidence
        for key, label in [
            ("current_status",    "Monitoring status"),
            ("violation_severity","Violation severity"),
            ("anomaly_score",     "Anomaly score"),
            ("exceedance_percent","Exceedance"),
        ]:
            val = reading.get(key)
            if val is not None:
                evidence.append(f"{label}: {val}")

        # Historical baseline
        if history:
            for param in ["pm25", "pm10", "so2", "no2", "co"]:
                vals = [float(r[param]) for r in history if r.get(param) is not None]
                if len(vals) >= 5:
                    mu  = statistics.mean(vals)
                    std = statistics.stdev(vals) if len(vals) >= 2 else 0
                    evidence.append(
                        f"Historical {param.upper()}: mean={mu:.2f}, std={std:.2f} "
                        f"over last {len(vals)} readings."
                    )

        return evidence

    def _analyze_pre_pattern(
        self,
        parameter: str,
        history: List[Dict[str, Any]],
    ) -> str:
        if len(history) < 5:
            return "Insufficient history to determine pre-incident pattern."

        vals = [float(r[parameter]) for r in history if r.get(parameter) is not None]
        if len(vals) < 5:
            return f"Not enough {parameter} history for pre-incident pattern analysis."

        recent = vals[-3:]
        older  = vals[:-3]

        mu_recent = sum(recent) / len(recent)
        mu_older  = sum(older)  / len(older)

        if mu_recent > mu_older * 1.5:
            return (
                f"{parameter.upper()} was rising sharply in the 3 readings before the incident "
                f"(from {mu_older:.2f} to {mu_recent:.2f}). "
                "This suggests a gradual build-up rather than a sudden event."
            )
        if mu_recent > mu_older * 1.1:
            return (
                f"Slight upward trend in {parameter.upper()} pre-incident "
                f"({mu_older:.2f} → {mu_recent:.2f}). "
                "Values were approaching the threshold before the breach."
            )
        return (
            f"{parameter.upper()} was stable at approximately {mu_older:.2f} before a sudden spike. "
            "This pattern is consistent with an abrupt process event."
        )

    def _analyze_production(
        self,
        reading: Dict[str, Any],
        history: List[Dict[str, Any]],
    ) -> str:
        prod = reading.get("production_activity")
        if prod is None:
            return "Production activity data not available."

        prod = float(prod)

        hist_prod = [float(r["production_activity"]) for r in history
                     if r.get("production_activity") is not None]
        if not hist_prod:
            return f"Current production activity: {prod:.1f}. No historical comparison available."

        avg = sum(hist_prod) / len(hist_prod)

        if prod > avg * 1.3:
            return (
                f"Production activity ({prod:.1f}) is significantly above historical average "
                f"({avg:.1f}). Elevated output may have overwhelmed pollution control capacity."
            )
        if prod < avg * 0.7:
            return (
                f"Production activity ({prod:.1f}) is below historical average ({avg:.1f}). "
                "Pollution spike during low production may indicate a maintenance or bypass issue."
            )
        return (
            f"Production activity ({prod:.1f}) is near historical average ({avg:.1f}). "
            "Emissions disproportionate to output — potential control equipment issue."
        )

    def _compare_historical(
        self,
        parameter: str,
        current_value: float,
        similar_incidents: List[Dict[str, Any]],
    ) -> str:
        if not similar_incidents:
            return "No similar historical incidents available for comparison."

        same_param = [i for i in similar_incidents if i.get("parameter") == parameter]
        if not same_param:
            return f"No historical incidents found specifically for {parameter.upper()}."

        n = len(same_param)
        causes = [i.get("root_cause") or i.get("cause", "unknown") for i in same_param]
        freq_cause = max(set(causes), key=causes.count) if causes else "unknown"

        return (
            f"Found {n} similar historical incident(s) for {parameter.upper()}. "
            f"Most common root cause in past incidents: '{freq_cause}'. "
            "Current event follows a comparable pattern."
        )

    # ── cause scoring ────────────────────────────────────────────────────────

    def _score_causes(
        self,
        parameter: str,
        reading: Dict[str, Any],
        history: List[Dict[str, Any]],
        pre_pattern: str,
        prod_correlation: str,
    ) -> List[Dict[str, Any]]:
        scored = []

        anomaly  = reading.get("anomaly_score") or 0.0
        exc      = reading.get("exceedance_percent") or 0.0
        prod     = float(reading.get("production_activity") or 1.0)
        status   = reading.get("current_status", "NORMAL")

        # Determine number of co-elevated water params
        water_elevated = sum(
            1 for p in ("ph", "turbidity", "chemical_level")
            if (reading.get(p) or 0) > 0
        )

        for cat in CAUSE_CATALOGUE:
            cid  = cat["id"]
            conf = 0.0

            if cid == "equipment_failure":
                # High anomaly score, single-param spike
                if anomaly >= 70:
                    conf = 0.6
                elif anomaly >= 40:
                    conf = 0.35

            elif cid == "process_upset":
                # Multi-param + high production
                if "above historical" in prod_correlation and exc > 30:
                    conf = 0.7
                elif exc > 50:
                    conf = 0.5

            elif cid == "maintenance_bypass":
                # Multi-param without production spike
                if "near historical" in prod_correlation or "below" in prod_correlation:
                    if exc > 50 or status == "CRITICAL":
                        conf = 0.65

            elif cid == "scheduled_discharge":
                # Moderate anomaly, predictable pattern
                if "stable at" in pre_pattern and anomaly < 50:
                    conf = 0.4

            elif cid == "raw_material_change":
                # Gradual rise pre-incident
                if "rising sharply" in pre_pattern or "upward trend" in pre_pattern:
                    conf = 0.55

            elif cid == "wastewater_overflow":
                # Multiple water params elevated
                if water_elevated >= 2 or parameter in ("ph", "turbidity", "chemical_level"):
                    conf = 0.6

            if conf > 0:
                scored.append({
                    "cause":       cat["cause"],
                    "confidence":  round(conf, 2),
                    "explanation": cat["explanation"],
                })

        # Sort by confidence descending
        scored.sort(key=lambda x: x["confidence"], reverse=True)

        # If nothing scored, add a fallback
        if not scored:
            scored.append({
                "cause":       "Undetermined — requires on-site investigation",
                "confidence":  0.2,
                "explanation": "Insufficient data to identify a dominant root cause.",
            })

        return scored

    # ── recommendations ──────────────────────────────────────────────────────

    def _recommend_investigation(
        self,
        causes: List[Dict[str, Any]],
        parameter: str,
    ) -> str:
        if not causes:
            return "Conduct on-site inspection and review all sensor data."

        top = causes[0]["cause"].lower()

        if "equipment" in top or "sensor" in top:
            return (
                "Inspect and calibrate the affected sensor. Cross-verify readings with "
                "manual sampling. Check nearby equipment for mechanical faults."
            )
        if "bypass" in top or "control" in top:
            return (
                "Immediately audit pollution control equipment status. Inspect scrubber, "
                "ETP, and filter logs. Review operator maintenance records."
            )
        if "process" in top or "operational" in top:
            return (
                "Review production logs at the time of incident. Identify the process unit "
                "responsible. Interview shift operators."
            )
        if "discharge" in top or "batch" in top:
            return (
                "Correlate incident time with batch schedules and shift changeovers. "
                "Review ETP discharge logs."
            )
        if "wastewater" in top or "overflow" in top:
            return (
                "Inspect ETP holding tanks for overflow. Check containment structures. "
                "Collect effluent samples for laboratory analysis."
            )
        return (
            "Conduct a structured root cause analysis (RCA) including sensor audit, "
            "process review, and environmental sampling."
        )

    def _recommend_action(
        self,
        reading: Dict[str, Any],
        causes: List[Dict[str, Any]],
    ) -> str:
        status = reading.get("current_status", "NORMAL")
        sev    = reading.get("violation_severity", "")

        if status == "CRITICAL" or sev == "CRITICAL":
            return (
                "IMMEDIATE: Consider temporary production halt. Notify regulatory authority. "
                "Deploy emergency sampling team. Issue community advisory if risk is HIGH."
            )
        if status == "WARNING" or sev in ("HIGH", "MEDIUM"):
            return (
                "Increase monitoring frequency to every 15 minutes. "
                "Notify factory environmental officer. Prepare incident report."
            )
        return (
            "Continue enhanced monitoring. Log the event. "
            "Review findings at next environmental compliance meeting."
        )


# ── Module-level singleton ───────────────────────────────────────────────────
investigation_agent = InvestigationAgent()
