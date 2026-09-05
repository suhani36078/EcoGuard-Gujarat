"""API route: /api/pollution-index — Gujarat Pollution Intelligence Score"""

from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from models.database import GujaratPollutionIndex, DistrictData, get_db

router = APIRouter()


class PollutionIndexOut(BaseModel):
    id: int
    recorded_at: Optional[datetime] = None
    overall_score: Optional[float] = None
    risk_category: Optional[str] = None
    air_score: Optional[float] = None
    water_score: Optional[float] = None
    noise_score: Optional[float] = None
    industrial_score: Optional[float] = None
    waste_score: Optional[float] = None
    major_pollutant_type: Optional[str] = None
    most_affected_district: Optional[str] = None
    change_from_previous: Optional[float] = None
    monitored_locations: Optional[int] = None
    high_risk_zones: Optional[int] = None
    active_alerts: Optional[int] = None
    health_interpretation: Optional[str] = None
    data_coverage_pct: Optional[float] = None
    data_source: Optional[str] = None

    class Config:
        from_attributes = True


@router.get("/current")
def get_current_index(db: Session = Depends(get_db)):
    """Returns the latest Gujarat Pollution Intelligence Score."""
    idx = (
        db.query(GujaratPollutionIndex)
        .order_by(GujaratPollutionIndex.recorded_at.desc())
        .first()
    )
    if not idx:
        # Compute from district data
        districts = db.query(DistrictData).all()
        if not districts:
            return _demo_index()
        n = len(districts)
        air = sum(d.air_score or 0 for d in districts) / n
        water = sum(d.water_score or 0 for d in districts) / n
        noise = sum(d.noise_score or 0 for d in districts) / n
        industrial = sum(d.industrial_score or 0 for d in districts) / n
        waste = sum(d.waste_score or 0 for d in districts) / n
        overall = (air * 0.35 + water * 0.25 + industrial * 0.20 + waste * 0.10 + noise * 0.10)
        worst = max(districts, key=lambda d: d.overall_score or 0)
        scores = {"air": air, "water": water, "noise": noise, "industrial": industrial, "waste": waste}
        major = max(scores, key=scores.get)
        return {
            "overall_score": round(overall, 1),
            "risk_category": _score_to_category(overall),
            "air_score": round(air, 1),
            "water_score": round(water, 1),
            "noise_score": round(noise, 1),
            "industrial_score": round(industrial, 1),
            "waste_score": round(waste, 1),
            "major_pollutant_type": major,
            "most_affected_district": worst.district_name,
            "change_from_previous": -2.3,
            "monitored_locations": sum(d.monitored_locations or 0 for d in districts),
            "high_risk_zones": sum(d.high_risk_zones or 0 for d in districts),
            "active_alerts": sum(d.active_alerts or 0 for d in districts),
            "health_interpretation": _health_interpretation(overall),
            "data_coverage_pct": 62.0,
            "data_source": "DEMO/SIMULATED",
            "data_note": "Estimated values based on available industrial and sensor data. Not official real-time government measurements.",
        }
    return idx


@router.get("/history")
def get_index_history(limit: int = 30, db: Session = Depends(get_db)):
    records = (
        db.query(GujaratPollutionIndex)
        .order_by(GujaratPollutionIndex.recorded_at.desc())
        .limit(limit)
        .all()
    )
    return records


def _score_to_category(score: float) -> str:
    if score <= 30: return "GOOD"
    if score <= 50: return "MODERATE"
    if score <= 65: return "POOR"
    if score <= 80: return "VERY POOR"
    return "SEVERE"


def _health_interpretation(score: float) -> str:
    if score <= 30:
        return "Air and environmental quality is satisfactory. Minimal health risk for all population groups."
    if score <= 50:
        return "Moderate pollution levels. Sensitive groups (children, elderly, respiratory patients) should limit prolonged outdoor exposure."
    if score <= 65:
        return "Unhealthy for sensitive groups. General public may experience discomfort. Avoid strenuous outdoor activities."
    if score <= 80:
        return "Unhealthy air and environmental conditions. Everyone may experience health effects. Limit outdoor exposure."
    return "Very unhealthy. Serious health effects expected. Avoid all outdoor activities. Authorities should issue public health advisory."


def _demo_index():
    return {
        "overall_score": 56.4,
        "risk_category": "POOR",
        "air_score": 62.1,
        "water_score": 58.3,
        "noise_score": 48.7,
        "industrial_score": 71.2,
        "waste_score": 44.5,
        "major_pollutant_type": "industrial",
        "most_affected_district": "Vapi-Ankleshwar Belt",
        "change_from_previous": 2.1,
        "monitored_locations": 47,
        "high_risk_zones": 8,
        "active_alerts": 12,
        "health_interpretation": "Moderate to poor conditions. Industrial zones show elevated pollution. Sensitive groups should take precautions.",
        "data_coverage_pct": 60.0,
        "data_source": "DEMO/SIMULATED",
        "data_note": "Estimated values based on available industrial and sensor data. Not official real-time government measurements.",
    }
