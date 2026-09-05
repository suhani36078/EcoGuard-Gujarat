"""
PRITHVI-X — Gujarat Pollution Intelligence & Action Platform
FastAPI entry point
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from models.database import Base, engine
from api import (
    auth, factories, readings, violations, anomalies,
    alerts, incidents, forecasts, risk_scores, dashboard,
    agents, community_risk, districts, hotspots,
    citizen_reports, pollution_index, predictions, chat,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create tables on startup if they don't exist."""
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Pollution Intelligence Platform",
    description="AI-Powered Industrial Pollution Monitoring for Gujarat",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth.router,          prefix="/api/auth",           tags=["Auth"])
app.include_router(factories.router,     prefix="/api/factories",      tags=["Factories"])
app.include_router(readings.router,      prefix="/api/readings",       tags=["Readings"])
app.include_router(violations.router,    prefix="/api/violations",     tags=["Violations"])
app.include_router(anomalies.router,     prefix="/api/anomalies",      tags=["Anomalies"])
app.include_router(alerts.router,        prefix="/api/alerts",         tags=["Alerts"])
app.include_router(incidents.router,     prefix="/api/incidents",      tags=["Incidents"])
app.include_router(forecasts.router,     prefix="/api/forecasts",      tags=["Forecasts"])
app.include_router(risk_scores.router,   prefix="/api/risk-scores",    tags=["Risk Scores"])
app.include_router(dashboard.router,     prefix="/api/dashboard",      tags=["Dashboard"])
app.include_router(agents.router,        prefix="/api/agents",         tags=["Agents"])
app.include_router(community_risk.router,  prefix="/api/community-risk",   tags=["Community Risk"])
app.include_router(districts.router,       prefix="/api/districts",         tags=["Districts"])
app.include_router(hotspots.router,        prefix="/api/hotspots",          tags=["Hotspots"])
app.include_router(citizen_reports.router, prefix="/api/citizen-reports",   tags=["Citizen Reports"])
app.include_router(pollution_index.router, prefix="/api/pollution-index",   tags=["Pollution Index"])
app.include_router(predictions.router,     prefix="/api/predictions",       tags=["Predictions"])
app.include_router(chat.router,            prefix="/api/chat",              tags=["Chat"])


@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "platform": "PRITHVI-X Gujarat Pollution Intelligence Platform v2.0"}


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy"}


@app.exception_handler(404)
async def not_found(request, exc):
    return JSONResponse(status_code=404, content={"detail": "Resource not found"})


@app.exception_handler(500)
async def server_error(request, exc):
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
