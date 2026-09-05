"""
Seed data for PRITHVI-X new tables: districts, hotspots, citizen_reports, pollution_index.
This extends the existing seed_data.py without replacing it.
"""

import os
import sys
from datetime import datetime, timedelta
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import (
    SessionLocal, Base, engine,
    DistrictData, Hotspot, CitizenReport, GujaratPollutionIndex,
)

random.seed(42)

# ─────────────────────────────────────────────
# Gujarat Districts Data (26 districts)
# ─────────────────────────────────────────────
DISTRICTS = [
    {
        "district_name": "Ahmedabad", "district_code": "AHM",
        "latitude": 23.0225, "longitude": 72.5714,
        "air_score": 68.0, "water_score": 52.0, "noise_score": 62.0,
        "industrial_score": 65.0, "waste_score": 55.0, "overall_score": 63.2,
        "risk_level": "HIGH", "main_pollutant": "PM2.5", "main_source": "Vehicular + Industrial (Vatva)",
        "trend": "stable", "monitored_locations": 12, "high_risk_zones": 3,
        "active_alerts": 4, "population": 8253000, "area_sq_km": 8707.0,
        "data_confidence": 0.78,
    },
    {
        "district_name": "Surat", "district_code": "SRT",
        "latitude": 21.1702, "longitude": 72.8311,
        "air_score": 58.0, "water_score": 61.0, "noise_score": 54.0,
        "industrial_score": 60.0, "waste_score": 50.0, "overall_score": 58.5,
        "risk_level": "MODERATE", "main_pollutant": "NOx", "main_source": "Textile + Diamond Industry",
        "trend": "stable", "monitored_locations": 8, "high_risk_zones": 2,
        "active_alerts": 2, "population": 6081000, "area_sq_km": 7657.0,
        "data_confidence": 0.72,
    },
    {
        "district_name": "Vapi", "district_code": "VPI",
        "latitude": 20.3724, "longitude": 72.9027,
        "air_score": 82.0, "water_score": 88.0, "noise_score": 55.0,
        "industrial_score": 91.0, "waste_score": 72.0, "overall_score": 83.5,
        "risk_level": "CRITICAL", "main_pollutant": "SO2 + Chemical Effluents",
        "main_source": "Chemical Manufacturing Zone",
        "trend": "increasing", "monitored_locations": 6, "high_risk_zones": 4,
        "active_alerts": 7, "population": 200000, "area_sq_km": 312.0,
        "data_confidence": 0.85,
    },
    {
        "district_name": "Ankleshwar", "district_code": "ANK",
        "latitude": 21.6263, "longitude": 73.0049,
        "air_score": 75.0, "water_score": 81.0, "noise_score": 48.0,
        "industrial_score": 85.0, "waste_score": 65.0, "overall_score": 76.8,
        "risk_level": "HIGH", "main_pollutant": "Textile Dyes + pH", "main_source": "GIDC Industrial Estate",
        "trend": "increasing", "monitored_locations": 5, "high_risk_zones": 3,
        "active_alerts": 5, "population": 180000, "area_sq_km": 290.0,
        "data_confidence": 0.82,
    },
    {
        "district_name": "Vadodara", "district_code": "VDR",
        "latitude": 22.3072, "longitude": 73.1812,
        "air_score": 55.0, "water_score": 48.0, "noise_score": 50.0,
        "industrial_score": 58.0, "waste_score": 45.0, "overall_score": 53.2,
        "risk_level": "MODERATE", "main_pollutant": "SO2", "main_source": "Petrochemical + Fertilizer",
        "trend": "stable", "monitored_locations": 7, "high_risk_zones": 2,
        "active_alerts": 2, "population": 2065000, "area_sq_km": 7794.0,
        "data_confidence": 0.70,
    },
    {
        "district_name": "Rajkot", "district_code": "RJK",
        "latitude": 22.3039, "longitude": 70.8022,
        "air_score": 48.0, "water_score": 42.0, "noise_score": 52.0,
        "industrial_score": 50.0, "waste_score": 40.0, "overall_score": 47.2,
        "risk_level": "MODERATE", "main_pollutant": "PM10", "main_source": "Engineering + Casting",
        "trend": "stable", "monitored_locations": 5, "high_risk_zones": 1,
        "active_alerts": 1, "population": 1390000, "area_sq_km": 11203.0,
        "data_confidence": 0.65,
    },
    {
        "district_name": "Gandhinagar", "district_code": "GDN",
        "latitude": 23.2156, "longitude": 72.6369,
        "air_score": 38.0, "water_score": 32.0, "noise_score": 35.0,
        "industrial_score": 40.0, "waste_score": 30.0, "overall_score": 36.5,
        "risk_level": "LOW", "main_pollutant": "PM2.5", "main_source": "Urban Traffic",
        "trend": "stable", "monitored_locations": 4, "high_risk_zones": 0,
        "active_alerts": 0, "population": 1387000, "area_sq_km": 1356.0,
        "data_confidence": 0.72,
    },
    {
        "district_name": "Jamnagar", "district_code": "JAM",
        "latitude": 22.4707, "longitude": 70.0577,
        "air_score": 62.0, "water_score": 55.0, "noise_score": 45.0,
        "industrial_score": 72.0, "waste_score": 48.0, "overall_score": 61.5,
        "risk_level": "HIGH", "main_pollutant": "SO2", "main_source": "Refinery Operations",
        "trend": "increasing", "monitored_locations": 4, "high_risk_zones": 2,
        "active_alerts": 3, "population": 920000, "area_sq_km": 14125.0,
        "data_confidence": 0.74,
    },
    {
        "district_name": "Bhavnagar", "district_code": "BHV",
        "latitude": 21.7645, "longitude": 72.1519,
        "air_score": 45.0, "water_score": 50.0, "noise_score": 40.0,
        "industrial_score": 52.0, "waste_score": 42.0, "overall_score": 46.8,
        "risk_level": "MODERATE", "main_pollutant": "Effluents", "main_source": "Ship-breaking + Cement",
        "trend": "stable", "monitored_locations": 3, "high_risk_zones": 1,
        "active_alerts": 1, "population": 977000, "area_sq_km": 11155.0,
        "data_confidence": 0.62,
    },
    {
        "district_name": "Bharuch", "district_code": "BRC",
        "latitude": 21.7051, "longitude": 73.0015,
        "air_score": 72.0, "water_score": 78.0, "noise_score": 48.0,
        "industrial_score": 80.0, "waste_score": 62.0, "overall_score": 73.2,
        "risk_level": "HIGH", "main_pollutant": "Chemical Effluents", "main_source": "Petrochemical + GIDC",
        "trend": "increasing", "monitored_locations": 5, "high_risk_zones": 3,
        "active_alerts": 4, "population": 1551000, "area_sq_km": 6524.0,
        "data_confidence": 0.80,
    },
    {
        "district_name": "Kutch", "district_code": "KCH",
        "latitude": 23.7337, "longitude": 69.8597,
        "air_score": 35.0, "water_score": 38.0, "noise_score": 30.0,
        "industrial_score": 42.0, "waste_score": 32.0, "overall_score": 36.8,
        "risk_level": "LOW", "main_pollutant": "Dust", "main_source": "Mining + Construction",
        "trend": "stable", "monitored_locations": 3, "high_risk_zones": 0,
        "active_alerts": 0, "population": 2092000, "area_sq_km": 45652.0,
        "data_confidence": 0.55,
    },
    {
        "district_name": "Morbi", "district_code": "MRB",
        "latitude": 22.8173, "longitude": 70.8377,
        "air_score": 65.0, "water_score": 58.0, "noise_score": 60.0,
        "industrial_score": 68.0, "waste_score": 55.0, "overall_score": 63.5,
        "risk_level": "HIGH", "main_pollutant": "PM10 + SO2", "main_source": "Ceramic + Clock Industry",
        "trend": "increasing", "monitored_locations": 3, "high_risk_zones": 2,
        "active_alerts": 3, "population": 950000, "area_sq_km": 3620.0,
        "data_confidence": 0.68,
    },
    {
        "district_name": "Patan", "district_code": "PTN",
        "latitude": 23.8500, "longitude": 72.1167,
        "air_score": 32.0, "water_score": 35.0, "noise_score": 28.0,
        "industrial_score": 30.0, "waste_score": 28.0, "overall_score": 31.5,
        "risk_level": "LOW", "main_pollutant": "Dust", "main_source": "Agriculture + Cotton",
        "trend": "stable", "monitored_locations": 2, "high_risk_zones": 0,
        "active_alerts": 0, "population": 1343000, "area_sq_km": 5728.0,
        "data_confidence": 0.50,
    },
    {
        "district_name": "Mehsana", "district_code": "MSN",
        "latitude": 23.5880, "longitude": 72.3693,
        "air_score": 42.0, "water_score": 40.0, "noise_score": 38.0,
        "industrial_score": 45.0, "waste_score": 35.0, "overall_score": 41.5,
        "risk_level": "MODERATE", "main_pollutant": "PM10", "main_source": "Dairy + Engineering",
        "trend": "stable", "monitored_locations": 3, "high_risk_zones": 1,
        "active_alerts": 1, "population": 2027000, "area_sq_km": 2767.0,
        "data_confidence": 0.58,
    },
    {
        "district_name": "Navsari", "district_code": "NVS",
        "latitude": 20.9467, "longitude": 72.9520,
        "air_score": 58.0, "water_score": 62.0, "noise_score": 45.0,
        "industrial_score": 65.0, "waste_score": 50.0, "overall_score": 59.5,
        "risk_level": "MODERATE", "main_pollutant": "Effluents", "main_source": "Sugar + Paper Industry",
        "trend": "stable", "monitored_locations": 3, "high_risk_zones": 1,
        "active_alerts": 2, "population": 1334000, "area_sq_km": 2211.0,
        "data_confidence": 0.65,
    },
]

