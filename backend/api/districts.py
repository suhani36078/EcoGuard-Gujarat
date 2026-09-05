"""API route: /api/districts — Gujarat district pollution data"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from models.database import DistrictData, get_db

router = APIRouter()


class DistrictOut(BaseModel):
    id: int
    district_name: str
    district_code: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    air_score: Optional[float] = None
    water_score: Optional[float] = None
    noise_score: Optional[float] = None
    industrial_score: Optional[float] = None
    waste_score: Optional[float] = None
    overall_score: Optional[float] = None
    risk_level: Optional[str] = None
    main_pollutant: Optional[str] = None
    main_source: Optional[str] = None
    trend: Optional[str] = None
    monitored_locations: Optional[int] = None
    high_risk_zones: Optional[int] = None
    active_alerts: Optional[int] = None
    population: Optional[int] = None
    area_sq_km: Optional[float] = None
    last_updated: Optional[datetime] = None
    data_source: Optional[str] = None
    data_confidence: Optional[float] = None

    class Config:
        from_attributes = True


@router.get("", response_model=List[DistrictOut])
def get_all_districts(
    risk_level: Optional[str] = Query(None),
    pollution_type: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    q = db.query(DistrictData)
    if risk_level:
        q = q.filter(DistrictData.risk_level == risk_level.upper())
    districts = q.order_by(DistrictData.overall_score.desc()).all()
    return districts


@router.get("/{code}", response_model=DistrictOut)
def get_district(code: str, db: Session = Depends(get_db)):
    from fastapi import HTTPException
    d = db.query(DistrictData).filter(DistrictData.district_code == code.upper()).first()
    if not d:
        raise HTTPException(status_code=404, detail="District not found")
    return d


@router.get("/summary/state")
def get_state_summary(db: Session = Depends(get_db)):
    """Return aggregate state-level pollution summary."""
    districts = db.query(DistrictData).all()
    if not districts:
        return {"message": "No district data available"}

    n = len(districts)
    avg_overall = sum(d.overall_score or 0 for d in districts) / n
    avg_air = sum(d.air_score or 0 for d in districts) / n
    avg_water = sum(d.water_score or 0 for d in districts) / n
    avg_noise = sum(d.noise_score or 0 for d in districts) / n
    avg_industrial = sum(d.industrial_score or 0 for d in districts) / n
    avg_waste = sum(d.waste_score or 0 for d in districts) / n
    high_risk = [d for d in districts if d.risk_level in ("HIGH", "CRITICAL")]
    total_alerts = sum(d.active_alerts or 0 for d in districts)
    total_monitored = sum(d.monitored_locations or 0 for d in districts)
    total_high_risk_zones = sum(d.high_risk_zones or 0 for d in districts)

    worst = max(districts, key=lambda d: d.overall_score or 0)

    def score_to_category(s: float) -> str:
        if s <= 30: return "GOOD"
        if s <= 50: return "MODERATE"
        if s <= 65: return "POOR"
        if s <= 80: return "VERY POOR"
        return "SEVERE"

    return {
        "overall_score": round(avg_overall, 1),
        "risk_category": score_to_category(avg_overall),
        "air_score": round(avg_air, 1),
        "water_score": round(avg_water, 1),
        "noise_score": round(avg_noise, 1),
        "industrial_score": round(avg_industrial, 1),
        "waste_score": round(avg_waste, 1),
        "total_districts": n,
        "high_risk_districts": len(high_risk),
        "monitored_locations": total_monitored,
        "high_risk_zones": total_high_risk_zones,
        "active_alerts": total_alerts,
        "most_affected_district": worst.district_name,
        "most_affected_score": worst.overall_score,
        "data_source": "DEMO/SIMULATED",
        "data_note": "Values are estimated from available industrial and sensor data. Not official government measurements.",
    }
