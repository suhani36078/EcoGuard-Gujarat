"""API route: /api/anomalies"""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from models.database import Anomaly, get_db
from models.schemas import AnomalyOut

router = APIRouter()


@router.get("", response_model=List[AnomalyOut])
def list_anomalies(
    status: Optional[str] = Query(default=None),
    limit: int = Query(default=200, le=1000),
    db: Session = Depends(get_db),
):
    q = db.query(Anomaly)
    if status:
        q = q.filter(Anomaly.status == status.lower())
    return q.order_by(Anomaly.detected_at.desc()).limit(limit).all()
