"""API route: /api/dashboard"""

from typing import Any, Dict, List

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from models.database import (
    Factory, Violation, Anomaly, Alert,
    Incident, SensorReading, RiskScore, get_db,
)
from models.schemas import DashboardSummaryOut

router = APIRouter()


@router.get("/summary", response_model=DashboardSummaryOut)
def dashboard_summary(db: Session = Depends(get_db)):
    total_factories      = db.query(Factory).count()
    active_violations    = db.query(Violation).filter(Violation.status == "active").count()
    critical_violations  = (
        db.query(Violation)
        .filter(Violation.severity == "CRITICAL", Violation.status == "active")
        .count()
    )
    open_anomalies       = db.query(Anomaly).filter(Anomaly.status == "open").count()
    pending_alerts       = db.query(Alert).filter(Alert.status == "pending").count()
    open_incidents       = (
        db.query(Incident)
        .filter(Incident.status.in_(["open", "investigating", "escalated"]))
        .count()
    )
    factories_at_risk    = (
        db.query(RiskScore)
        .filter(RiskScore.risk_level.in_(["HIGH", "CRITICAL"]))
        .count()
    )
    recent_readings_count = db.query(SensorReading).count()

    # Violations by severity
    sev_rows = (
        db.query(Violation.severity, func.count(Violation.id))
        .filter(Violation.status == "active")
        .group_by(Violation.severity)
        .all()
    )
    violations_by_severity = {row[0]: row[1] for row in sev_rows if row[0]}

    # Top violating factories (by active violation count)
    top_rows = (
        db.query(Violation.factory_id, func.count(Violation.id).label("cnt"))
        .filter(Violation.status == "active")
        .group_by(Violation.factory_id)
        .order_by(func.count(Violation.id).desc())
        .limit(5)
        .all()
    )
    top_violating_factories = [
        {"factory_id": r[0], "violation_count": r[1]} for r in top_rows
    ]

    # Risk distribution
    risk_rows = (
        db.query(RiskScore.risk_level, func.count(RiskScore.id))
        .group_by(RiskScore.risk_level)
        .all()
    )
    risk_distribution = {row[0]: row[1] for row in risk_rows if row[0]}

    return DashboardSummaryOut(
        total_factories=total_factories,
        active_violations=active_violations,
        critical_violations=critical_violations,
        open_anomalies=open_anomalies,
        pending_alerts=pending_alerts,
        open_incidents=open_incidents,
        factories_at_risk=factories_at_risk,
        recent_readings_count=recent_readings_count,
        violations_by_severity=violations_by_severity,
        top_violating_factories=top_violating_factories,
        risk_distribution=risk_distribution,
    )
