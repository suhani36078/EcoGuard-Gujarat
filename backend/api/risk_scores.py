"""API route: /api/risk-scores"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from models.database import RiskScore, Factory, get_db
from models.schemas import RiskScoreOut

router = APIRouter()


@router.get("", response_model=List[RiskScoreOut])
def list_risk_scores(db: Session = Depends(get_db)):
    return db.query(RiskScore).order_by(RiskScore.overall_score.desc()).all()


@router.get("/{factory_id}", response_model=RiskScoreOut)
def get_factory_risk(factory_id: str, db: Session = Depends(get_db)):
    score = (
        db.query(RiskScore)
        .filter(RiskScore.factory_id == factory_id)
        .order_by(RiskScore.calculated_at.desc())
        .first()
    )
    if not score:
        raise HTTPException(status_code=404, detail="Risk score not found for this factory")
    return score
