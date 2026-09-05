"""API route: /api/community-risk"""

from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from models.database import RiskScore, Factory, SensorReading, get_db
from models.schemas import CommunityRiskOut

router = APIRouter()

HEALTH_ADVISORIES = {
    "CRITICAL": (
        "Immediate evacuation advisory issued for 2 km radius. "
        "Schools and hospitals notified. Emergency services on standby."
    ),
    "HIGH": (
        "Stay indoors advisory. Sensitive groups (elderly, children, asthmatic) "
        "should avoid outdoor exposure."
    ),
    "MEDIUM": (
        "Caution advised. Limit prolonged outdoor activities. "
        "Monitor air quality updates."
    ),
    "LOW": "Air quality acceptable. No special precautions required.",
}

POPULATION_ESTIMATES = {
    "Vapi":        "~250,000 residents within 5 km radius",
    "Ankleshwar":  "~180,000 residents within 5 km radius",
    "Vatva":       "~320,000 residents within 5 km radius",
}


@router.get("", response_model=List[CommunityRiskOut])
def get_community_risk(db: Session = Depends(get_db)):
    risks = []
    factories = db.query(Factory).all()

    for factory in factories:
        risk = (
            db.query(RiskScore)
            .filter(RiskScore.factory_id == factory.id)
            .order_by(RiskScore.calculated_at.desc())
            .first()
        )
        if not risk:
            continue

        # Get latest wind data
        latest = (
            db.query(SensorReading)
            .filter(SensorReading.factory_id == factory.id)
            .order_by(SensorReading.timestamp.desc())
            .first()
        )

        level = risk.risk_level or "LOW"
        score = risk.overall_score or 0.0

        # Affected radius (rough estimate: higher risk = larger radius)
        affected_km = round(0.5 + score / 100 * 4.5, 1)

        risks.append(CommunityRiskOut(
            factory_id=factory.id,
            factory_name=factory.name,
            location=factory.location,
            risk_level=level,
            overall_score=score,
            wind_direction=latest.wind_direction if latest else None,
            wind_speed=latest.wind_speed if latest else None,
            nearby_population=POPULATION_ESTIMATES.get(factory.location),
            health_advisory=HEALTH_ADVISORIES.get(level, HEALTH_ADVISORIES["LOW"]),
            affected_area_km=affected_km,
        ))

    return sorted(risks, key=lambda r: r.overall_score, reverse=True)