# ─────────────────────────────────────────────
# Hotspot Data
# ─────────────────────────────────────────────
HOTSPOTS = [
    {
        "name": "Vapi Chemical Complex", "district": "Vapi",
        "latitude": 20.3724, "longitude": 72.9027,
        "pollution_type": "industrial", "severity": "CRITICAL", "severity_score": 91.5,
        "trend": "increasing", "possible_source": "Chemical manufacturing & effluent discharge",
        "explanation": "The Vapi Chemical Zone hosts over 1000 industrial units producing chemicals, pharmaceuticals, and dyes. Groundwater contamination with heavy metals (mercury, chromium) has been documented. SO2 and NOx levels regularly exceed CPCB limits. Effluent discharge into the Damanganga river is a major water pollution driver.",
        "affected_radius": 8.5, "population_affected": 125000, "status": "active",
    },
    {
        "name": "Ankleshwar GIDC", "district": "Ankleshwar",
        "latitude": 21.6263, "longitude": 73.0049,
        "pollution_type": "industrial", "severity": "HIGH", "severity_score": 82.0,
        "trend": "increasing", "possible_source": "Textile dye & pharmaceutical manufacturing",
        "explanation": "Ankleshwar GIDC is one of India's largest industrial estates. Textile dye effluent with high pH (9.8+) and turbidity (55+ NTU) enters Narmada tributaries. Air pollution from chemical units shows elevated SO2 and VOC levels. Repeated non-compliance with effluent treatment norms.",
        "affected_radius": 7.0, "population_affected": 98000, "status": "active",
    },
    {
        "name": "Vatva Industrial Area", "district": "Ahmedabad",
        "latitude": 22.9682, "longitude": 72.6389,
        "pollution_type": "air", "severity": "HIGH", "severity_score": 76.5,
        "trend": "stable", "possible_source": "Pharmaceutical & chemical manufacturing",
        "explanation": "Vatva houses over 2000 industrial units near residential Ahmedabad. PM2.5 levels frequently exceed 150 µg/m³. Pharmaceutical effluents and chemical VOCs create air quality issues. Wind patterns carry pollution toward densely populated areas during evening hours.",
        "affected_radius": 5.0, "population_affected": 350000, "status": "active",
    },
    {
        "name": "Alang Ship Breaking Yard", "district": "Bhavnagar",
        "latitude": 21.4000, "longitude": 72.1500,
        "pollution_type": "water", "severity": "HIGH", "severity_score": 72.0,
        "trend": "stable", "possible_source": "Ship dismantling & hazardous waste",
        "explanation": "Alang is the world's largest ship-breaking yard. Heavy metal contamination (lead, asbestos, PCBs) from ship dismantling enters the coastal marine ecosystem. Oil spills and antifouling paint chemicals affect the intertidal zone. Worker exposure to hazardous materials is a significant health concern.",
        "affected_radius": 12.0, "population_affected": 45000, "status": "active",
    },
    {
        "name": "Jamnagar Refinery Belt", "district": "Jamnagar",
        "latitude": 22.4707, "longitude": 70.0577,
        "pollution_type": "air", "severity": "HIGH", "severity_score": 74.0,
        "trend": "increasing", "possible_source": "Petroleum refining operations",
        "explanation": "The Jamnagar refinery complex (world's largest) produces elevated SO2 (85-120 µg/m³) and NO2 emissions. Hydrogen sulfide incidents have been reported. Flaring operations contribute to VOC and particulate pollution. Coastal marine habitats show hydrocarbon stress.",
        "affected_radius": 15.0, "population_affected": 180000, "status": "active",
    },
    {
        "name": "Naroda Industrial Zone", "district": "Ahmedabad",
        "latitude": 23.0800, "longitude": 72.6600,
        "pollution_type": "air", "severity": "MODERATE", "severity_score": 62.0,
        "trend": "stable", "possible_source": "Mixed manufacturing & auto industry",
        "explanation": "Naroda industrial zone shows elevated PM10 and CO levels from metal casting and automotive component manufacturing. Noise pollution from factory operations affects neighboring residential areas. Groundwater shows trace contaminants from older industrial units.",
        "affected_radius": 3.5, "population_affected": 120000, "status": "active",
    },
    {
        "name": "Morbi Ceramic Cluster", "district": "Morbi",
        "latitude": 22.8173, "longitude": 70.8377,
        "pollution_type": "air", "severity": "HIGH", "severity_score": 71.0,
        "trend": "increasing", "possible_source": "Ceramic kiln emissions",
        "explanation": "Morbi's ceramic industry (world's second largest) operates hundreds of kilns burning coal and gas. PM10 concentrations of 180-250 µg/m³ are recorded during peak production. SO2 from coal combustion exceeds standards. Dust deposition affects agricultural land within 10km radius.",
        "affected_radius": 6.0, "population_affected": 89000, "status": "active",
    },
    {
        "name": "Sabarmati River Belt", "district": "Ahmedabad",
        "latitude": 23.0500, "longitude": 72.5800,
        "pollution_type": "water", "severity": "MODERATE", "severity_score": 58.0,
        "trend": "stable", "possible_source": "Industrial & urban sewage discharge",
        "explanation": "The Sabarmati River receives untreated sewage and industrial effluent from Ahmedabad urban area. BOD levels exceed acceptable limits during dry season. Despite Sabarmati riverfront development, upstream industrial discharge continues. Heavy metals detected in river sediments.",
        "affected_radius": 20.0, "population_affected": 500000, "status": "active",
    },
    {
        "name": "Surat Textile District", "district": "Surat",
        "latitude": 21.2000, "longitude": 72.8400,
        "pollution_type": "water", "severity": "MODERATE", "severity_score": 60.0,
        "trend": "decreasing", "possible_source": "Textile dyeing & processing units",
        "explanation": "Surat's textile processing industry generates large volumes of colored effluent. The Tapi River shows elevated BOD and COD due to textile discharge. Recent CETP (Common Effluent Treatment Plant) improvements have reduced pollution levels. Continued monitoring required.",
        "affected_radius": 5.0, "population_affected": 220000, "status": "active",
    },
    {
        "name": "Bharuch Petrochemical Zone", "district": "Bharuch",
        "latitude": 21.7051, "longitude": 73.0015,
        "pollution_type": "industrial", "severity": "HIGH", "severity_score": 78.0,
        "trend": "increasing", "possible_source": "Petrochemical & fertilizer plants",
        "explanation": "Bharuch hosts major petrochemical and fertilizer industries including ONGC operations. Ammonia and sulfur dioxide emissions frequently exceed permissible limits. The Narmada riverine ecosystem shows stress from chemical discharge. Groundwater contamination with nitrogen compounds documented.",
        "affected_radius": 10.0, "population_affected": 145000, "status": "active",
    },
]

