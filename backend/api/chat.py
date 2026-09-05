"""API route: /api/chat — AI Pollution Assistant powered by IBM Granite"""

import uuid
from typing import Optional, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from models.database import ChatMessage, DistrictData, Hotspot, CitizenReport, get_db

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    session_id: str
    user_message: str
    assistant_response: str
    agent_used: Optional[str] = None
    sources: Optional[List[str]] = None


@router.post("/message", response_model=ChatResponse)
def send_message(req: ChatRequest, db: Session = Depends(get_db)):
    session_id = req.session_id or str(uuid.uuid4())

    # Save user message
    user_msg = ChatMessage(
        session_id=session_id,
        role="user",
        content=req.message,
        created_at=datetime.utcnow(),
    )
    db.add(user_msg)

    # Route to appropriate response
    response, agent_used, sources = _generate_response(req.message, db)

    # Save assistant message
    asst_msg = ChatMessage(
        session_id=session_id,
        role="assistant",
        content=response,
        agent_used=agent_used,
        created_at=datetime.utcnow(),
    )
    db.add(asst_msg)
    db.commit()

    return ChatResponse(
        session_id=session_id,
        user_message=req.message,
        assistant_response=response,
        agent_used=agent_used,
        sources=sources,
    )


@router.get("/history/{session_id}")
def get_history(session_id: str, db: Session = Depends(get_db)):
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )
    return [{"role": m.role, "content": m.content, "agent": m.agent_used, "time": m.created_at} for m in messages]


def _generate_response(message: str, db: Session) -> tuple:
    """Intelligent rule-based routing + IBM Granite fallback."""
    msg_lower = message.lower()
    sources = ["PRITHVI-X Platform Database", "Industrial Sensor Network (DEMO)"]

    # Try IBM Granite first
    try:
        from services.granite_service import granite_service
        context = _build_context(msg_lower, db)
        prompt = f"""You are PRITHVI-X, an expert AI assistant for Gujarat Pollution Intelligence Platform.
Answer the following user question about pollution in Gujarat using the available data context.
Be specific, helpful, and always note when data is estimated/simulated vs real.

Context: {context}

User Question: {message}

Provide a clear, concise response in 2-4 sentences. If recommending actions, be practical."""
        response = granite_service.generate(prompt, max_tokens=300)
        if response and len(response.strip()) > 20:
            return response.strip(), "GraniteAI + PollutionAnalyst", sources
    except Exception:
        pass

    # Rule-based fallback
    return _rule_based_response(msg_lower, db), "PollutionAnalyst", sources


def _build_context(msg_lower: str, db: Session) -> str:
    parts = []
    try:
        districts = db.query(DistrictData).order_by(DistrictData.overall_score.desc()).limit(5).all()
        if districts:
            parts.append(f"Top polluted districts: {', '.join(f'{d.district_name}({d.overall_score:.0f})' for d in districts)}")

        hotspots = db.query(Hotspot).filter(Hotspot.status == "active").limit(5).all()
        if hotspots:
            parts.append(f"Active hotspots: {', '.join(f'{h.name}({h.severity})' for h in hotspots)}")

        critical_h = db.query(Hotspot).filter(Hotspot.severity == "CRITICAL").count()
        parts.append(f"Critical hotspots: {critical_h}")

        reports = db.query(CitizenReport).filter(CitizenReport.status == "submitted").count()
        parts.append(f"Pending citizen reports: {reports}")
    except Exception:
        parts.append("Platform data available for Gujarat industrial zones.")
    return ". ".join(parts)


