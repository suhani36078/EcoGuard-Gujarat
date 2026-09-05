"""
Pydantic v2 schemas for request / response validation.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict


# ─────────────────────────────────────────────
# Shared config
# ─────────────────────────────────────────────

class OrmBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ─────────────────────────────────────────────
# Factory
# ─────────────────────────────────────────────

class FactoryOut(OrmBase):
    id: str
    name: str
    location: str
    latitude: float
    longitude: float
    type: Optional[str] = None
    status: Optional[str] = None
    created_at: Optional[datetime] = None


# ─────────────────────────────────────────────
# Sensor Reading
# ─────────────────────────────────────────────

class SensorReadingOut(OrmBase):
    id: int
    factory_id: str
    timestamp: datetime
    pm25: Optional[float] = None
    pm10: Optional[float] = None
    so2: Optional[float] = None
    no2: Optional[float] = None
    co: Optional[float] = None
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    wind_speed: Optional[float] = None
    wind_direction: Optional[float] = None
    ph: Optional[float] = None
    turbidity: Optional[float] = None
    chemical_level: Optional[float] = None
    production_activity: Optional[float] = None


# ─────────────────────────────────────────────
# Pollution Limit
# ─────────────────────────────────────────────

class PollutionLimitOut(OrmBase):
    id: int
    parameter: str
    configured_limit: float
    unit: Optional[str] = None
    severity_low: Optional[float] = None
    severity_medium: Optional[float] = None
    severity_high: Optional[float] = None
    severity_critical: Optional[float] = None


class PollutionLimitUpdate(BaseModel):
    configured_limit: Optional[float] = None
    unit: Optional[str] = None
    severity_low: Optional[float] = None
    severity_medium: Optional[float] = None
    severity_high: Optional[float] = None
    severity_critical: Optional[float] = None


# ─────────────────────────────────────────────
# Violation
# ─────────────────────────────────────────────

class ViolationOut(OrmBase):
    id: int
    factory_id: str
    parameter: str
    value: float
    limit_value: float
    exceedance_percent: Optional[float] = None
    severity: Optional[str] = None
    status: Optional[str] = None
    detected_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None


# ─────────────────────────────────────────────
# Anomaly
# ─────────────────────────────────────────────

class AnomalyOut(OrmBase):
    id: int
    factory_id: str
    parameter: Optional[str] = None
    anomaly_score: Optional[float] = None
    detected_at: Optional[datetime] = None
    description: Optional[str] = None
    status: Optional[str] = None


# ─────────────────────────────────────────────
# Forecast
# ─────────────────────────────────────────────

class ForecastOut(OrmBase):
    id: int
    factory_id: str
    parameter: Optional[str] = None
    predicted_value: Optional[float] = None
    forecast_time: Optional[datetime] = None
    confidence: Optional[float] = None
    model_used: Optional[str] = None


# ─────────────────────────────────────────────
# Risk Score
# ─────────────────────────────────────────────

class RiskScoreOut(OrmBase):
    id: int
    factory_id: str
    overall_score: Optional[float] = None
    risk_level: Optional[str] = None
    components: Optional[Dict[str, Any]] = None
    calculated_at: Optional[datetime] = None


# ─────────────────────────────────────────────
# Alert
# ─────────────────────────────────────────────

class AlertOut(OrmBase):
    id: int
    factory_id: str
    violation_id: Optional[int] = None
    severity: Optional[str] = None
    message: Optional[str] = None
    recipients: Optional[str] = None
    status: Optional[str] = None
    created_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None


# ─────────────────────────────────────────────
# Incident
# ─────────────────────────────────────────────

class IncidentOut(OrmBase):
    id: int
    factory_id: str
    title: str
    description: Optional[str] = None
    status: Optional[str] = None
    severity: Optional[str] = None
    created_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    assigned_to: Optional[str] = None


class IncidentActionIn(BaseModel):
    action: str          # e.g. "assign", "resolve", "escalate", "add_note"
    performed_by: str
    note: Optional[str] = None
    assigned_to: Optional[str] = None


# ─────────────────────────────────────────────
# Agent Log
# ─────────────────────────────────────────────

class AgentLogOut(OrmBase):
    id: int
    agent_name: str
    action: Optional[str] = None
    input_summary: Optional[str] = None
    output_summary: Optional[str] = None
    timestamp: Optional[datetime] = None


# ─────────────────────────────────────────────
# Auth
# ─────────────────────────────────────────────

class LoginIn(BaseModel):
    username: str
    password: str


class RegisterIn(BaseModel):
    username: str
    password: str
    email: str
    role: Optional[str] = "viewer"


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    username: str


# ─────────────────────────────────────────────
# Agent pipeline
# ─────────────────────────────────────────────

class AgentProcessIn(BaseModel):
    event_id: Optional[str] = None
    factory_id: str
    timestamp: Optional[str] = None
    parameter: Optional[str] = None
    value: Optional[float] = None
    configured_limit: Optional[float] = None
    location: Optional[str] = None
    severity: Optional[str] = None


class AgentContextOut(BaseModel):
    event_id: Optional[str] = None
    factory_id: str
    timestamp: Optional[str] = None
    parameter: Optional[str] = None
    value: Optional[float] = None
    configured_limit: Optional[float] = None
    location: Optional[str] = None
    severity: Optional[str] = None
    current_status: Optional[str] = None
    anomaly_score: Optional[float] = None
    violation_status: Optional[str] = None
    predicted_value: Optional[float] = None
    risk_score: Optional[float] = None
    community_risk: Optional[str] = None
    evidence: Optional[Dict[str, Any]] = None
    combined_assessment: Optional[str] = None
    alert_level: Optional[str] = None


# ─────────────────────────────────────────────
# Dashboard summary
# ─────────────────────────────────────────────

class DashboardSummaryOut(BaseModel):
    total_factories: int
    active_violations: int
    critical_violations: int
    open_anomalies: int
    pending_alerts: int
    open_incidents: int
    factories_at_risk: int
    recent_readings_count: int
    violations_by_severity: Dict[str, int]
    top_violating_factories: List[Dict[str, Any]]
    risk_distribution: Dict[str, int]


# ─────────────────────────────────────────────
# Community Risk
# ─────────────────────────────────────────────

class CommunityRiskOut(BaseModel):
    factory_id: str
    factory_name: str
    location: str
    risk_level: str
    overall_score: float
    wind_direction: Optional[float] = None
    wind_speed: Optional[float] = None
    nearby_population: Optional[str] = None
    health_advisory: Optional[str] = None
    affected_area_km: Optional[float] = None
