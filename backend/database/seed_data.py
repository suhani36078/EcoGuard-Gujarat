"""
Synthetic data generation for the Gujarat Pollution Platform demo.
Generates 7 factories with 500+ sensor readings each spanning 7 days,
plus violations, anomalies, risk scores, alerts, and incidents.
"""

import os
import sys
import random
import math
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import (
    SessionLocal, Base, engine,
    Factory, SensorReading, PollutionLimit, Violation, Anomaly,
    Forecast, RiskScore, Alert, Incident, AgentLog, User,
)
from services.auth_service import get_password_hash

# ─────────────────────────────────────────────
# Deterministic random for reproducibility
# ─────────────────────────────────────────────
random.seed(42)

BASE_TIME = datetime(2026, 9, 1, 0, 0, 0)   # 7 days of data
READINGS_PER_FACTORY = 504                    # 1 per 20 min × 7 days

# ─────────────────────────────────────────────
# Factory definitions
# ─────────────────────────────────────────────
FACTORIES = [
    {
        "id": "F001", "name": "Factory A - Vapi Chemical Works",
        "location": "Vapi", "latitude": 20.3724, "longitude": 72.9027,
        "type": "Chemical", "status": "active", "scenario": "normal",
    },
    {
        "id": "F002", "name": "Factory B - Ankleshwar Dye Plant",
        "location": "Ankleshwar", "latitude": 21.6263, "longitude": 73.0049,
        "type": "Textile Dye", "status": "active", "scenario": "moderate",
    },
    {
        "id": "F003", "name": "Factory C - Vatva Pharma Industries",
        "location": "Vatva", "latitude": 22.9682, "longitude": 72.6389,
        "type": "Pharmaceutical", "status": "active", "scenario": "repeat_violator",
    },
    {
        "id": "F004", "name": "Factory D - Vapi Petrochemical",
        "location": "Vapi", "latitude": 20.3800, "longitude": 72.9100,
        "type": "Petrochemical", "status": "active", "scenario": "so2_spike",
    },
    {
        "id": "F005", "name": "Factory E - Ankleshwar Effluent Plant",
        "location": "Ankleshwar", "latitude": 21.6350, "longitude": 73.0150,
        "type": "Effluent Treatment", "status": "active", "scenario": "water_problem",
    },
    {
        "id": "F006", "name": "Factory F - Vapi Community Risk Zone",
        "location": "Vapi", "latitude": 20.3650, "longitude": 72.8950,
        "type": "Mixed Industry", "status": "active", "scenario": "community_risk",
    },
    {
        "id": "F007", "name": "Factory G - Vatva Trend Watcher",
        "location": "Vatva", "latitude": 22.9750, "longitude": 72.6450,
        "type": "Chemical", "status": "active", "scenario": "future_violation",
    },
]

# ─────────────────────────────────────────────
# Pollution limits
# ─────────────────────────────────────────────
POLLUTION_LIMITS = [
    {"parameter": "pm25",          "configured_limit": 60,  "unit": "µg/m³",
     "severity_low": 60,  "severity_medium": 90,  "severity_high": 120, "severity_critical": 180},
    {"parameter": "pm10",          "configured_limit": 100, "unit": "µg/m³",
     "severity_low": 100, "severity_medium": 150, "severity_high": 200, "severity_critical": 300},
    {"parameter": "so2",           "configured_limit": 80,  "unit": "µg/m³",
     "severity_low": 80,  "severity_medium": 120, "severity_high": 160, "severity_critical": 200},
    {"parameter": "no2",           "configured_limit": 80,  "unit": "µg/m³",
     "severity_low": 80,  "severity_medium": 120, "severity_high": 160, "severity_critical": 200},
    {"parameter": "co",            "configured_limit": 10,  "unit": "mg/m³",
     "severity_low": 10,  "severity_medium": 15,  "severity_high": 20,  "severity_critical": 30},
    {"parameter": "ph",            "configured_limit": 8.5, "unit": "pH",
     "severity_low": 8.5, "severity_medium": 9.0, "severity_high": 9.5, "severity_critical": 10.0},
    {"parameter": "turbidity",     "configured_limit": 10,  "unit": "NTU",
     "severity_low": 10,  "severity_medium": 20,  "severity_high": 50,  "severity_critical": 100},
    {"parameter": "chemical_level","configured_limit": 50,  "unit": "mg/L",
     "severity_low": 50,  "severity_medium": 75,  "severity_high": 100, "severity_critical": 150},
]

# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def gauss(mean, sigma):
    return random.gauss(mean, sigma)

def severity_for(param, value):
    """Return severity label based on pollution_limits thresholds."""
    limits = {r["parameter"]: r for r in POLLUTION_LIMITS}
    if param not in limits:
        return "LOW"
    l = limits[param]
    if param == "ph":
        if value <= 6.5:
            exceedance = (6.5 - value) / 6.5 * 100
        else:
            exceedance = (value - 8.5) / 8.5 * 100
    else:
        exceedance = (value - l["configured_limit"]) / l["configured_limit"] * 100
    if exceedance <= 0:
        return None
    if value >= l["severity_critical"]:
        return "CRITICAL"
    if value >= l["severity_high"]:
        return "HIGH"
    if value >= l["severity_medium"]:
        return "MEDIUM"
    return "LOW"


def exceedance_pct(param, value):
    limits = {r["parameter"]: r for r in POLLUTION_LIMITS}
    if param not in limits:
        return 0.0
    l = limits[param]
    if param == "ph":
        limit_val = 8.5 if value > 8.5 else 6.5
    else:
        limit_val = l["configured_limit"]
    return round(max(0.0, (value - limit_val) / limit_val * 100), 2)


# ─────────────────────────────────────────────
# Per-scenario sensor reading generator
# ─────────────────────────────────────────────