def _rule_based_response(msg: str, db: Session) -> str:
    # Highest pollution city/district
    if any(k in msg for k in ["highest", "most polluted", "worst", "polluted city", "polluted district"]):
        try:
            d = db.query(DistrictData).order_by(DistrictData.overall_score.desc()).first()
            if d:
                return (f"Based on available data, **{d.district_name}** currently has the highest pollution score "
                        f"({d.overall_score:.0f}/100, {d.risk_level} risk). "
                        f"Main contributing factor: {d.main_pollutant or 'industrial emissions'}. "
                        f"Note: This is based on simulated/estimated data, not live government sensors.")
        except Exception:
            pass
        return ("Based on available simulated data, the **Vapi-Ankleshwar industrial belt** shows the highest "
                "pollution levels in Gujarat, driven primarily by chemical and textile industrial activity.")

    # Ahmedabad specific
    if "ahmedabad" in msg:
        return ("**Ahmedabad** shows moderate air pollution levels (AQI estimated 145-180 range) primarily from "
                "vehicular traffic, construction dust, and industrial activity in Vatva. "
                "Residents in Vatva, Naroda, and Odhav areas face higher exposure. "
                "Recommended: Use N95 masks during peak traffic hours. Data: DEMO/ESTIMATED.")

    # Surat specific
    if "surat" in msg:
        return ("**Surat** has moderate-to-high pollution levels due to diamond polishing units, textile dyeing, "
                "and dense traffic. Water pollution from Tapi river industrial discharge is a concern. "
                "Air quality is typically MODERATE (AQI 100-150). Data: DEMO/ESTIMATED.")

    # Hotspots
    if any(k in msg for k in ["hotspot", "hot spot", "high risk area", "dangerous area"]):
        try:
            hs = db.query(Hotspot).filter(Hotspot.severity.in_(["CRITICAL", "HIGH"])).limit(3).all()
            if hs:
                names = ", ".join(f"{h.name} ({h.district}, {h.pollution_type})" for h in hs)
                return (f"Current high-risk pollution hotspots: {names}. "
                        f"These areas show significantly elevated pollution from industrial sources. "
                        f"Intervention and monitoring are recommended. Data: DEMO/SIMULATED.")
        except Exception:
            pass
        return ("Current major hotspots are concentrated in **Vapi** (chemical), **Ankleshwar** (textile/dye), "
                "and **Vatva** (pharmaceutical/chemical). These industrial zones consistently show elevated "
                "pollutant levels exceeding CPCB norms. Data: DEMO/SIMULATED.")

    # Water pollution
    if any(k in msg for k in ["water", "river", "effluent", "tapi", "sabarmati"]):
        return ("Gujarat's major water pollution concerns include industrial effluent discharge into the "
                "Sabarmati, Tapi, and Narmada rivers. The Vapi chemical zone has historically high groundwater "
                "contamination. Key parameters: pH (9.2-10.1 in some zones), turbidity (>55 NTU), "
                "dissolved chemicals. Data: DEMO/ESTIMATED from industrial monitoring.")

    # What to do / health advice
    if any(k in msg for k in ["what should", "precaution", "protect", "health", "safe", "mask"]):
        return ("During high pollution periods: 1) Wear N95/N99 masks outdoors; "
                "2) Avoid outdoor exercise during 6-10 AM and 6-9 PM; "
                "3) Use air purifiers indoors; 4) Keep windows closed during high industrial activity; "
                "5) Stay hydrated and eat antioxidant-rich foods; "
                "6) Check PRITHVI-X alerts before outdoor activities.")

    # Compare cities
    if "compare" in msg:
        return ("City pollution comparison (DEMO DATA): "
                "Vapi (Industrial Score: 78, CRITICAL) > Ankleshwar (72, HIGH) > "
                "Vatva-Ahmedabad (65, HIGH) > Surat (58, MODERATE) > Vadodara (52, MODERATE) > "
                "Rajkot (45, MODERATE) > Gandhinagar (38, LOW). "
                "Industrial cities consistently show higher pollution than commercial/administrative centers.")

    # Prediction / forecast
    if any(k in msg for k in ["predict", "forecast", "future", "next", "will"]):
        return ("Based on trend analysis of available data, pollution in industrial zones is expected to "
                "remain HIGH in the coming period. Seasonal factors (winter temperature inversions, "
                "monsoon reduction) will influence levels. The Vapi-Ankleshwar belt shows an increasing "
                "industrial activity trend. Prediction confidence: MODERATE. Data: DEMO/MODEL-BASED.")

    # Industrial pollution
    if any(k in msg for k in ["industrial", "factory", "chemical", "emission"]):
        return ("Gujarat's industrial pollution is primarily concentrated in three zones: "
                "1) **Vapi Chemical Zone** — SO2, NOx, chemical effluents; "
                "2) **Ankleshwar Industrial Estate** — textile dyes, pharmaceutical waste; "
                "3) **Vatva (Ahmedabad)** — mixed industrial, pharmaceutical. "
                "These zones collectively account for ~65% of industrial pollution in Gujarat. Data: DEMO/ESTIMATED.")

    # Default response
    return ("I'm PRITHVI-X, Gujarat's pollution intelligence assistant. I can help you with: "
            "current pollution levels, city comparisons, hotspot information, health advice, "
            "industrial pollution data, predictions, and citizen reporting. "
            "What specific information about Gujarat pollution would you like to know?")
