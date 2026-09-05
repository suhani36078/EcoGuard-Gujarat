"""
Regulatory Alert & Escalation Agent
──────────────────────────────────────
Generates, deduplicates, and escalates regulatory alerts.

Severity → Recipients:
  LOW      → dashboard notification only
  MEDIUM   → factory environmental officer
  HIGH     → factory + regulatory team
  CRITICAL → factory + regulatory + community warning

Duplicate prevention: same factory+parameter within 30 min → skip.
Escalation: unacknowledged after X minutes → escalate one level.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ── Escalation timeouts (minutes) ───────────────────────────────────────────
ESCALATION_TIMEOUT: Dict[str, int] = {
    "LOW":      60,   # escalate if unacknowledged after 60 min
    "MEDIUM":   30,
    "HIGH":     15,
    "CRITICAL":  5,
}

# ── Recipient groups ─────────────────────────────────────────────────────────
RECIPIENTS: Dict[str, List[str]] = {
    "LOW":      ["dashboard"],
    "MEDIUM":   ["dashboard", "factory_env_officer"],
    "HIGH":     ["dashboard", "factory_env_officer", "regulatory_team"],
    "CRITICAL": ["dashboard", "factory_env_officer", "regulatory_team", "community_warning"],
}

# Deduplication window in minutes
DEDUP_WINDOW_MINUTES = 30

# Escalation ladder
ESCALATION_LADDER = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]


class AlertAgent:
    """
    Manages alert generation, deduplication, and escalation for regulatory events.

    In production this should be backed by the database; here it maintains
    an in-memory registry so it can run standalone or within the supervisor pipeline.
    """

    name = "AlertAgent"

    def __init__(self):
        # In-memory alert registry: {alert_id: alert_dict}
        self._registry: Dict[str, Dict[str, Any]] = {}

    # ── public interface ─────────────────────────────────────────────────────

    def generate_alert(
        self,
        factory_id: str,
        parameter: str,
        severity: str,
        message: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate a new alert (or return the duplicate if within dedup window).

        Returns
        -------
        {
            alert_id, factory_id, parameter, severity, message,
            recipients, status, created_at, is_duplicate, escalation_timeout_min
        }
        """
        severity = severity.upper()
        if severity not in ESCALATION_LADDER:
            severity = "LOW"

        context = context or {}

        # ── Deduplication check ──────────────────────────────────────────────
        duplicate = self._find_duplicate(factory_id, parameter, severity)
        if duplicate:
            logger.info(
                "[%s] Duplicate suppressed: factory=%s param=%s sev=%s",
                self.name, factory_id, parameter, severity,
            )
            return {**duplicate, "is_duplicate": True}

        # ── Build alert ──────────────────────────────────────────────────────
        alert_id   = f"ALERT-{uuid.uuid4().hex[:8].upper()}"
        recipients = RECIPIENTS.get(severity, ["dashboard"])
        now        = datetime.utcnow()

        alert = {
            "alert_id":               alert_id,
            "factory_id":             factory_id,
            "parameter":              parameter,
            "severity":               severity,
            "message":                message,
            "recipients":             recipients,
            "status":                 "pending",
            "created_at":             now.isoformat(),
            "acknowledged_at":        None,
            "resolved_at":            None,
            "escalation_timeout_min": ESCALATION_TIMEOUT.get(severity, 60),
            "escalated_to":           None,
            "is_duplicate":           False,
            "context_snapshot": {
                "anomaly_score":     context.get("anomaly_score"),
                "violation_status":  context.get("violation_status"),
                "risk_score":        context.get("risk_score"),
                "community_risk":    context.get("community_risk"),
            },
        }

        self._registry[alert_id] = alert
        logger.info("[%s] Created %s: factory=%s param=%s sev=%s", self.name, alert_id, factory_id, parameter, severity)
        return alert

    def acknowledge(self, alert_id: str) -> Dict[str, Any]:
        """Mark alert as acknowledged."""
        alert = self._registry.get(alert_id)
        if not alert:
            return {"error": f"Alert {alert_id} not found."}
        alert["status"]           = "acknowledged"
        alert["acknowledged_at"]  = datetime.utcnow().isoformat()
        logger.info("[%s] Acknowledged: %s", self.name, alert_id)
        return alert

    def resolve(self, alert_id: str) -> Dict[str, Any]:
        """Mark alert as resolved."""
        alert = self._registry.get(alert_id)
        if not alert:
            return {"error": f"Alert {alert_id} not found."}
        alert["status"]      = "resolved"
        alert["resolved_at"] = datetime.utcnow().isoformat()
        logger.info("[%s] Resolved: %s", self.name, alert_id)
        return alert

    def check_escalations(self) -> List[Dict[str, Any]]:
        """
        Check all pending/acknowledged alerts and escalate those that have
        exceeded their timeout.  Returns list of escalated alerts.
        """
        escalated = []
        now = datetime.utcnow()

        for alert_id, alert in self._registry.items():
            if alert.get("status") in ("resolved",):
                continue

            severity       = alert.get("severity", "LOW")
            timeout_min    = ESCALATION_TIMEOUT.get(severity, 60)
            created_at_str = alert.get("created_at")

            try:
                created_at = datetime.fromisoformat(created_at_str)
            except (TypeError, ValueError):
                continue

            age_min = (now - created_at).total_seconds() / 60

            if age_min >= timeout_min and alert.get("status") != "escalated":
                new_severity = self._next_severity(severity)
                if new_severity != severity:
                    alert["status"]       = "escalated"
                    alert["escalated_to"] = new_severity
                    alert["recipients"]   = RECIPIENTS.get(new_severity, alert["recipients"])
                    logger.warning(
                        "[%s] Escalated %s: %s → %s after %.0f min",
                        self.name, alert_id, severity, new_severity, age_min,
                    )
                    escalated.append(dict(alert))

        return escalated

    def get_active_alerts(self, factory_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Return all active (non-resolved) alerts, optionally filtered by factory."""
        alerts = [a for a in self._registry.values() if a.get("status") != "resolved"]
        if factory_id:
            alerts = [a for a in alerts if a.get("factory_id") == factory_id]
        return sorted(alerts, key=lambda x: x.get("created_at", ""), reverse=True)

    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Supervisor-compatible process() method."""
        factory_id = context.get("factory_id", "UNKNOWN")
        parameter  = context.get("parameter", "unknown")
        alert_level = context.get("alert_level", "LOW")

        # Only generate alert for WARNING/CRITICAL states
        status = context.get("current_status", "NORMAL")
        if status == "NORMAL" and alert_level == "LOW":
            context["alert_generated"] = False
            context["alert_result"]    = None
            return context

        message = self._build_message(context)
        alert   = self.generate_alert(factory_id, parameter, alert_level, message, context)
        context["alert_generated"] = not alert.get("is_duplicate", False)
        context["alert_result"]    = alert
        return context

    # ── internal helpers ─────────────────────────────────────────────────────

    def _find_duplicate(
        self,
        factory_id: str,
        parameter: str,
        severity: str,
    ) -> Optional[Dict[str, Any]]:
        cutoff = datetime.utcnow() - timedelta(minutes=DEDUP_WINDOW_MINUTES)
        for alert in self._registry.values():
            if (
                alert.get("factory_id") == factory_id
                and alert.get("parameter") == parameter
                and alert.get("severity") == severity
                and alert.get("status") not in ("resolved",)
            ):
                try:
                    created_at = datetime.fromisoformat(alert["created_at"])
                    if created_at >= cutoff:
                        return alert
                except (TypeError, ValueError):
                    pass
        return None

    @staticmethod
    def _next_severity(current: str) -> str:
        idx = ESCALATION_LADDER.index(current) if current in ESCALATION_LADDER else 0
        if idx < len(ESCALATION_LADDER) - 1:
            return ESCALATION_LADDER[idx + 1]
        return current

    def _build_message(self, context: Dict[str, Any]) -> str:
        factory_id = context.get("factory_id", "UNKNOWN")
        parameter  = context.get("parameter", "unknown").upper()
        value      = context.get("value")
        status     = context.get("current_status", "UNKNOWN")
        exc        = context.get("exceedance_percent") or 0.0
        risk       = context.get("risk_score") or 0.0
        community  = context.get("community_risk", "")
        alert_lvl  = context.get("alert_level", "")

        parts = [
            f"[{alert_lvl}] Factory {factory_id}: {parameter}",
        ]

        if value is not None:
            parts.append(f"= {value}")

        if status in ("WARNING", "CRITICAL"):
            parts.append(f"({status})")

        if exc > 0:
            parts.append(f"— {exc:.1f}% above regulatory limit.")

        if risk > 0:
            parts.append(f"Risk score: {risk:.1f}/100.")

        if community in ("HIGH", "CRITICAL"):
            parts.append(f"Community risk: {community}.")

        return " ".join(parts)


# ── Module-level singleton ───────────────────────────────────────────────────
alert_agent = AlertAgent()
