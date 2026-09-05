"""API route: /api/forecasts"""

from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from models.database import Forecast, get_db
from models.schemas import ForecastOut

router = APIRouter()


@router.get("/{factory_id}", response_model=List[ForecastOut])
def get_factory_forecasts(
    factory_id: str,
    limit: int = Query(default=48, le=200),
    db: Session = Depends(get_db),
):
    return (
        db.query(Forecast)
        .filter(Forecast.factory_id == factory_id)
        .order_by(Forecast.forecast_time)
        .limit(limit)
        .all()
    )