# ─────────────────────────────────────────────
# Citizen Report Samples
# ─────────────────────────────────────────────
CITIZEN_REPORTS = [
    {
        "category": "smoke", "location": "Near Vatva GIDC, Ahmedabad",
        "district": "Ahmedabad", "latitude": 22.9700, "longitude": 72.6400,
        "description": "Black smoke emanating from factory chimney for past 2 hours. Visibility reduced.",
        "severity": "HIGH", "status": "under_review",
    },
    {
        "category": "water", "location": "Vapi Industrial Area, Gate 4",
        "district": "Vapi", "latitude": 20.3750, "longitude": 72.9050,
        "description": "Industrial effluent being discharged directly into nearby canal. Water is blue-green colored.",
        "severity": "CRITICAL", "status": "assigned", "assigned_to": "GPCB Inspector Sharma",
    },
    {
        "category": "garbage", "location": "Near Narol, Ahmedabad",
        "district": "Ahmedabad", "latitude": 22.9600, "longitude": 72.6200,
        "description": "Large garbage dump burning near residential area. Toxic fumes affecting residents.",
        "severity": "HIGH", "status": "submitted",
    },
    {
        "category": "noise", "location": "Morbi Ceramic Zone",
        "district": "Morbi", "latitude": 22.8200, "longitude": 70.8400,
        "description": "Kiln operations running 24/7 with extreme noise levels. Cannot sleep at night.",
        "severity": "MODERATE", "status": "submitted",
    },
    {
        "category": "industrial", "location": "Ankleshwar GIDC Main Road",
        "district": "Ankleshwar", "latitude": 21.6280, "longitude": 73.0070,
        "description": "Chemical smell permeating entire neighborhood. Children coughing.",
        "severity": "HIGH", "status": "under_review",
    },
    {
        "category": "burning", "location": "Surat Vesu Area",
        "district": "Surat", "latitude": 21.1600, "longitude": 72.8100,
        "description": "Waste burning near residential plot. Black smoke visible from 1km.",
        "severity": "MODERATE", "status": "resolved",
        "resolution_note": "Municipal team dispatched. Burning stopped and area cleared.",
    },
    {
        "category": "water", "location": "Sabarmati Riverbank, Ellis Bridge",
        "district": "Ahmedabad", "latitude": 23.0200, "longitude": 72.5700,
        "description": "Industrial foam and discolored water observed in Sabarmati river.",
        "severity": "HIGH", "status": "submitted",
    },
    {
        "category": "smoke", "location": "Jamnagar Refinery Road",
        "district": "Jamnagar", "latitude": 22.4750, "longitude": 70.0600,
        "description": "Unusual flaring at refinery visible at night. Strong sulfur smell.",
        "severity": "HIGH", "status": "submitted",
    },
]


