"""
Effluent / Water Quality Agent
────────────────────────────────
Analyzes industrial wastewater parameters:
  - pH (normal 6.5–8.5)
  - Turbidity (limit 10 NTU)
  - Chemical levels
  - Abnormal discharge pattern detection

Output: SAFE / WARNING / UNSAFE with structured explanation.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ── Thresholds ───────────────────────────────────────────────────────────────

PH_NORMAL_LO  = 6.5
PH_NORMAL_HI  = 8.5
PH_WARN_LO    = 6.0
PH_WARN_HI    = 9.0

TURBIDITY_LIMIT     = 10.0    # NTU
TURBIDITY_WARN      = 8.0     # NTU

CHEMICAL_LIMIT      = 50.0    # mg/L
CHEMICAL_WARN       = 40.0    # mg/L

# Spike ratio: current vs rolling mean that triggers pattern alert
SPIKE_RATIO         = 2.5

# Water-quality parameters
WATER_PARAMS = ["ph", "turbidity", "chemical_level"]


class EffluentAgent:
    """
    Classifies effluent / wastewater quality from a sensor reading context.
    """

    name = "EffluentAgent"

    # ── public interface ─────────────────────────────────────────────────────

    def analyze(
        self,
        factory_id: str,
        reading: Dict[str, Any],
        history: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Analyze a single reading (and optional history) for water quality.

        Returns
        -------
        {
            status        : SAFE | WARNING | UNSAFE
            overall_level : SAFE | WARNING | UNSAFE
            ph_analysis   : {...}
            turbidity_analysis : {...}
            chemical_analysis  : {...}
            discharge_pattern  : {...}
            issues        : [str, ...]
            explanation   : str
        }
        """
        ph_result      = self._analyze_ph(reading.get("ph"))
        turb_result    = self._analyze_turbidity(reading.get("turbidity"))
        chem_result    = self._analyze_chemical(reading.get("chemical_level"))
        pattern_result = self._detect_discharge_pattern(reading, history or [])

        issues = []
        statuses = []

        for label, result in [
            ("pH", ph_result),
            ("Turbidity", turb_result),
            ("Chemical level", chem_result),
        ]:
            s = result.get("status", "SAFE")
            statuses.append(s)
            if s != "SAFE":
                issues.append(result.get("message", f"{label} issue detected."))

        if pattern_result.get("anomalous"):
            statuses.append("WARNING")
            issues.append(pattern_result.get("description", "Abnormal discharge pattern."))

        # Overall: worst status wins
        if "UNSAFE" in statuses:
            overall = "UNSAFE"
        elif "WARNING" in statuses:
            overall = "WARNING"
        else:
            overall = "SAFE"

        explanation = self._build_explanation(overall, issues, reading)

        logger.info("[%s] factory=%s overall=%s", self.name, factory_id, overall)

        return {
            "factory_id":          factory_id,
            "status":              overall,
            "overall_level":       overall,
            "ph_analysis":         ph_result,
            "turbidity_analysis":  turb_result,
            "chemical_analysis":   chem_result,
            "discharge_pattern":   pattern_result,
            "issues":              issues,
            "explanation":         explanation,
            "analyzed_at":         datetime.utcnow().isoformat(),
        }

    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Supervisor-compatible process() method."""
        factory_id = context.get("factory_id", "UNKNOWN")

        # Only relevant if water parameters are present
        has_water = any(context.get(p) is not None for p in WATER_PARAMS)
        if not has_water:
            context["effluent_status"] = "NOT_APPLICABLE"
            context["effluent_result"] = {"status": "NOT_APPLICABLE", "explanation": "No water parameters in reading."}
            return context

        result = self.analyze(factory_id, context, context.get("history", []))
        context["effluent_status"] = result["status"]
        context["effluent_result"] = result
        return context

    # ── parameter-level analysis ─────────────────────────────────────────────

    def _analyze_ph(self, value: Optional[float]) -> Dict[str, Any]:
        if value is None:
            return {"status": "SAFE", "parameter": "ph", "value": None, "message": "pH not measured."}

        v = float(value)
        if PH_NORMAL_LO <= v <= PH_NORMAL_HI:
            status  = "SAFE"
            message = f"pH {v:.2f} is within normal range [{PH_NORMAL_LO}, {PH_NORMAL_HI}]."
        elif PH_WARN_LO <= v <= PH_WARN_HI:
            status  = "WARNING"
            message = (
                f"pH {v:.2f} is outside normal range [{PH_NORMAL_LO}, {PH_NORMAL_HI}] "
                f"but within warning limits [{PH_WARN_LO}, {PH_WARN_HI}]. "
                "Monitor closely — may indicate process upset."
            )
        else:
            status  = "UNSAFE"
            direction = "acidic" if v < PH_WARN_LO else "alkaline"
            message = (
                f"pH {v:.2f} is critically {direction} — well outside acceptable limits. "
                "Risk of aquatic ecosystem damage and regulatory violation."
            )

        return {
            "status":    status,
            "parameter": "ph",
            "value":     v,
            "normal_range": [PH_NORMAL_LO, PH_NORMAL_HI],
            "message":   message,
        }

    def _analyze_turbidity(self, value: Optional[float]) -> Dict[str, Any]:
        if value is None:
            return {"status": "SAFE", "parameter": "turbidity", "value": None, "message": "Turbidity not measured."}

        v = float(value)
        if v <= TURBIDITY_WARN:
            status  = "SAFE"
            message = f"Turbidity {v:.1f} NTU — within safe limit ({TURBIDITY_LIMIT} NTU)."
        elif v <= TURBIDITY_LIMIT:
            status  = "WARNING"
            message = (
                f"Turbidity {v:.1f} NTU approaching regulatory limit ({TURBIDITY_LIMIT} NTU). "
                "Check filtration system."
            )
        else:
            pct = round((v - TURBIDITY_LIMIT) / TURBIDITY_LIMIT * 100, 1)
            status  = "UNSAFE"
            message = (
                f"Turbidity {v:.1f} NTU exceeds regulatory limit ({TURBIDITY_LIMIT} NTU) "
                f"by {pct}%. Discharge must be halted pending treatment."
            )

        return {
            "status":    status,
            "parameter": "turbidity",
            "value":     v,
            "limit":     TURBIDITY_LIMIT,
            "message":   message,
        }

    def _analyze_chemical(self, value: Optional[float]) -> Dict[str, Any]:
        if value is None:
            return {"status": "SAFE", "parameter": "chemical_level", "value": None, "message": "Chemical level not measured."}

        v = float(value)
        if v <= CHEMICAL_WARN:
            status  = "SAFE"
            message = f"Chemical level {v:.1f} mg/L — within safe limit ({CHEMICAL_LIMIT} mg/L)."
        elif v <= CHEMICAL_LIMIT:
            status  = "WARNING"
            message = (
                f"Chemical level {v:.1f} mg/L approaching regulatory limit ({CHEMICAL_LIMIT} mg/L). "
                "Review treatment process."
            )
        else:
            pct = round((v - CHEMICAL_LIMIT) / CHEMICAL_LIMIT * 100, 1)
            status  = "UNSAFE"
            message = (
                f"Chemical level {v:.1f} mg/L exceeds limit ({CHEMICAL_LIMIT} mg/L) "
                f"by {pct}%. Potential contamination of receiving water body."
            )

        return {
            "status":    status,
            "parameter": "chemical_level",
            "value":     v,
            "limit":     CHEMICAL_LIMIT,
            "message":   message,
        }

    # ── discharge pattern detection ──────────────────────────────────────────

    def _detect_discharge_pattern(
        self,
        current: Dict[str, Any],
        history: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        if len(history) < 5:
            return {"anomalous": False, "description": "Insufficient history for pattern analysis."}

        anomalies = []
        for param in WATER_PARAMS:
            curr_val = current.get(param)
            if curr_val is None:
                continue
            hist_vals = [float(r[param]) for r in history if r.get(param) is not None]
            if len(hist_vals) < 5:
                continue
            mean = sum(hist_vals) / len(hist_vals)
            if mean < 1e-6:
                continue
            ratio = float(curr_val) / mean
            if ratio >= SPIKE_RATIO:
                anomalies.append(
                    f"{param.upper()} is {ratio:.1f}× the historical mean "
                    f"({curr_val:.2f} vs avg {mean:.2f}) — possible sudden discharge."
                )

        if anomalies:
            return {
                "anomalous":   True,
                "description": "Abnormal discharge pattern detected: " + "; ".join(anomalies),
                "details":     anomalies,
            }

        return {"anomalous": False, "description": "No abnormal discharge pattern detected."}

    # ── helpers ──────────────────────────────────────────────────────────────

    def _build_explanation(
        self,
        overall: str,
        issues: List[str],
        reading: Dict[str, Any],
    ) -> str:
        if overall == "SAFE":
            return (
                "All measured water quality parameters are within acceptable limits. "
                "Effluent discharge is compliant."
            )
        prefix = {
            "WARNING": "Water quality is degraded and requires attention.",
            "UNSAFE":  "Water quality is critically unsafe — immediate action required.",
        }.get(overall, "")

        issue_text = " ".join(issues)
        params_summary = ", ".join(
            f"{p}={reading[p]:.2f}" for p in WATER_PARAMS if reading.get(p) is not None
        )
        return f"{prefix} Issues: {issue_text} Readings: [{params_summary}]."


# ── Module-level singleton ───────────────────────────────────────────────────
effluent_agent = EffluentAgent()
