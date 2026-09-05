"""API route: /api/agents — triggers the multi-agent pipeline."""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from models.database import AgentLog, get_db
from models.schemas import AgentProcessIn, AgentContextOut
from agents.supervisor.agent import supervisor_agent

router = APIRouter()


@router.post("/process", response_model=AgentContextOut)
def run_agent_pipeline(body: AgentProcessIn, db: Session = Depends(get_db)):
    context = body.model_dump()
    if not context.get("event_id"):
        context["event_id"] = f"EVT-{uuid.uuid4().hex[:8].upper()}"
    if not context.get("timestamp"):
        context["timestamp"] = datetime.utcnow().isoformat()

    result = supervisor_agent.process(context)

    # Persist log
    db.add(AgentLog(
        agent_name="SupervisorAgent",
        action="pipeline_run",
        input_summary=(
            f"factory={body.factory_id} param={body.parameter} value={body.value}"
        ),
        output_summary=(
            f"alert_level={result.get('alert_level')} "
            f"status={result.get('current_status')} "
            f"assessment={result.get('combined_assessment', '')[:120]}"
        ),
    ))
    db.commit()

    return AgentContextOut(**result)
