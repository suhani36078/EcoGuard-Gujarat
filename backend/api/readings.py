"""API route: /api/readings"""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from models.database import SensorReading, get_db
from models.schemas import SensorReadingOut

router = APIRouter()


@router.get("/{factory_id}", response_model=List[SensorReadingOut])
def get_readings(
    factory_id: str,
    limit: int = Query(default=100, le=1000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    return (
        db.query(SensorReading)
        .filter(SensorReading.factory_id == factory_id)
        .order_by(SensorReading.timestamp.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