def generate_readings(factory_id, scenario, n=READINGS_PER_FACTORY):
    readings = []
    for i in range(n):
        t = BASE_TIME + timedelta(minutes=20 * i)
        hour = t.hour
        day_frac = i / n  # 0 → 1 over the 7 days

        # Base meteorological values
        temperature = clamp(gauss(32 + 4 * math.sin(math.pi * hour / 12), 1.5), 22, 42)
        humidity    = clamp(gauss(65 - 0.3 * temperature, 5), 30, 95)
        wind_speed  = clamp(gauss(3.5, 0.8), 0.5, 12)

        if scenario == "community_risk":
            # Wind blowing toward residential (SE direction)
            wind_direction = clamp(gauss(135, 15), 110, 160)
        else:
            wind_direction = clamp(gauss(220, 45), 0, 360)

        production = 1.0 if 8 <= hour <= 20 else 0.4

        # ── normal baseline ──
        pm25      = clamp(gauss(25 * production, 5), 5, 250)
        pm10      = clamp(gauss(45 * production, 8), 10, 400)
        so2       = clamp(gauss(30 * production, 8), 5, 300)
        no2       = clamp(gauss(35 * production, 8), 5, 300)
        co        = clamp(gauss(4 * production, 0.8), 0.5, 40)
        ph        = clamp(gauss(7.2, 0.15), 5.5, 11.0)
        turbidity = clamp(gauss(4, 1), 0.5, 200)
        chemical  = clamp(gauss(20, 5), 2, 200)

        # ── scenario overrides ──
        if scenario == "moderate":
            pm25  = clamp(gauss(55 * production, 10), 5, 250)
            pm10  = clamp(gauss(85 * production, 15), 10, 400)
            so2   = clamp(gauss(65 * production, 12), 5, 300)
            no2   = clamp(gauss(70 * production, 12), 5, 300)
            co    = clamp(gauss(8 * production, 1.5), 0.5, 40)

        elif scenario == "repeat_violator":
            # Cycles of violations every ~200 readings
            cycle = math.sin(math.pi * i / 100)
            pm25  = clamp(gauss(70 + 30 * max(0, cycle), 8), 5, 250)
            pm10  = clamp(gauss(110 + 50 * max(0, cycle), 12), 10, 400)
            so2   = clamp(gauss(85 + 40 * max(0, cycle), 10), 5, 300)
            co    = clamp(gauss(10 + 5 * max(0, cycle), 1.5), 0.5, 40)

        elif scenario == "so2_spike":
            # SO2 gradual spike in last 20% of readings
            spike_start = int(n * 0.80)
            if i >= spike_start:
                progress = (i - spike_start) / (n - spike_start)  # 0 → 1
                # 50 → 55 → 60 → 75 → 95 → 120 → 150
                spike_values = [50, 55, 60, 75, 95, 120, 150]
                idx = int(progress * (len(spike_values) - 1))
                idx = min(idx, len(spike_values) - 2)
                frac = progress * (len(spike_values) - 1) - idx
                base_so2 = spike_values[idx] + frac * (spike_values[idx + 1] - spike_values[idx])
                so2 = clamp(gauss(base_so2, 3), 5, 300)
            else:
                so2 = clamp(gauss(45 * production, 8), 5, 300)

        elif scenario == "water_problem":
            ph        = clamp(gauss(9.8, 0.4), 5.5, 11.0)
            turbidity = clamp(gauss(55, 12), 0.5, 200)
            chemical  = clamp(gauss(80, 15), 2, 200)

        elif scenario == "community_risk":
            # High PM + wind toward residential
            pm25 = clamp(gauss(95 * production, 15), 5, 250)
            pm10 = clamp(gauss(145 * production, 20), 10, 400)
            co   = clamp(gauss(12 * production, 2), 0.5, 40)

        elif scenario == "future_violation":
            # SO2 + NO2 slowly increasing trend
            trend = 1.0 + day_frac * 1.2
            so2  = clamp(gauss(40 * trend * production, 8), 5, 300)
            no2  = clamp(gauss(42 * trend * production, 8), 5, 300)
            pm25 = clamp(gauss(30 * trend * production, 6), 5, 250)

        readings.append({
            "factory_id": factory_id,
            "timestamp": t,
            "pm25":             round(pm25, 2),
            "pm10":             round(pm10, 2),
            "so2":              round(so2, 2),
            "no2":              round(no2, 2),
            "co":               round(co, 2),
            "temperature":      round(temperature, 1),
            "humidity":         round(humidity, 1),
            "wind_speed":       round(wind_speed, 1),
            "wind_direction":   round(wind_direction, 1),
            "ph":               round(ph, 2),
            "turbidity":        round(turbidity, 2),
            "chemical_level":   round(chemical, 2),
            "production_activity": round(production, 2),
        })
    return readings


def detect_violations_from_readings(readings, factory_id):
    """Generate violation records from readings that exceed limits."""
    violations = []
    limits_map = {r["parameter"]: r["configured_limit"] for r in POLLUTION_LIMITS}
    params = ["pm25", "pm10", "so2", "no2", "co", "turbidity", "chemical_level"]

    for r in readings:
        for param in params:
            val = r.get(param, 0)
            limit = limits_map.get(param, 9999)
            if val > limit:
                sev = severity_for(param, val)
                exc = exceedance_pct(param, val)
                violations.append({
                    "factory_id": factory_id,
                    "parameter": param,
                    "value": val,
                    "limit_value": limit,
                    "exceedance_percent": exc,
                    "severity": sev,
                    "status": "active" if val > limit * 1.1 else "resolved",
                    "detected_at": r["timestamp"],
                    "resolved_at": r["timestamp"] + timedelta(hours=random.randint(1, 8)) if val <= limit * 1.1 else None,
                })
    # Keep at most 80 violations per factory to avoid DB bloat
    random.shuffle(violations)
    return violations[:80]


