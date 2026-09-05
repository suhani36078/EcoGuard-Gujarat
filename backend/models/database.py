"""
SQLAlchemy ORM models for PRITHVI-X — Gujarat Pollution Intelligence Platform.
"""

import os
import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, Float, Integer, DateTime, Text, JSON,
    ForeignKey, create_engine,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./pollution_platform.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def new_uuid():
    return str(uuid.uuid4())


# ─────────────────────────────────────────────
# Factories
# ─────────────────────────────────────────────

class Factory(Base):
    __tablename__ = "factories"

    id         = Column(String, primary_key=True, default=new_uuid)
    name       = Column(String, nullable=False)
    location   = Column(String, nullable=False)
    latitude   = Column(Float, nullable=False)
    longitude  = Column(Float, nullable=False)
    type       = Column(String)
    status     = Column(String, default="active")
    created_at = Column(DateTime, default=datetime.utcnow)

    readings   = relationship("SensorReading", back_populates="factory", lazy="dynamic")
    violations = relationship("Violation",     back_populates="factory", lazy="dynamic")
    anomalies  = relationship("Anomaly",       back_populates="factory", lazy="dynamic")
    alerts     = relationship("Alert",         back_populates="factory", lazy="dynamic")
    incidents  = relationship("Incident",      back_populates="factory", lazy="dynamic")
    forecasts  = relationship("Forecast",      back_populates="factory", lazy="dynamic")
    risk_scores= relationship("RiskScore",     back_populates="factory", lazy="dynamic")


# ─────────────────────────────────────────────
# Sensor Readings
# ─────────────────────────────────────────────

class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id                  = Column(Integer, primary_key=True, autoincrement=True)
    factory_id          = Column(String, ForeignKey("factories.id"), nullable=False)
    timestamp           = Column(DateTime, nullable=False)
    pm25                = Column(Float)
    pm10                = Column(Float)
    so2                 = Column(Float)
    no2                 = Column(Float)
    co                  = Column(Float)
    temperature         = Column(Float)
    humidity            = Column(Float)
    wind_speed          = Column(Float)
    wind_direction      = Column(Float)
    ph                  = Column(Float)
    turbidity           = Column(Float)
    chemical_level      = Column(Float)
    production_activity = Column(Float, default=1.0)

    factory = relationship("Factory", back_populates="readings")


# ─────────────────────────────────────────────
# Pollution Limits
# ─────────────────────────────────────────────

class PollutionLimit(Base):
    __tablename__ = "pollution_limits"

    id                = Column(Integer, primary_key=True, autoincrement=True)
    parameter         = Column(String, unique=True, nullable=False)
    configured_limit  = Column(Float, nullable=False)
    unit              = Column(String)
    severity_low      = Column(Float)
    severity_medium   = Column(Float)
    severity_high     = Column(Float)
    severity_critical = Column(Float)


# ─────────────────────────────────────────────
# Violations
# ─────────────────────────────────────────────

class Violation(Base):
    __tablename__ = "violations"

    id                 = Column(Integer, primary_key=True, autoincrement=True)
    factory_id         = Column(String, ForeignKey("factories.id"), nullable=False)
    parameter          = Column(String, nullable=False)
    value              = Column(Float, nullable=False)
    limit_value        = Column(Float, nullable=False)
    exceedance_percent = Column(Float, default=0.0)
    severity           = Column(String)
    status             = Column(String, default="active")
    detected_at        = Column(DateTime, default=datetime.utcnow)
    resolved_at        = Column(DateTime, nullable=True)

    factory = relationship("Factory", back_populates="violations")


# ─────────────────────────────────────────────
# Anomalies
# ─────────────────────────────────────────────

class Anomaly(Base):
    __tablename__ = "anomalies"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    factory_id    = Column(String, ForeignKey("factories.id"), nullable=False)
    parameter     = Column(String)
    anomaly_score = Column(Float)
    detected_at   = Column(DateTime, default=datetime.utcnow)
    description   = Column(Text)
    status        = Column(String, default="open")

    factory = relationship("Factory", back_populates="anomalies")


# ─────────────────────────────────────────────
# Forecasts
# ─────────────────────────────────────────────

class Forecast(Base):
    __tablename__ = "forecasts"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    factory_id      = Column(String, ForeignKey("factories.id"), nullable=False)
    parameter       = Column(String)
    predicted_value = Column(Float)
    forecast_time   = Column(DateTime)
    confidence      = Column(Float)
    model_used      = Column(String)

    factory = relationship("Factory", back_populates="forecasts")


# ─────────────────────────────────────────────
# Risk Scores
# ─────────────────────────────────────────────

class RiskScore(Base):
    __tablename__ = "risk_scores"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    factory_id    = Column(String, ForeignKey("factories.id"), nullable=False)
    overall_score = Column(Float)
    risk_level    = Column(String)
    components    = Column(JSON)
    calculated_at = Column(DateTime, default=datetime.utcnow)

    factory = relationship("Factory", back_populates="risk_scores")


# ─────────────────────────────────────────────
# Alerts
# ─────────────────────────────────────────────

class Alert(Base):
    __tablename__ = "alerts"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    factory_id      = Column(String, ForeignKey("factories.id"), nullable=False)
    violation_id    = Column(Integer, ForeignKey("violations.id"), nullable=True)
    severity        = Column(String)
    message         = Column(Text)
    recipients      = Column(String)
    status          = Column(String, default="pending")
    created_at      = Column(DateTime, default=datetime.utcnow)
    acknowledged_at = Column(DateTime, nullable=True)
    resolved_at     = Column(DateTime, nullable=True)

    factory = relationship("Factory", back_populates="alerts")


# ─────────────────────────────────────────────
# Incidents
# ─────────────────────────────────────────────

