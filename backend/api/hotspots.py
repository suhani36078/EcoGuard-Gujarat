"""API route: /api/hotspots — Pollution hotspot detection"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from models.database import Hotspot, get_db

router = APIRouter()


class HotspotOut(BaseModel):
    id: int
    name: str
    district: str
    latitude: float
    longitude: float
    pollution_type: str
    severity: str
    severity_score: Optional[float] = None
    trend: Optional[str] = None
    possible_source: Optional[str] = None
    explanation: Optional[str] = None
    affected_radius: Optional[float] = None
    population_affected: Optional[int] = None
    detected_at: Optional[datetime] = None
    last_updated: Optional[datetime] = None
    status: Optional[str] = None

    class Config:
        from_attributes = True


@router.get("", response_model=List[HotspotOut])
def get_hotspots(
    district: Optional[str] = Query(None),
    pollution_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    status: Optional[str] = Query("active"),
    db: Session = Depends(get_db),
):
    q = db.query(Hotspot)
    if district:
        q = q.filter(Hotspot.district.ilike(f"%{district}%"))
    if pollution_type:
        q = q.filter(Hotspot.pollution_type == pollution_type.lower())
    if severity:
        q = q.filter(Hotspot.severity == severity.upper())
    if status:
        q = q.filter(Hotspot.status == status)
    return q.order_by(Hotspot.severity_score.desc()).all()


@router.get("/summary")
def hotspot_summary(db: Session = Depends(get_db)):
    hotspots = db.query(Hotspot).filter(Hotspot.status == "active").all()
    by_type: dict = {}
    by_severity: dict = {}
    for h in hotspots:
        by_type[h.pollution_type] = by_type.get(h.pollution_type, 0) + 1
        by_severity[h.severity] = by_severity.get(h.severity, 0) + 1

    critical = [h for h in hotspots if h.severity == "CRITICAL"]
    return {
        "total_active": len(hotspots),
        "by_type": by_type,
        "by_severity": by_severity,
        "critical_count": len(critical),
        "critical_hotspots": [
            {"name": h.name, "district": h.district, "type": h.pollution_type}
            for h in critical[:5]
        ],
    }


@router.get("/{hotspot_id}", response_model=HotspotOut)
def get_hotspot(hotspot_id: int, db: Session = Depends(get_db)):
    from fastapi import HTTPException
    h = db.query(Hotspot).filter(Hotspot.id == hotspot_id).first()
    if not h:
        raise HTTPException(status_code=404, detail="Hotspot not found")
    return h