def generate_anomalies(readings, factory_id):
    """Z-score based anomaly detection for seeding."""
    import statistics
    anomalies = []
    params = ["pm25", "pm10", "so2", "no2", "co", "turbidity", "chemical_level"]
    for param in params:
        values = [r[param] for r in readings if r.get(param) is not None]
        if len(values) < 10:
            continue
        mean = statistics.mean(values)
        stdev = statistics.stdev(values) or 1
        for r in readings:
            val = r.get(param)
            if val is None:
                continue
            z = abs((val - mean) / stdev)
            if z > 2.5:
                score = min(100, round(z * 20, 1))
                anomalies.append({
                    "factory_id": factory_id,
                    "parameter": param,
                    "anomaly_score": score,
                    "detected_at": r["timestamp"],
                    "description": (
                        f"{param.upper()} value {val} deviates {z:.1f}σ from mean {mean:.1f}. "
                        f"Possible equipment fault or unauthorized discharge."
                    ),
                    "status": "open" if score > 60 else "reviewed",
                })
    random.shuffle(anomalies)
    return anomalies[:30]


def generate_forecasts(factory_id, scenario):
    """Generate simple forecast records for next 24 hours."""
    forecasts = []
    future_base = BASE_TIME + timedelta(days=7)
    params_map = {
        "normal":           {"so2": (30, 2), "pm25": (25, 3), "no2": (35, 3)},
        "moderate":         {"so2": (68, 5), "pm25": (58, 6), "no2": (72, 5)},
        "repeat_violator":  {"so2": (90, 8), "pm25": (75, 7), "no2": (80, 6)},
        "so2_spike":        {"so2": (170, 10), "pm25": (40, 5), "no2": (50, 5)},
        "water_problem":    {"ph": (10.1, 0.2), "turbidity": (58, 8), "chemical_level": (85, 10)},
        "community_risk":   {"pm25": (100, 12), "co": (13, 1.5), "pm10": (155, 18)},
        "future_violation": {"so2": (82, 5), "no2": (85, 5), "pm25": (65, 6)},
    }
    scenario_params = params_map.get(scenario, params_map["normal"])
    for h in range(1, 25):
        for param, (mean, sigma) in scenario_params.items():
            forecasts.append({
                "factory_id": factory_id,
                "parameter": param,
                "predicted_value": round(clamp(gauss(mean, sigma), 0, 400), 2),
                "forecast_time": future_base + timedelta(hours=h),
                "confidence": round(clamp(gauss(0.78, 0.08), 0.5, 0.98), 3),
                "model_used": "LSTM+IsolationForest",
            })
    return forecasts


def generate_risk_score(factory_id, scenario):
    risk_map = {
        "normal":           (22, "LOW"),
        "moderate":         (48, "MEDIUM"),
        "repeat_violator":  (65, "HIGH"),
        "so2_spike":        (78, "HIGH"),
        "water_problem":    (55, "MEDIUM"),
        "community_risk":   (85, "CRITICAL"),
        "future_violation": (58, "MEDIUM"),
    }
    score, level = risk_map.get(scenario, (30, "LOW"))
    return {
        "factory_id": factory_id,
        "overall_score": score + random.randint(-3, 3),
        "risk_level": level,
        "components": {
            "air_quality": round(score * 0.4 + random.uniform(-5, 5), 1),
            "water_quality": round(score * 0.25 + random.uniform(-5, 5), 1),
            "violation_history": round(score * 0.2 + random.uniform(-3, 3), 1),
            "community_exposure": round(score * 0.15 + random.uniform(-3, 3), 1),
        },
        "calculated_at": BASE_TIME + timedelta(days=7),
    }


