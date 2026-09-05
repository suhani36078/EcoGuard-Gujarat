"""
Agent Service
──────────────
Bridges the FastAPI backend to the supervisor agent pipeline.

Responsibilities:
  1. Accept a factory_id and latest SensorReading
  2. Enrich the agent context with recent history, violations, etc.
  3. Run the supervisor pipeline
  4. Persist results (anomalies, violations, forecasts, risk scores, alerts)
     back to the database
  5. Return the enriched context dict for the API response
"""

from __future__ import annotations

import logging
import sys
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

# Ensure project root is on the import path when running from the backend dir
_PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "..")
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class AgentService:
    """
    High-level service that wires sensor data → agent pipeline → database.
    """

    # ── public interface ─────────────────────────────────────────────────────

    def run_pipeline(
        self,
        db: Session,
        factory_id: str,
        reading: Any,  # SensorReading ORM instance or dict
        parameter: Optional[str] = None,
        value: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Run the full agent pipeline for a new sensor reading and persist results.

        Parameters
        ----------
        db         : SQLAlchemy session
        factory_id : str
        reading    : SensorReading ORM object or plain dict
        parameter  : the parameter being assessed (e.g. "pm25"); if None, the
                     highest currently violating parameter is auto-selected
        value      : corresponding float value; derived from reading if None

        Returns
        -------
        Enriched context dict including all agent outputs.
        """
        context = self._build_context(db, factory_id, reading, parameter, value)

        # Run supervisor pipeline
        try:
            from agents.supervisor.agent import supervisor_agent
            context = supervisor_agent.process(context)
        except Exception as exc:
            logger.error("[AgentService] Supervisor pipeline failed: %s", exc, exc_info=True)
            context["pipeline_error"] = str(exc)
            return context

        # Persist results
        self._save_results(db, factory_id, context)

        return context

    def run_pipeline_for_reading_dict(
        self,
        db: Session,
        reading_dict: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Convenience method: accepts a plain reading dict (as posted to the API)
        and runs the pipeline, auto-selecting the worst parameter.
        """
        factory_id = reading_dict.get("factory_id", "UNKNOWN")
        parameter, value = self._worst_parameter(reading_dict)
        return self.run_pipeline(db, factory_id, reading_dict, parameter, value)

    # ── context builder ──────────────────────────────────────────────────────

    def _build_context(
        self,
        db: Session,
        factory_id: str,
        reading: Any,
        parameter: Optional[str],
        value: Optional[float],
    ) -> Dict[str, Any]:
        # Convert ORM → dict if needed
        if hasattr(reading, "__table__"):
            reading_dict = self._orm_to_dict(reading)
        else:
            reading_dict = dict(reading)

        # Auto-select worst parameter if not specified
        if parameter is None or value is None:
            parameter, value = self._worst_parameter(reading_dict)

        context: Dict[str, Any] = {
            **reading_dict,
            "factory_id": factory_id,
            "parameter":  parameter,
            "value":      value,
        }

        # Attach recent history (last 48 h, max 200 readings)
        try:
            context["history"]    = self._get_history(db, factory_id)
            context["violations"] = self._get_recent_violations(db, factory_id)
            context["similar_incidents"] = []  # future: fetch from incidents table
        except Exception as exc:
            logger.warning("[AgentService] Could not load context data: %s", exc)
            context.setdefault("history", [])
            context.setdefault("violations", [])
            context.setdefault("similar_incidents", [])

        return context

    # ── result persistence ───────────────────────────────────────────────────

    def _save_results(
        self,
        db: Session,
        factory_id: str,
        context: Dict[str, Any],
    ) -> None:
        """Persist agent outputs to the database.  Errors are logged, not raised."""
        try:
            self._save_violation(db, factory_id, context)
            self._save_anomaly(db, factory_id, context)
            self._save_forecast(db, factory_id, context)
            self._save_risk_score(db, factory_id, context)
            self._save_alert(db, factory_id, context)
            db.commit()
        except Exception as exc:
            logger.error("[AgentService] Failed to persist results: %s", exc, exc_info=True)
            try:
                db.rollback()
            except Exception:
                pass

    def _save_violation(self, db: Session, factory_id: str, context: Dict[str, Any]) -> None:
        from models.database import Violation
        if context.get("violation_status") != "VIOLATION":
            return
        v = Violation(
            factory_id         = factory_id,
            parameter          = context.get("parameter", "unknown"),
            value              = float(context.get("value") or 0),
            limit_value        = float(context.get("limit_value") or 0),
            exceedance_percent = float(context.get("exceedance_percent") or 0),
            severity           = context.get("violation_severity"),
            status             = "active",
            detected_at        = datetime.utcnow(),
        )
        db.add(v)
        logger.debug("[AgentService] Saved violation for %s/%s", factory_id, context.get("parameter"))

    def _save_anomaly(self, db: Session, factory_id: str, context: Dict[str, Any]) -> None:
        from models.database import Anomaly
        score = context.get("anomaly_score")
        if score is None or score < 40:
            return
        a = Anomaly(
            factory_id    = factory_id,
            parameter     = context.get("parameter"),
            anomaly_score = float(score),
            detected_at   = datetime.utcnow(),
            description   = context.get("anomaly_reason", ""),
            status        = "open" if score >= 60 else "reviewed",
        )
        db.add(a)
        logger.debug("[AgentService] Saved anomaly score=%.1f for %s", score, factory_id)

    def _save_forecast(self, db: Session, factory_id: str, context: Dict[str, Any]) -> None:
        from models.database import Forecast
        forecast = context.get("forecast")
        if not forecast or forecast.get("model_used") == "none":
            return

        now = datetime.utcnow()
        from datetime import timedelta
        for horizon_h, key in [(1, "predicted_1h"), (2, "predicted_2h"), (4, "predicted_4h")]:
            val = forecast.get(key)
            if val is None:
                continue
            f = Forecast(
                factory_id      = factory_id,
                parameter       = forecast.get("parameter", context.get("parameter")),
                predicted_value = float(val),
                forecast_time   = now + timedelta(hours=horizon_h),
                confidence      = float(forecast.get("confidence") or 0),
                model_used      = forecast.get("model_used", "LinearRegression"),
            )
            db.add(f)
        logger.debug("[AgentService] Saved forecasts for %s", factory_id)

    def _save_risk_score(self, db: Session, factory_id: str, context: Dict[str, Any]) -> None:
        from models.database import RiskScore
        score = context.get("risk_score")
        if score is None:
            return
        r = RiskScore(
            factory_id    = factory_id,
            overall_score = float(score),
            risk_level    = context.get("risk_level", "LOW"),
            components    = context.get("risk_breakdown"),
            calculated_at = datetime.utcnow(),
        )
        db.add(r)
        logger.debug("[AgentService] Saved risk score=%.1f for %s", score, factory_id)

    def _save_alert(self, db: Session, factory_id: str, context: Dict[str, Any]) -> None:
        from models.database import Alert
        alert_result = context.get("alert_result")
        if not alert_result or alert_result.get("is_duplicate"):
            return
        if not context.get("alert_generated"):
            return
        a = Alert(
            factory_id  = factory_id,
            severity    = alert_result.get("severity", "LOW"),
            message     = alert_result.get("message", ""),
            recipients  = ", ".join(alert_result.get("recipients", [])),
            status      = "pending",
            created_at  = datetime.utcnow(),
        )
        db.add(a)
        logger.debug(
            "[AgentService] Saved alert sev=%s for %s",
            alert_result.get("severity"), factory_id,
        )

    # ── data helpers ─────────────────────────────────────────────────────────

    @staticmethod
    def _get_history(
        db: Session,
        factory_id: str,
        hours: int = 48,
        limit: int = 200,
    ) -> List[Dict[str, Any]]:
        from datetime import timedelta
        from models.database import SensorReading

        since = datetime.utcnow() - timedelta(hours=hours)
        rows = (
            db.query(SensorReading)
            .filter(
                SensorReading.factory_id == factory_id,
                SensorReading.timestamp  >= since,
            )
            .order_by(SensorReading.timestamp.asc())
            .limit(limit)
            .all()
        )
        return [AgentService._orm_to_dict(r) for r in rows]

    @staticmethod
    def _get_recent_violations(
        db: Session,
        factory_id: str,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        from models.database import Violation

        rows = (
            db.query(Violation)
            .filter(Violation.factory_id == factory_id)
            .order_by(Violation.detected_at.desc())
            .limit(limit)
            .all()
        )
        return [AgentService._orm_to_dict(r) for r in rows]

    # ── utility ──────────────────────────────────────────────────────────────

    @staticmethod
    def _orm_to_dict(obj: Any) -> Dict[str, Any]:
        """Convert an SQLAlchemy ORM instance to a plain dict."""
        if isinstance(obj, dict):
            return obj
        result = {}
        for col in obj.__table__.columns:
            val = getattr(obj, col.name, None)
            if isinstance(val, datetime):
                val = val.isoformat()
            result[col.name] = val
        return result

    @staticmethod
    def _worst_parameter(reading: Dict[str, Any]) -> tuple:
        """
        Return (parameter_name, value) for the parameter with the highest
        exceedance ratio relative to known limits.  Falls back to pm25.
        """
        LIMITS = {
            "pm25": 60, "pm10": 100, "so2": 80, "no2": 80, "co": 10,
            "turbidity": 10, "chemical_level": 50,
        }
        worst_param = "pm25"
        worst_ratio = 0.0

        for param, limit in LIMITS.items():
            val = reading.get(param)
            if val is not None:
                try:
                    ratio = float(val) / limit
                    if ratio > worst_ratio:
                        worst_ratio = ratio
                        worst_param = param
                except (TypeError, ValueError):
                    pass

        value = reading.get(worst_param)
        return worst_param, float(value) if value is not None else 0.0


# ── Module-level singleton ───────────────────────────────────────────────────
agent_service = AgentService()