def seed_prithvi_data():
    """Seed all new PRITHVI-X data tables."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        print("Seeding district data...")
        if db.query(DistrictData).count() == 0:
            for d in DISTRICTS:
                district = DistrictData(
                    district_name=d["district_name"],
                    district_code=d["district_code"],
                    latitude=d["latitude"],
                    longitude=d["longitude"],
                    air_score=d["air_score"],
                    water_score=d["water_score"],
                    noise_score=d["noise_score"],
                    industrial_score=d["industrial_score"],
                    waste_score=d["waste_score"],
                    overall_score=d["overall_score"],
                    risk_level=d["risk_level"],
                    main_pollutant=d["main_pollutant"],
                    main_source=d["main_source"],
                    trend=d["trend"],
                    monitored_locations=d["monitored_locations"],
                    high_risk_zones=d["high_risk_zones"],
                    active_alerts=d["active_alerts"],
                    population=d["population"],
                    area_sq_km=d["area_sq_km"],
                    data_source="DEMO/SIMULATED",
                    data_confidence=d["data_confidence"],
                    last_updated=datetime.utcnow(),
                )
                db.add(district)
            db.commit()
            print(f"  Added {len(DISTRICTS)} districts.")
        else:
            print("  District data already seeded.")

        print("Seeding hotspot data...")
        if db.query(Hotspot).count() == 0:
            now = datetime.utcnow()
            for h in HOTSPOTS:
                hotspot = Hotspot(
                    name=h["name"],
                    district=h["district"],
                    latitude=h["latitude"],
                    longitude=h["longitude"],
                    pollution_type=h["pollution_type"],
                    severity=h["severity"],
                    severity_score=h["severity_score"],
                    trend=h["trend"],
                    possible_source=h["possible_source"],
                    explanation=h["explanation"],
                    affected_radius=h["affected_radius"],
                    population_affected=h["population_affected"],
                    detected_at=now - timedelta(days=random.randint(1, 30)),
                    last_updated=now,
                    status=h["status"],
                )
                db.add(hotspot)
            db.commit()
            print(f"  Added {len(HOTSPOTS)} hotspots.")
        else:
            print("  Hotspot data already seeded.")

        print("Seeding citizen reports...")
        if db.query(CitizenReport).count() == 0:
            now = datetime.utcnow()
            for r in CITIZEN_REPORTS:
                report = CitizenReport(
                    category=r["category"],
                    location=r["location"],
                    district=r["district"],
                    latitude=r["latitude"],
                    longitude=r["longitude"],
                    description=r["description"],
                    severity=r["severity"],
                    status=r["status"],
                    assigned_to=r.get("assigned_to"),
                    resolution_note=r.get("resolution_note"),
                    submitted_at=now - timedelta(days=random.randint(0, 7)),
                    updated_at=now - timedelta(hours=random.randint(0, 48)),
                    upvotes=random.randint(0, 15),
                )
                if r["status"] == "resolved":
                    report.resolved_at = now - timedelta(hours=random.randint(1, 24))
                db.add(report)
            db.commit()
            print(f"  Added {len(CITIZEN_REPORTS)} citizen reports.")
        else:
            print("  Citizen reports already seeded.")

        print("Seeding Gujarat Pollution Index...")
        if db.query(GujaratPollutionIndex).count() == 0:
            base_scores = [58.2, 56.9, 57.4, 55.8, 57.1, 56.4, 58.0, 57.3, 56.1, 55.5, 56.8, 57.6, 56.4]
            now = datetime.utcnow()
            for i, score in enumerate(base_scores):
                idx = GujaratPollutionIndex(
                    recorded_at=now - timedelta(days=len(base_scores) - i),
                    overall_score=score,
                    risk_category="POOR" if score > 55 else "MODERATE",
                    air_score=score * 1.1,
                    water_score=score * 0.9,
                    noise_score=score * 0.82,
                    industrial_score=score * 1.2,
                    waste_score=score * 0.78,
                    major_pollutant_type="industrial",
                    most_affected_district="Vapi",
                    change_from_previous=round(random.uniform(-3, 3), 1),
                    monitored_locations=47,
                    high_risk_zones=8,
                    active_alerts=12,
                    health_interpretation="Moderate to poor conditions in industrial zones. General public should monitor exposure.",
                    data_coverage_pct=62.0,
                    data_source="DEMO/SIMULATED",
                )
                db.add(idx)
            db.commit()
            print(f"  Added {len(base_scores)} pollution index records.")
        else:
            print("  Pollution index already seeded.")

        print("[OK] PRITHVI-X seed data complete.")

    except Exception as e:
        print(f"[ERROR] Seeding PRITHVI-X data: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_prithvi_data()