def generate_alerts(factory_id, scenario, violations):
    alerts = []
    severity_map = {
        "normal": [], "moderate": ["MEDIUM"],
        "repeat_violator": ["HIGH", "HIGH", "MEDIUM"],
        "so2_spike": ["CRITICAL", "HIGH"],
        "water_problem": ["HIGH", "MEDIUM"],
        "community_risk": ["CRITICAL", "HIGH"],
        "future_violation": ["MEDIUM"],
    }
    for sev in severity_map.get(scenario, []):
        alerts.append({
            "factory_id": factory_id,
            "severity": sev,
            "message": (
                f"[{sev}] Pollution limit exceeded at {factory_id}. "
                f"Immediate inspection required."
            ),
            "recipients": "gpcb@gujarat.gov.in,officer@pollution.gov",
            "status": "pending" if sev == "CRITICAL" else "acknowledged",
            "created_at": BASE_TIME + timedelta(days=6, hours=random.randint(0, 23)),
            "acknowledged_at": (
                None if sev == "CRITICAL"
                else BASE_TIME + timedelta(days=6, hours=random.randint(1, 23))
            ),
            "resolved_at": None,
        })
    return alerts


def generate_incidents(factory_id, scenario):
    if scenario in ("normal",):
        return []
    incident_map = {
        "so2_spike": {
            "title": "Critical SO2 Spike - Immediate Action Required",
            "description": (
                "SO2 levels escalating from 50 to 150 µg/m³ over 24 hours. "
                "Suspected flue gas desulphurization unit failure. "
                "Evacuation advisory issued for 500m radius."
            ),
            "severity": "CRITICAL", "status": "open",
        },
        "water_problem": {
            "title": "Effluent Treatment Failure - High pH & Turbidity",
            "description": (
                "Effluent discharge pH at 9.8 (limit 8.5). Turbidity at 55 NTU (limit 10). "
                "GIDC drainage authority notified. Shutdown order pending."
            ),
            "severity": "HIGH", "status": "investigating",
        },
        "community_risk": {
            "title": "Community Exposure Alert - Wind Toward Residential",
            "description": (
                "High PM2.5 (95 µg/m³) with wind direction 135° toward residential colony. "
                "Health advisory issued. Schools notified."
            ),
            "severity": "CRITICAL", "status": "open",
        },
        "repeat_violator": {
            "title": "Repeated Compliance Failure - Legal Notice Issued",
            "description": (
                "Factory has exceeded limits 12 times in last 30 days. "
                "Environmental court notice issued. Show-cause order pending."
            ),
            "severity": "HIGH", "status": "legal_action",
        },
        "future_violation": {
            "title": "Predicted Violation - Preventive Action Required",
            "description": (
                "AI forecasting predicts SO2 will exceed 80 µg/m³ within 48 hours "
                "based on current trend. Plant manager contacted."
            ),
            "severity": "MEDIUM", "status": "preventive",
        },
        "moderate": {
            "title": "Elevated Pollution - Monitoring Increased",
            "description": "Multiple parameters approaching limits. Enhanced monitoring activated.",
            "severity": "MEDIUM", "status": "monitoring",
        },
    }
    if scenario not in incident_map:
        return []
    inc = incident_map[scenario].copy()
    inc.update({
        "factory_id": factory_id,
        "created_at": BASE_TIME + timedelta(days=5, hours=random.randint(0, 23)),
        "resolved_at": None,
        "assigned_to": "officer@pollution.gov",
    })
    return [inc]


# ─────────────────────────────────────────────
# Main seeding function
# ─────────────────────────────────────────────

