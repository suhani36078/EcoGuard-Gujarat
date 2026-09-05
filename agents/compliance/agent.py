"""
Compliance / Violation Agent
──────────────────────────────
Compares sensor readings against configurable pollution_limits,
calculates exceedance percentage, determines severity, tracks
violation duration, and checks violation history.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ── Default limits (overridden by DB values at runtime) ─────────────────────

DEFAULT_LIMITS: Dict[str, Dict[str, Any]] = {
    "pm25":          {"limit": 60,   "unit": "µg/m³"},
    "pm10":          {"limit": 100,  "unit": "µg/m³"},
    "so2":           {"limit": 80,   "unit": "µg/m³"},
    "no2":           {"limit": 80,   "unit": "µg/m³"},
    "co":            {"limit": 10,   "unit": "mg/m³"},
    "ph_hi":         {"limit": 8.5,  "unit": "pH",   "param": "ph"},
    "ph_lo":         {"limit": 6.5,  "unit": "pH",   "param": "ph", "direction": "below"},
    "turbidity":     {"limit": 10,   "unit": "NTU"},
    "chemical_level":{"limit": 50,   "unit": "mg/L"},
}

SEVERITY_THRESHOLDS = {
    # exceedance % → severity
    "pm25":          [(0, "LOW"), (50, "MEDIUM"), (100, "HIGH"), (200, "CRITICAL")],
    "pm10":          [(0, "LOW"), (50, "MEDIUM"), (100, "HIGH"), (200, "CRITICAL")],
    "so2":           [(0, "LOW"), (50, "MEDIUM"), (100, "HIGH"), (150, "CRITICAL")],
    "no2":           [(0, "LOW"), (50, "MEDIUM"), (100, "HIGH"), (150, "CRITICAL")],
    "co":            [(0, "LOW"), (50, "MEDIUM"), (100, "HIGH"), (200, "CRITICAL")],
    "ph":            [(0, "LOW"), (5,  "MEDIUM"), (15,  "HIGH"), (25,  "CRITICAL")],
    "turbidity":     [(0, "LOW"), (100,"MEDIUM"), (400, "HIGH"), (900, "CRITICAL")],
    "chemical_level":[(0, "LOW"), (50, "MEDIUM"), (100, "HIGH"), (200, "CRITICAL")],
}


class ComplianceAgent:
    """
    Checks readings against pollution limits and records violations.
    """

    name = "ComplianceAgent"

    def __init__(self, limits: Optional[Dict[str, Any]] = None):
        self._limits = limits or DEFAULT_LIMITS

    # ── public interface ─────────────────────────────────────────────────────

    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fills context["violation_status"] and related fields.
        """
        parameter = context.get("parameter")
        value     = context.get("value")

        if value is None or parameter is None:
            context["violation_status"] = "UNKNOWN"
            return context

        result = self.check_single(parameter, float(value))
        context["violation_status"] = result["status"]
        context["exceedance_percent"] = result.get("exceedance_percent", 0)
        context["violation_severity"] = result.get("severity")
        context["limit_value"] = result.get("limit_value")
        return context

    def check_single(self, parameter: str, value: float) -> Dict[str, Any]:
        """
        Check a single (parameter, value) pair against limits.
        Returns a dict with: status, limit_value, exceedance_percent, severity, message.
        """
        if parameter == "ph":
            return self._check_ph(value)

        cfg_key = parameter
        cfg = self._limits.get(cfg_key)
        if cfg is None:
            return {"status": "NO_LIMIT", "message": f"No limit configured for {parameter}."}

        limit = cfg["limit"]
        unit  = cfg.get("unit", "")

        if value <= limit:
            return {
                "status": "COMPLIANT",
                "parameter": parameter,
                "value": value,
                "limit_value": limit,
                "exceedance_percent": 0.0,
                "severity": None,
                "message": f"{parameter.upper()} {value} {unit} — within limit {limit} {unit}.",
            }

        exceedance = round((value - limit) / limit * 100, 2)
        severity = self._severity(parameter, exceedance)
        return {
            "status": "VIOLATION",
            "parameter": parameter,
            "value": value,
            "limit_value": limit,
            "exceedance_percent": exceedance,
            "severity": severity,
            "message": (
                f"{parameter.upper()} {value} {unit} exceeds limit {limit} {unit} "
                f"by {exceedance:.1f}%. Severity: {severity}."
            ),
        }

    def check_reading(self, reading: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Check all parameters in a reading dict.
        Returns a list of violation records (only violations).
        """
        violations = []
        params = ["pm25", "pm10", "so2", "no2", "co", "turbidity", "chemical_level", "ph"]
        for param in params:
            val = reading.get(param)
            if val is None:
                continue
            result = self.check_single(param, float(val))
            if result.get("status") == "VIOLATION":
                result["factory_id"] = reading.get("factory_id")
                result["detected_at"] = reading.get("timestamp", datetime.utcnow())
                violations.append(result)
        return violations

    def update_limits(self, new_limits: Dict[str, Any]) -> None:
        """Allow runtime limit reconfiguration."""
        self._limits.update(new_limits)
        logger.info("[%s] Limits updated: %s", self.name, list(new_limits.keys()))

    def check_violation_history(
        self,
        violations: List[Dict[str, Any]],
        lookback_count: int = 30,
    ) -> Dict[str, Any]:
        """
        Analyse a list of past violation records.
        Returns repeat-offender stats.
        """
        total = len(violations)
        by_param: Dict[str, int] = {}
        by_severity: Dict[str, int] = {}
        for v in violations[-lookback_count:]:
            param = v.get("parameter", "unknown")
            sev   = v.get("severity", "UNKNOWN")
            by_param[param]    = by_param.get(param, 0) + 1
            by_severity[sev]   = by_severity.get(sev, 0) + 1

        repeat_offender = total >= 10
        most_frequent   = max(by_param, key=by_param.get) if by_param else None

        return {
            "total_violations": total,
            "repeat_offender": repeat_offender,
            "most_frequent_param": most_frequent,
            "violations_by_param": by_param,
            "violations_by_severity": by_severity,
            "compliance_rate": round(max(0, 1 - total / max(lookback_count, 1)) * 100, 1),
        }

    def track_duration(
        self,
        violations: List[Dict[str, Any]],
        parameter: str,
    ) -> Optional[float]:
        """
        Calculate total violation duration in hours for a given parameter.
        Assumes violations are sorted by detected_at.
        """
        param_viols = [
            v for v in violations
            if v.get("parameter") == parameter and v.get("detected_at")
        ]
        if not param_viols:
            return None

        first = param_viols[0]["detected_at"]
        last  = param_viols[-1].get("resolved_at") or param_viols[-1]["detected_at"]

        if isinstance(first, str):
            first = datetime.fromisoformat(first)
        if isinstance(last, str):
            last = datetime.fromisoformat(last)

        duration = (last - first).total_seconds() / 3600
        return round(duration, 2)

    # ── private helpers ──────────────────────────────────────────────────────

    def _check_ph(self, value: float) -> Dict[str, Any]:
        lo, hi = 6.5, 8.5
        if lo <= value <= hi:
            return {
                "status": "COMPLIANT",
                "parameter": "ph",
                "value": value,
                "limit_value": hi,
                "exceedance_percent": 0.0,
                "severity": None,
                "message": f"pH {value} within [{lo}, {hi}].",
            }
        if value > hi:
            exceedance = round((value - hi) / hi * 100, 2)
            limit_val = hi
        else:
            exceedance = round((lo - value) / lo * 100, 2)
            limit_val = lo

        severity = self._severity("ph", exceedance)
        direction = "above upper" if value > hi else "below lower"
        return {
            "status": "VIOLATION",
            "parameter": "ph",
            "value": value,
            "limit_value": limit_val,
            "exceedance_percent": exceedance,
            "severity": severity,
            "message": (
                f"pH {value} is {direction} limit ({limit_val}). "
                f"Exceedance: {exceedance:.1f}%. Severity: {severity}."
            ),
        }

    def _severity(self, parameter: str, exceedance_pct: float) -> str:
        thresholds = SEVERITY_THRESHOLDS.get(parameter, [(0, "LOW"), (50, "MEDIUM"), (100, "HIGH"), (200, "CRITICAL")])
        severity = "LOW"
        for threshold, label in thresholds:
            if exceedance_pct >= threshold:
                severity = label
        return severity


# ── Module-level singleton ───────────────────────────────────────────────────
compliance_agent = ComplianceAgent()
