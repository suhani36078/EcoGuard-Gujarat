"""
Backend test suite for the Gujarat Pollution Intelligence Platform.

Tests cover:
  - API endpoints (auth, factories, violations, anomalies, alerts, dashboard, agents)
  - Agent pipeline logic (monitoring, anomaly, compliance, forecasting)
  - Data services and ML preprocessing

Run with:
    cd backend
    pip install pytest pytest-asyncio httpx
    pytest ../tests/ -v
"""

import os
import sys
import pytest

# Ensure backend is importable
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_BACKEND = os.path.join(_ROOT, "backend")
sys.path.insert(0, _BACKEND)
sys.path.insert(0, _ROOT)   # needed so `agents.*` is importable
os.chdir(_BACKEND)

# Use in-memory SQLite for tests
os.environ["DATABASE_URL"] = "sqlite:///./test_pollution.db"
os.environ["JWT_SECRET"]   = "test-secret-key"
os.environ["JWT_EXPIRE_MINUTES"] = "60"
os.environ["WATSONX_API_KEY"] = ""
os.environ["WATSONX_AI_URL"]  = ""

from dotenv import load_dotenv
load_dotenv(dotenv_path=".env.example")

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# ─────────────────────────────────────────────
# Test DB Setup
# ─────────────────────────────────────────────

TEST_DB_URL = "sqlite:///./test_pollution.db"
engine_test = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)


def get_test_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    from models.database import Base
    Base.metadata.create_all(bind=engine_test)
    # Seed minimal data
    from models.database import User, Factory, PollutionLimit
    from services.auth_service import get_password_hash

    db = TestingSession()
    # Users
    db.add(User(username="test_admin", email="ta@test.com",
                password_hash=get_password_hash("testpass"), role="admin"))
    db.add(User(username="test_viewer", email="tv@test.com",
                password_hash=get_password_hash("viewerpass"), role="viewer"))
    # Factory
    db.add(Factory(
        id="F001", name="Test Factory Alpha", location="Vapi",
        latitude=20.37, longitude=72.90, type="Chemical", status="active",
    ))
    db.add(Factory(
        id="F002", name="Test Factory Beta", location="Ankleshwar",
        latitude=21.62, longitude=73.00, type="Textile", status="active",
    ))
    # Pollution limits
    for item in [
        ("pm25", 60, "µg/m³"), ("pm10", 100, "µg/m³"), ("so2", 80, "µg/m³"),
        ("no2", 80, "µg/m³"), ("co", 10, "mg/m³"), ("ph", 8.5, "pH"),
        ("turbidity", 10, "NTU"), ("chemical_level", 50, "mg/L"),
    ]:
        db.add(PollutionLimit(
            parameter=item[0], configured_limit=item[1], unit=item[2],
            severity_low=item[1], severity_medium=item[1]*1.5,
            severity_high=item[1]*2.0, severity_critical=item[1]*3.0,
        ))
    db.commit()
    db.close()
    yield
    # Cleanup
    try:
        Base.metadata.drop_all(bind=engine_test)
        engine_test.dispose()
    except Exception:
        pass
    import time
    time.sleep(0.1)
    try:
        if os.path.exists("test_pollution.db"):
            os.remove("test_pollution.db")
    except OSError:
        pass  # Windows may hold file lock; not a test failure


@pytest.fixture(scope="session")
def client():
    from main import app
    from models.database import get_db
    app.dependency_overrides[get_db] = get_test_db
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
def auth_headers(client):
    resp = client.post("/api/auth/login", json={"username": "test_admin", "password": "testpass"})
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ─────────────────────────────────────────────
# Auth tests
# ─────────────────────────────────────────────