def seed_all():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # ── Wipe existing data ──
        for model in [AgentLog, Alert, Incident, RiskScore, Forecast,
                      Anomaly, Violation, SensorReading, PollutionLimit,
                      Factory, User]:
            db.query(model).delete()
        db.commit()
        print("Existing data cleared.")

        # ── Users ──
        users = [
            User(username="admin",     email="admin@pollution.gov",
                 password_hash=get_password_hash("admin123"),     role="admin"),
            User(username="regulator", email="regulator@gpcb.gov",
                 password_hash=get_password_hash("regulator123"), role="regulator"),
            User(username="officer",   email="officer@pollution.gov",
                 password_hash=get_password_hash("officer123"),   role="officer"),
            User(username="viewer",    email="viewer@gpcb.gov",
                 password_hash=get_password_hash("viewer123"),    role="viewer"),
        ]
        db.add_all(users)
        db.commit()
        print(f"[OK] Seeded {len(users)} users")

        # ── Pollution limits ──
        db.add_all([PollutionLimit(**pl) for pl in POLLUTION_LIMITS])
        db.commit()
        print(f"[OK] Seeded {len(POLLUTION_LIMITS)} pollution limits")

        # ── Factories + readings + derived data ──
        for fdef in FACTORIES:
            scenario = fdef.pop("scenario")
            factory = Factory(**fdef)
            db.add(factory)
            db.commit()

            readings_data = generate_readings(factory.id, scenario)
            db.bulk_insert_mappings(SensorReading, readings_data)
            db.commit()
            print(f"  [OK] {factory.id}: {len(readings_data)} readings ({scenario})")

            violations_data = detect_violations_from_readings(readings_data, factory.id)
            if violations_data:
                db.bulk_insert_mappings(Violation, violations_data)
                db.commit()
                print(f"    [OK] {len(violations_data)} violations")

            anomalies_data = generate_anomalies(readings_data, factory.id)
            if anomalies_data:
                db.bulk_insert_mappings(Anomaly, anomalies_data)
                db.commit()
                print(f"    [OK] {len(anomalies_data)} anomalies")

            forecasts_data = generate_forecasts(factory.id, scenario)
            db.bulk_insert_mappings(Forecast, forecasts_data)
            db.commit()

            risk_data = generate_risk_score(factory.id, scenario)
            db.add(RiskScore(**risk_data))
            db.commit()

            alerts_data = generate_alerts(factory.id, scenario, violations_data)
            if alerts_data:
                db.bulk_insert_mappings(Alert, alerts_data)
                db.commit()
                print(f"    [OK] {len(alerts_data)} alerts")

            incidents_data = generate_incidents(factory.id, scenario)
            if incidents_data:
                db.bulk_insert_mappings(Incident, incidents_data)
                db.commit()
                print(f"    [OK] {len(incidents_data)} incident(s)")

            # Restore scenario key for potential re-runs
            fdef["scenario"] = scenario

        # ── Agent logs ──
        agent_logs = [
            AgentLog(agent_name="MonitoringAgent",   action="scan_readings",
                     input_summary="Batch scan of 504 readings",
                     output_summary="12 WARNING, 5 CRITICAL events detected"),
            AgentLog(agent_name="AnomalyAgent",      action="detect_anomalies",
                     input_summary="Rolling z-score + IsolationForest",
                     output_summary="87 anomalies scored across 7 factories"),
            AgentLog(agent_name="ComplianceAgent",   action="check_limits",
                     input_summary="All readings vs pollution_limits table",
                     output_summary="234 violations detected, 3 CRITICAL"),
            AgentLog(agent_name="ForecastingAgent",  action="run_forecast",
                     input_summary="LSTM model, 24h horizon",
                     output_summary="Factory G predicted to breach SO2 limit in 48h"),
            AgentLog(agent_name="SupervisorAgent",   action="aggregate",
                     input_summary="Outputs from all sub-agents",
                     output_summary="Combined assessment issued for 7 factories"),
        ]
        db.add_all(agent_logs)
        db.commit()
        print(f"[OK] Seeded {len(agent_logs)} agent logs")

        print("\n[DONE] Seed complete! Database ready for demo.")

    finally:
        db.close()


if __name__ == "__main__":
    seed_all()