class Incident(Base):
    __tablename__ = "incidents"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    factory_id  = Column(String, ForeignKey("factories.id"), nullable=False)
    title       = Column(String, nullable=False)
    description = Column(Text)
    status      = Column(String, default="open")
    severity    = Column(String)
    created_at  = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    assigned_to = Column(String)

    factory = relationship("Factory", back_populates="incidents")


# ─────────────────────────────────────────────
# Agent Logs
# ─────────────────────────────────────────────

class AgentLog(Base):
    __tablename__ = "agent_logs"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    agent_name     = Column(String, nullable=False)
    action         = Column(String)
    input_summary  = Column(Text)
    output_summary = Column(Text)
    timestamp      = Column(DateTime, default=datetime.utcnow)


# ─────────────────────────────────────────────
# Users
# ─────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    username      = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role          = Column(String, default="viewer")
    email         = Column(String, unique=True)
    created_at    = Column(DateTime, default=datetime.utcnow)


# ─────────────────────────────────────────────
# District Pollution Data
# ─────────────────────────────────────────────

class DistrictData(Base):
    __tablename__ = "district_data"

    id                   = Column(Integer, primary_key=True, autoincrement=True)
    district_name        = Column(String, nullable=False)
    district_code        = Column(String, unique=True, nullable=False)
    latitude             = Column(Float)
    longitude            = Column(Float)
    air_score            = Column(Float, default=0)
    water_score          = Column(Float, default=0)
    noise_score          = Column(Float, default=0)
    industrial_score     = Column(Float, default=0)
    waste_score          = Column(Float, default=0)
    overall_score        = Column(Float, default=0)
    risk_level           = Column(String, default="LOW")
    main_pollutant       = Column(String)
    main_source          = Column(String)
    trend                = Column(String, default="stable")   # increasing/decreasing/stable
    monitored_locations  = Column(Integer, default=0)
    high_risk_zones      = Column(Integer, default=0)
    active_alerts        = Column(Integer, default=0)
    population           = Column(Integer)
    area_sq_km           = Column(Float)
    last_updated         = Column(DateTime, default=datetime.utcnow)
    data_source          = Column(String, default="DEMO")
    data_confidence      = Column(Float, default=0.75)


# ─────────────────────────────────────────────
# Pollution Hotspots
# ─────────────────────────────────────────────

class Hotspot(Base):
    __tablename__ = "hotspots"

    id               = Column(Integer, primary_key=True, autoincrement=True)
    name             = Column(String, nullable=False)
    district         = Column(String, nullable=False)
    latitude         = Column(Float, nullable=False)
    longitude        = Column(Float, nullable=False)
    pollution_type   = Column(String, nullable=False)  # air/water/noise/industrial/waste
    severity         = Column(String, nullable=False)  # LOW/MODERATE/HIGH/CRITICAL
    severity_score   = Column(Float)
    trend            = Column(String, default="stable")
    possible_source  = Column(String)
    explanation      = Column(Text)
    affected_radius  = Column(Float)   # km
    population_affected = Column(Integer)
    detected_at      = Column(DateTime, default=datetime.utcnow)
    last_updated     = Column(DateTime, default=datetime.utcnow)
    status           = Column(String, default="active")


# ─────────────────────────────────────────────
# Citizen Reports
# ─────────────────────────────────────────────

class CitizenReport(Base):
    __tablename__ = "citizen_reports"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    reporter_id     = Column(Integer, ForeignKey("users.id"), nullable=True)
    category        = Column(String, nullable=False)   # garbage/smoke/water/noise/industrial/burning
    location        = Column(String, nullable=False)
    district        = Column(String)
    latitude        = Column(Float)
    longitude       = Column(Float)
    description     = Column(Text)
    severity        = Column(String, default="MODERATE")
    image_url       = Column(String)
    status          = Column(String, default="submitted")  # submitted/under_review/assigned/resolved
    assigned_to     = Column(String)
    submitted_at    = Column(DateTime, default=datetime.utcnow)
    updated_at      = Column(DateTime, default=datetime.utcnow)
    resolved_at     = Column(DateTime, nullable=True)
    resolution_note = Column(Text)
    upvotes         = Column(Integer, default=0)


# ─────────────────────────────────────────────
# Chat Messages
# ─────────────────────────────────────────────

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id           = Column(Integer, primary_key=True, autoincrement=True)
    session_id   = Column(String, nullable=False)
    role         = Column(String, nullable=False)   # user/assistant
    content      = Column(Text, nullable=False)
    agent_used   = Column(String)
    created_at   = Column(DateTime, default=datetime.utcnow)


# ─────────────────────────────────────────────
# Gujarat Pollution Index
# ─────────────────────────────────────────────

class GujaratPollutionIndex(Base):
    __tablename__ = "gujarat_pollution_index"

    id                    = Column(Integer, primary_key=True, autoincrement=True)
    recorded_at           = Column(DateTime, default=datetime.utcnow)
    overall_score         = Column(Float)
    risk_category         = Column(String)   # GOOD/MODERATE/POOR/VERY_POOR/SEVERE
    air_score             = Column(Float)
    water_score           = Column(Float)
    noise_score           = Column(Float)
    industrial_score      = Column(Float)
    waste_score           = Column(Float)
    major_pollutant_type  = Column(String)
    most_affected_district= Column(String)
    change_from_previous  = Column(Float)   # percentage
    monitored_locations   = Column(Integer, default=0)
    high_risk_zones       = Column(Integer, default=0)
    active_alerts         = Column(Integer, default=0)
    health_interpretation = Column(Text)
    data_coverage_pct     = Column(Float, default=60.0)
    data_source           = Column(String, default="DEMO/SIMULATED")


# ─────────────────────────────────────────────
# Dependency helper
# ─────────────────────────────────────────────

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
