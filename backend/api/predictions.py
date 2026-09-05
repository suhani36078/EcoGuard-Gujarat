"""API route: /api/predictions — Pollution prediction and what-if analysis"""

from typing import List, Optional, Dict
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime, timedelta

from models.database import DistrictData, SensorReading, Violation, get_db

router = APIRouter()


class PredictionRequest(BaseModel):
    district: Optional[str] = None
    factory_id: Optional[str] = None
    days_ahead: Optional[int] = 7


class WhatIfRequest(BaseModel):
    district: Optional[str] = "Gujarat"
    traffic_reduction_pct: Optional[float] = 0
    industrial_reduction_pct: Optional[float] = 0
    waste_reduction_pct: Optional[float] = 0
    green_cover_increase_pct: Optional[float] = 0
    public_transport_adoption_pct: Optional[float] = 0


@router.post("/district")
def predict_district_pollution(req: PredictionRequest, db: Session = Depends(get_db)):
    """Predict pollution risk for a district over the coming period."""
    district = None
    if req.district:
        district = db.query(DistrictData).filter(
            DistrictData.district_name.ilike(f"%{req.district}%")
        ).first()

    base_score = district.overall_score if district else 56.4
    base_trend = district.trend if district else "stable"

    trend_factor = {"increasing": 0.05, "stable": 0.0, "decreasing": -0.03}.get(base_trend, 0)
    predictions = []
    now = datetime.utcnow()
    for day in range(1, (req.days_ahead or 7) + 1):
        # Simple trend-based extrapolation with seasonal noise
        import random
        random.seed(day + 42)
        noise = random.uniform(-2, 2)
        predicted = base_score + (trend_factor * base_score * day) + noise
        predicted = max(0, min(100, predicted))
        predictions.append({
            "date": (now + timedelta(days=day)).strftime("%Y-%m-%d"),
            "predicted_score": round(predicted, 1),
            "risk_level": _score_to_risk(predicted),
            "confidence": max(0.4, 0.85 - (day * 0.05)),
        })

    return {
        "district": district.district_name if district else req.district or "Gujarat",
        "base_score": base_score,
        "current_trend": base_trend,
        "predictions": predictions,
        "model": "LinearTrend + SeasonalAdjustment (DEMO)",
        "data_note": "Predictions are model-based estimates using available sensor trends. Not official forecasts.",
        "confidence_note": "Confidence decreases for longer horizons. Replace with ML model for production use.",
    }


@router.get("/hotspot-risk")
def predict_hotspot_formation(db: Session = Depends(get_db)):
    """Identify districts at risk of new hotspot formation."""
    districts = db.query(DistrictData).filter(
        DistrictData.trend == "increasing"
    ).order_by(DistrictData.overall_score.desc()).limit(5).all()

    at_risk = []
    for d in districts:
        risk_probability = min(0.95, (d.overall_score / 100) * 1.3)
        at_risk.append({
            "district": d.district_name,
            "current_score": d.overall_score,
            "hotspot_probability": round(risk_probability, 2),
            "primary_threat": d.main_pollutant or "industrial",
            "risk_level": d.risk_level,
        })

    return {
        "at_risk_districts": at_risk,
        "analysis_basis": "Increasing pollution trend with high baseline score",
        "data_note": "DEMO/MODEL-BASED — not official risk assessment",
    }


@router.post("/what-if")
def what_if_analysis(req: WhatIfRequest, db: Session = Depends(get_db)):
    """Estimate pollution change under hypothetical interventions."""

    # Fetch base score
    if req.district and req.district != "Gujarat":
        d = db.query(DistrictData).filter(
            DistrictData.district_name.ilike(f"%{req.district}%")
        ).first()
        base_score = d.overall_score if d else 56.4
        base_air = d.air_score if d else 62.0
        base_water = d.water_score if d else 58.0
        base_industrial = d.industrial_score if d else 71.0
        base_waste = d.waste_score if d else 44.0
        base_noise = d.noise_score if d else 48.0
    else:
        base_score = 56.4
        base_air = 62.0
        base_water = 58.0
        base_industrial = 71.0
        base_waste = 44.0
        base_noise = 48.0

    # Impact coefficients (how each intervention reduces specific pollution types)
    traffic_impact = (req.traffic_reduction_pct or 0) / 100
    industrial_impact = (req.industrial_reduction_pct or 0) / 100
    waste_impact = (req.waste_reduction_pct or 0) / 100
    green_impact = (req.green_cover_increase_pct or 0) / 100
    transport_impact = (req.public_transport_adoption_pct or 0) / 100

    new_air = base_air * (1 - traffic_impact * 0.35 - industrial_impact * 0.20 - green_impact * 0.15 - transport_impact * 0.20)
    new_water = base_water * (1 - industrial_impact * 0.40 - waste_impact * 0.30)
    new_noise = base_noise * (1 - traffic_impact * 0.50 - transport_impact * 0.30)
    new_industrial = base_industrial * (1 - industrial_impact * 0.60)
    new_waste = base_waste * (1 - waste_impact * 0.60 - green_impact * 0.20)

    new_air = max(5, new_air)
    new_water = max(5, new_water)
    new_noise = max(5, new_noise)
    new_industrial = max(5, new_industrial)
    new_waste = max(5, new_waste)

    new_overall = new_air * 0.35 + new_water * 0.25 + new_industrial * 0.20 + new_waste * 0.10 + new_noise * 0.10
    reduction = base_score - new_overall
    reduction_pct = (reduction / base_score) * 100 if base_score > 0 else 0

    factors = []
    if req.traffic_reduction_pct:
        factors.append(f"Traffic reduction ({req.traffic_reduction_pct:.0f}%): reduces air & noise pollution")
    if req.industrial_reduction_pct:
        factors.append(f"Industrial reduction ({req.industrial_reduction_pct:.0f}%): major impact on air & water")
    if req.waste_reduction_pct:
        factors.append(f"Waste reduction ({req.waste_reduction_pct:.0f}%): improves waste & water scores")
    if req.green_cover_increase_pct:
        factors.append(f"Green cover (+{req.green_cover_increase_pct:.0f}%): natural air filtration, dust absorption")
    if req.public_transport_adoption_pct:
        factors.append(f"Public transport ({req.public_transport_adoption_pct:.0f}%): reduces vehicular emissions")

    return {
        "district": req.district or "Gujarat",
        "baseline": {
            "overall_score": round(base_score, 1),
            "air_score": round(base_air, 1),
            "water_score": round(base_water, 1),
            "noise_score": round(base_noise, 1),
            "industrial_score": round(base_industrial, 1),
            "waste_score": round(base_waste, 1),
            "risk_level": _score_to_risk(base_score),
        },
        "projected": {
            "overall_score": round(new_overall, 1),
            "air_score": round(new_air, 1),
            "water_score": round(new_water, 1),
            "noise_score": round(new_noise, 1),
            "industrial_score": round(new_industrial, 1),
            "waste_score": round(new_waste, 1),
            "risk_level": _score_to_risk(new_overall),
        },
        "reduction": round(reduction, 1),
        "reduction_percent": round(reduction_pct, 1),
        "intervention_factors": factors,
        "disclaimer": "SIMULATION ONLY — This is a simplified model-based estimate. Actual results depend on implementation, enforcement, and environmental conditions. Not a guarantee or official policy recommendation.",
        "model": "Linear Intervention Impact Model (DEMO)",
    }


def _score_to_risk(score: float) -> str:
    if score <= 30: return "LOW"
    if score <= 50: return "MODERATE"
    if score <= 65: return "HIGH"
    return "CRITICAL"