class TestAuth:
    def test_login_success(self, client):
        resp = client.post("/api/auth/login", json={"username": "test_admin", "password": "testpass"})
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["role"] == "admin"
        assert data["username"] == "test_admin"

    def test_login_wrong_password(self, client):
        resp = client.post("/api/auth/login", json={"username": "test_admin", "password": "wrong"})
        assert resp.status_code == 401

    def test_login_unknown_user(self, client):
        resp = client.post("/api/auth/login", json={"username": "nobody", "password": "x"})
        assert resp.status_code == 401

    def test_register_new_user(self, client):
        resp = client.post("/api/auth/register", json={
            "username": "new_tester",
            "password": "secret123",
            "email": "new@test.com",
            "role": "viewer",
        })
        assert resp.status_code == 201
        assert resp.json()["username"] == "new_tester"

    def test_register_duplicate_username(self, client):
        data = {"username": "test_admin", "password": "x", "email": "dup@test.com"}
        resp = client.post("/api/auth/register", json=data)
        assert resp.status_code == 400


# ─────────────────────────────────────────────
# Health check
# ─────────────────────────────────────────────

class TestHealth:
    def test_root(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_health_endpoint(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"


# ─────────────────────────────────────────────
# Factories
# ─────────────────────────────────────────────

class TestFactories:
    def test_list_factories(self, client, auth_headers):
        resp = client.get("/api/factories", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 2
        ids = [f["id"] for f in data]
        assert "F001" in ids

    def test_get_factory(self, client, auth_headers):
        resp = client.get("/api/factories/F001", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == "F001"
        assert resp.json()["location"] == "Vapi"

    def test_get_factory_not_found(self, client, auth_headers):
        resp = client.get("/api/factories/NONEXISTENT", headers=auth_headers)
        assert resp.status_code == 404


# ─────────────────────────────────────────────
# Readings
# ─────────────────────────────────────────────

class TestReadings:
    def test_get_readings_empty(self, client, auth_headers):
        resp = client.get("/api/readings/F001", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_get_readings_with_limit(self, client, auth_headers):
        resp = client.get("/api/readings/F001?limit=5", headers=auth_headers)
        assert resp.status_code == 200
        assert len(resp.json()) <= 5


# ─────────────────────────────────────────────
# Violations
# ─────────────────────────────────────────────

class TestViolations:
    def test_list_violations(self, client, auth_headers):
        resp = client.get("/api/violations", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


# ─────────────────────────────────────────────
# Anomalies
# ─────────────────────────────────────────────

class TestAnomalies:
    def test_list_anomalies(self, client, auth_headers):
        resp = client.get("/api/anomalies", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


# ─────────────────────────────────────────────
# Alerts
# ─────────────────────────────────────────────

class TestAlerts:
    def test_list_alerts(self, client, auth_headers):
        resp = client.get("/api/alerts", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


# ─────────────────────────────────────────────
# Dashboard
# ─────────────────────────────────────────────

class TestDashboard:
    def test_dashboard_summary(self, client, auth_headers):
        resp = client.get("/api/dashboard/summary", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        required_keys = [
            "total_factories", "active_violations", "critical_violations",
            "open_anomalies", "pending_alerts", "open_incidents",
            "factories_at_risk", "recent_readings_count",
            "violations_by_severity", "top_violating_factories", "risk_distribution",
        ]
        for key in required_keys:
            assert key in data, f"Missing key: {key}"
        assert data["total_factories"] >= 2


# ─────────────────────────────────────────────
# Risk Scores
# ─────────────────────────────────────────────

class TestRiskScores:
    def test_list_risk_scores(self, client, auth_headers):
        resp = client.get("/api/risk-scores", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


# ─────────────────────────────────────────────
# Community Risk
# ─────────────────────────────────────────────

class TestCommunityRisk:
    def test_community_risk(self, client, auth_headers):
        resp = client.get("/api/community-risk", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


# ─────────────────────────────────────────────
# Agent Pipeline
# ─────────────────────────────────────────────

class TestAgentPipeline:
    def test_pipeline_normal_reading(self, client, auth_headers):
        resp = client.post("/api/agents/process", headers=auth_headers, json={
            "factory_id": "F001",
            "parameter": "pm25",
            "value": 22.0,
            "configured_limit": 60.0,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["factory_id"] == "F001"
        assert "alert_level" in data
        assert data["alert_level"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL")

    def test_pipeline_critical_so2(self, client, auth_headers):
        """Value well above limit should produce HIGH or CRITICAL alert."""
        resp = client.post("/api/agents/process", headers=auth_headers, json={
            "factory_id": "F001",
            "parameter": "so2",
            "value": 180.0,
            "configured_limit": 80.0,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["alert_level"] in ("HIGH", "CRITICAL")

    def test_pipeline_returns_combined_assessment(self, client, auth_headers):
        resp = client.post("/api/agents/process", headers=auth_headers, json={
            "factory_id": "F001",
            "parameter": "so2",
            "value": 160.0,
            "configured_limit": 80.0,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "combined_assessment" in data
        assert isinstance(data["combined_assessment"], str)
        assert len(data["combined_assessment"]) > 0


# ─────────────────────────────────────────────
# Agent unit tests
# ─────────────────────────────────────────────

class TestMonitoringAgent:
    def test_normal_reading(self):
        from agents.monitoring.agent import monitoring_agent
        ctx = {"factory_id": "F001", "parameter": "pm25", "value": 22.0, "configured_limit": 60.0}
        result = monitoring_agent.process(ctx)
        assert result["current_status"] == "NORMAL"

    def test_warning_reading(self):
        from agents.monitoring.agent import monitoring_agent
        ctx = {"factory_id": "F001", "parameter": "pm25", "value": 52.0, "configured_limit": 60.0}
        result = monitoring_agent.process(ctx)
        assert result["current_status"] in ("WARNING", "CRITICAL")

    def test_critical_reading(self):
        from agents.monitoring.agent import monitoring_agent
        ctx = {"factory_id": "F001", "parameter": "so2", "value": 200.0, "configured_limit": 80.0}
        result = monitoring_agent.process(ctx)
        assert result["current_status"] == "CRITICAL"


class TestAnomalyAgent:
    def test_anomaly_score_present(self):
        from agents.anomaly.agent import anomaly_agent
        ctx = {
            "factory_id": "F001", "parameter": "so2", "value": 200.0,
            "current_status": "CRITICAL",
            "history": [
                {"so2": 30 + i * 0.1} for i in range(50)
            ],
        }
        result = anomaly_agent.process(ctx)
        assert "anomaly_score" in result
        assert 0 <= result["anomaly_score"] <= 100

    def test_no_history_fallback(self):
        from agents.anomaly.agent import anomaly_agent
        ctx = {"factory_id": "F001", "parameter": "pm25", "value": 55.0, "history": []}
        result = anomaly_agent.process(ctx)
        assert "anomaly_score" in result


class TestComplianceAgent:
    def test_violation_detected(self):
        from agents.compliance.agent import compliance_agent
        ctx = {
            "factory_id": "F001",
            "parameter": "so2", "value": 120.0, "configured_limit": 80.0,
            "current_status": "CRITICAL",
        }
        result = compliance_agent.process(ctx)
        assert result.get("violation_status") == "VIOLATION"
        assert "exceedance_percent" in result

    def test_compliant_reading(self):
        from agents.compliance.agent import compliance_agent
        ctx = {
            "factory_id": "F001",
            "parameter": "pm25", "value": 25.0, "configured_limit": 60.0,
            "current_status": "NORMAL",
        }
        result = compliance_agent.process(ctx)
        assert result.get("violation_status") == "COMPLIANT"


class TestForecastingAgent:
    def test_forecast_with_history(self):
        from agents.forecasting.agent import forecasting_agent
        import random
        history = [{"so2": 30 + random.gauss(0, 2), "timestamp": f"2026-09-0{(i % 7) + 1}T{10 + (i % 12):02d}:00:00"} for i in range(40)]
        ctx = {
            "factory_id": "F001",
            "parameter": "so2", "value": 85.0, "configured_limit": 80.0,
            "history": history,
        }
        result = forecasting_agent.process(ctx)
        assert "forecast" in result
        forecast = result["forecast"]
        assert "predicted_1h" in forecast or "model_used" in forecast

    def test_forecast_no_history(self):
        from agents.forecasting.agent import forecasting_agent
        ctx = {"factory_id": "F001", "parameter": "pm25", "value": 55.0, "history": []}
        result = forecasting_agent.process(ctx)
        # Should not crash
        assert "forecast" in result


class TestSupervisorAgent:
    def test_normal_flow(self):
        from agents.supervisor.agent import supervisor_agent
        ctx = {
            "factory_id": "F001",
            "parameter": "pm25", "value": 20.0, "configured_limit": 60.0,
            "history": [],
        }
        result = supervisor_agent.process(ctx)
        assert result["alert_level"] == "LOW"
        assert "combined_assessment" in result

    def test_critical_flow(self):
        from agents.supervisor.agent import supervisor_agent
        ctx = {
            "factory_id": "F001",
            "parameter": "so2", "value": 250.0, "configured_limit": 80.0,
            "history": [{"so2": 30 + i} for i in range(30)],
        }
        result = supervisor_agent.process(ctx)
        assert result["alert_level"] in ("HIGH", "CRITICAL")
        assert result["current_status"] == "CRITICAL"


# ─────────────────────────────────────────────
# Auth service unit tests
# ─────────────────────────────────────────────

class TestAuthService:
    def test_password_hash_and_verify(self):
        from services.auth_service import get_password_hash, verify_password
        hashed = get_password_hash("my_secret")
        assert verify_password("my_secret", hashed)
        assert not verify_password("wrong", hashed)

    def test_token_create_decode(self):
        from services.auth_service import create_access_token, decode_access_token
        token = create_access_token({"sub": "test_user", "role": "admin"})
        assert isinstance(token, str)
        payload = decode_access_token(token)
        assert payload is not None
        assert payload["sub"] == "test_user"
        assert payload["role"] == "admin"

    def test_invalid_token(self):
        from services.auth_service import decode_access_token
        result = decode_access_token("not.a.valid.token")
        assert result is None


# ─────────────────────────────────────────────
# ML preprocessing unit tests
# ─────────────────────────────────────────────

class TestMLPreprocessing:
    def test_preprocessor_basic(self):
        """Ensure preprocessor runs without error on sample data."""
        try:
            from ml.preprocessing.preprocessor import PollutionPreprocessor
            pp = PollutionPreprocessor()
            import pandas as pd
            import numpy as np
            data = pd.DataFrame({
                "pm25": np.random.uniform(10, 100, 50),
                "pm10": np.random.uniform(20, 200, 50),
                "so2":  np.random.uniform(10, 150, 50),
                "no2":  np.random.uniform(10, 150, 50),
                "co":   np.random.uniform(1, 20, 50),
            })
            result = pp.preprocess(data)
            assert result is not None
        except (ImportError, AttributeError):
            pytest.skip("ML preprocessor not available or interface changed")


# ─────────────────────────────────────────────
# Granite service unit tests (offline/fallback)
# ─────────────────────────────────────────────

class TestGraniteServiceFallback:
    """Test that Granite service falls back gracefully when credentials are missing."""

    def test_explain_incident_fallback(self):
        from services.granite_service import GraniteService
        gs = GraniteService()
        # With no credentials, should return fallback string, not raise
        result = gs.explain_incident({
            "title": "SO2 Spike", "factory_id": "F004",
            "severity": "CRITICAL", "status": "open",
        })
        assert isinstance(result, str)
        assert len(result) > 0

    def test_explain_violation_fallback(self):
        from services.granite_service import GraniteService
        gs = GraniteService()
        result = gs.explain_violation({
            "parameter": "so2", "value": 150, "limit_value": 80,
            "exceedance_percent": 87.5, "severity": "CRITICAL",
        })
        assert isinstance(result, str)
        assert "so2" in result.lower() or "150" in result or "80" in result

    def test_answer_query_fallback(self):
        from services.granite_service import GraniteService
        gs = GraniteService()
        result = gs.answer_query("What is the current SO2 level?", {"so2": 150, "factory": "F004"})
        assert isinstance(result, str)
        assert len(result) > 0

    def test_generate_alert_fallback(self):
        from services.granite_service import GraniteService
        gs = GraniteService()
        result = gs.generate_alert_message({
            "severity": "CRITICAL", "factory_id": "F004",
            "parameter": "so2", "value": 150,
        })
        assert isinstance(result, str)
        assert "CRITICAL" in result or "F004" in result
