"""
Data service — higher-level query helpers used by API routes.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from models.database import (
    Factory, SensorReading, Violation, Anomaly, RiskScore, Alert,
)


class DataService:

    # ── Factories ────────────────────────────────────────────────────────────

    @staticmethod
    def get_factory(db: Session, factory_id: str) -> Optional[Factory]:
        return db.query(Factory).filter(Factory.id == factory_id).first()

    @staticmethod
    def get_all_factories(db: Session) -> List[Factory]:
        return db.query(Factory).all()

    # ── Readings ─────────────────────────────────────────────────────────────

    @staticmethod
    def get_recent_readings(
        db: Session,
        factory_id: str,
        hours: int = 24,
        limit: int = 200,
    ) -> List[SensorReading]:
        since = datetime.utcnow() - timedelta(hours=hours)
        return (
            db.query(SensorReading)
            .filter(
                SensorReading.factory_id == factory_id,
                SensorReading.timestamp >= since,
            )
            .order_by(SensorReading.timestamp.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_latest_reading(db: Session, factory_id: str) -> Optional[SensorReading]:
        return (
            db.query(SensorReading)
            .filter(SensorReading.factory_id == factory_id)
            .order_by(SensorReading.timestamp.desc())
            .first()
        )

    # ── Violations ───────────────────────────────────────────────────────────

    @staticmethod
    def get_active_violations(db: Session, factory_id: Optional[str] = None) -> List[Violation]:
        q = db.query(Violation).filter(Violation.status == "active")
        if factory_id:
            q = q.filter(Violation.factory_id == factory_id)
        return q.order_by(Violation.detected_at.desc()).all()

    @staticmethod
    def violation_count_last_n_days(
        db: Session,
        factory_id: str,
        days: int = 30,
    ) -> int:
        since = datetime.utcnow() - timedelta(days=days)
        return (
            db.query(Violation)
            .filter(
                Violation.factory_id == factory_id,
                Violation.detected_at >= since,
            )
            .count()
        )

    # ── Risk ─────────────────────────────────────────────────────────────────

    @staticmethod
    def get_latest_risk_score(db: Session, factory_id: str) -> Optional[RiskScore]:
        return (
            db.query(RiskScore)
            .filter(RiskScore.factory_id == factory_id)
            .order_by(RiskScore.calculated_at.desc())
            .first()
        )

    # ── Summary stats ────────────────────────────────────────────────────────

    @staticmethod
    def platform_summary(db: Session) -> Dict[str, Any]:
        total_factories  = db.query(Factory).count()
        active_viols     = db.query(Violation).filter(Violation.status == "active").count()
        critical_viols   = (
            db.query(Violation)
            .filter(Violation.status == "active", Violation.severity == "CRITICAL")
            .count()
        )
        open_anomalies   = db.query(Anomaly).filter(Anomaly.status == "open").count()
        pending_alerts   = db.query(Alert).filter(Alert.status == "pending").count()
        return {
            "total_factories":    total_factories,
            "active_violations":  active_viols,
            "critical_violations":critical_viols,
            "open_anomalies":     open_anomalies,
            "pending_alerts":     pending_alerts,
        }


data_service = DataService()
