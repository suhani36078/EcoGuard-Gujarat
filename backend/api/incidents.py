"""API route: /api/incidents"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from models.database import Incident, AgentLog, get_db
from models.schemas import IncidentOut, IncidentActionIn

router = APIRouter()


@router.get("", response_model=List[IncidentOut])
def list_incidents(
    status: Optional[str] = Query(default=None),
    severity: Optional[str] = Query(default=None),
    limit: int = Query(default=100, le=500),
    db: Session = Depends(get_db),
):
    q = db.query(Incident)
    if status:
        q = q.filter(Incident.status == status.lower())
    if severity:
        q = q.filter(Incident.severity == severity.upper())
    return q.order_by(Incident.created_at.desc()).limit(limit).all()


@router.get("/{incident_id}", response_model=IncidentOut)
def get_incident(incident_id: int, db: Session = Depends(get_db)):
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@router.post("/{incident_id}/action")
def incident_action(
    incident_id: int,
    body: IncidentActionIn,
    db: Session = Depends(get_db),
):
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    action = body.action.lower()
    if action == "resolve":
        incident.status = "resolved"
        incident.resolved_at = datetime.utcnow()
    elif action == "assign":
        incident.assigned_to = body.assigned_to or incident.assigned_to
    elif action == "escalate":
        incident.status = "escalated"
    elif action == "add_note":
        note = body.note or ""
        incident.description = (incident.description or "") + f"\n\n[{body.performed_by}] {note}"

    db.commit()

    # Log the action
    db.add(AgentLog(
        agent_name="HumanOfficer",
        action=action,
        input_summary=f"Incident #{incident_id} — {body.action}",
        output_summary=f"Performed by {body.performed_by}. Note: {body.note or '—'}",
    ))
    db.commit()

    return {"message": f"Action '{action}' applied to incident {incident_id}"}
