"""
Monitoring Agent
─────────────────
Reads incoming sensor data, validates it, detects basic threshold
breaches and forwards WARNING / CRITICAL events to the supervisor.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# ── Configured limits (mirrors pollution_limits table) ──────────────────────

LIMITS: Dict[str, Dict[str, Any]] = {
    "pm25":          {"limit": 60,   "unit": "µg/m³",  "warn_pct": 0.80},
    "pm10":          {"limit": 100,  "unit": "µg/m³",  "warn_pct": 0.80},
    "so2":           {"limit": 80,   "unit": "µg/m³",  "warn_pct": 0.80},
    "no2":           {"limit": 80,   "unit": "µg/m³",  "warn_pct": 0.80},
    "co":            {"limit": 10,   "unit": "mg/m³",  "warn_pct": 0.80},
    "ph":            {"limit_lo": 6.5, "limit_hi": 8.5, "unit": "pH", "warn_pct": 0.05},
    "turbidity":     {"limit": 10,   "unit": "NTU",    "warn_pct": 0.80},
    "chemical_level":{"limit": 50,   "unit": "mg/L",   "warn_pct": 0.80},
}

REQUIRED_FIELDS = ["pm25", "pm10", "so2", "no2", "co", "temperature",
                   "humidity", "wind_speed", "wind_direction"]

VALID_RANGES = {
    "pm25": (0, 1000), "pm10": (0, 2000), "so2": (0, 2000),
    "no2": (0, 2000), "co": (0, 200), "temperature": (-20, 60),
    "humidity": (0, 100), "wind_speed": (0, 100), "wind_direction": (0, 360),
    "ph": (0, 14), "turbidity": (0, 10000), "chemical_level": (0, 5000),
}


class MonitoringAgent:
    """
    Validates incoming sensor readings and classifies them as
    NORMAL / WARNING / CRITICAL based on configured pollution limits.
    """

    name = "MonitoringAgent"

    # ── public interface ─────────────────────────────────────────────────────

    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Accepts an agent context dict, fills context["current_status"] and
        returns the updated context.
        """
        factory_id  = context.get("factory_id", "UNKNOWN")
        parameter   = context.get("parameter")
        value       = context.get("value")

        if value is None or parameter is None:
            context["current_status"] = "UNKNOWN"
            context["monitoring_notes"] = "Insufficient data — missing parameter or value."
            return context

        status, notes = self._classify(parameter, value)
        context["current_status"] = status
        context["monitoring_notes"] = notes

        logger.info(
            "[%s] factory=%s param=%s value=%s → %s",
            self.name, factory_id, parameter, value, status,
        )
        return context

    def validate_reading(self, reading: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a raw sensor reading dict.
        Returns {"valid": bool, "errors": [...], "warnings": [...]}
        """
        errors: list   = []
        warnings: list = []

        # Check required fields
        for field in REQUIRED_FIELDS:
            if reading.get(field) is None:
                errors.append(f"Missing required field: {field}")

        # Range checks
        for field, (lo, hi) in VALID_RANGES.items():
            val = reading.get(field)
            if val is None:
                continue
            try:
                v = float(val)
            except (TypeError, ValueError):
                errors.append(f"Non-numeric value for {field}: {val}")
                continue
            if not (lo <= v <= hi):
                errors.append(f"{field}={v} is outside valid range [{lo}, {hi}]")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
        }

    def scan_batch(self, readings: list, limits_override: Optional[dict] = None) -> Dict[str, Any]:
        """
        Scan a list of reading dicts against limits.
        Returns summary statistics.
        """
        limits = limits_override or LIMITS
        normal = warning = critical = 0
        flagged = []

        for r in readings:
            worst = "NORMAL"
            for param, cfg in limits.items():
                val = r.get(param)
                if val is None:
                    continue
                status, _ = self._classify(param, float(val), cfg)
                if status == "CRITICAL":
                    worst = "CRITICAL"
                elif status == "WARNING" and worst != "CRITICAL":
                    worst = "WARNING"

            if worst == "NORMAL":
                normal += 1
            elif worst == "WARNING":
                warning += 1
                flagged.append({"timestamp": r.get("timestamp"), "status": "WARNING"})
            else:
                critical += 1
                flagged.append({"timestamp": r.get("timestamp"), "status": "CRITICAL"})

        return {
            "total": len(readings),
            "normal": normal,
            "warning": warning,
            "critical": critical,
            "flagged_events": flagged[:50],  # cap response size
        }

    # ── private helpers ──────────────────────────────────────────────────────

    def _classify(
        self,
        parameter: str,
        value: float,
        cfg: Optional[dict] = None,
    ) -> tuple[str, str]:
        cfg = cfg or LIMITS.get(parameter)
        if cfg is None:
            return "NORMAL", f"No limit configured for {parameter}."

        if parameter == "ph":
            lo, hi = cfg.get("limit_lo", 6.5), cfg.get("limit_hi", 8.5)
            deviation = max(0, lo - value, value - hi)
            warn_threshold = (hi - lo) * cfg.get("warn_pct", 0.05)
            if deviation <= 0:
                return "NORMAL", f"pH {value} within [{lo}, {hi}]."
            if deviation <= warn_threshold:
                return "WARNING", f"pH {value} near boundary [{lo}, {hi}]."
            return "CRITICAL", f"pH {value} outside [{lo}, {hi}] by {deviation:.2f}."

        limit = cfg.get("limit", 9999)
        warn_threshold = limit * cfg.get("warn_pct", 0.80)
        unit = cfg.get("unit", "")

        if value < warn_threshold:
            return "NORMAL", f"{parameter.upper()} {value} {unit} — within safe range."
        if value < limit:
            return "WARNING", (
                f"{parameter.upper()} {value} {unit} approaching limit {limit} {unit} "
                f"({value / limit * 100:.1f}% of limit)."
            )
        pct_over = (value - limit) / limit * 100
        return "CRITICAL", (
            f"{parameter.upper()} {value} {unit} EXCEEDS limit {limit} {unit} "
            f"by {pct_over:.1f}%."
        )


# ── Module-level singleton ───────────────────────────────────────────────────
monitoring_agent = MonitoringAgent()
