"""API route: /api/violations"""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from models.database import Violation, get_db
from models.schemas import ViolationOut

router = APIRouter()


@router.get("", response_model=List[ViolationOut])
def list_violations(
    severity: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    limit: int = Query(default=200, le=2000),
    db: Session = Depends(get_db),
):
    q = db.query(Violation)
    if severity:
        q = q.filter(Violation.severity == severity.upper())
    if status:
        q = q.filter(Violation.status == status.lower())
    return q.order_by(Violation.detected_at.desc()).limit(limit).all()


@router.get("/{factory_id}", response_model=List[ViolationOut])
def get_factory_violations(
    factory_id: str,
    limit: int = Query(default=100, le=500),
    db: Session = Depends(get_db),
):
    return (
        db.query(Violation)
        .filter(Violation.factory_id == factory_id)
        .order_by(Violation.detected_at.desc())
        .limit(limit)
        .all()
    )
