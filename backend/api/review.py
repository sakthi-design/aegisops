"""
Review & Audit API Router.
Provides Human-in-the-Loop approvals, edits, regeneration triggers, and enterprise audit logs.
"""
from typing import Dict, Any, Optional
import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from backend.database.session import get_db
from backend.database.repositories.incident_repo import IncidentRepository
from backend.database.schema import AuditLogModel
from backend.api.incidents import ACTIVE_PIPELINES, orchestrator
from backend.models.incident import IncidentStatus

router = APIRouter(prefix="/incidents", tags=["Review & Audit"])

@router.post("/{incident_id}/review")
def submit_human_review(
    incident_id: str,
    action: str = Body(..., embed=True),  # "APPROVE", "REJECT", "EDIT", "FLAG"
    notes: Optional[str] = Body(default="", embed=True),
    reviewer: str = Body(default="SRE Commander", embed=True),
    db: Session = Depends(get_db)
):
    repo = IncidentRepository(db)
    model = repo.get_incident(incident_id)
    if not model:
        raise HTTPException(status_code=404, detail="Incident not found")

    action_upper = action.upper()
    if action_upper == "APPROVE":
        model.status = IncidentStatus.APPROVED.value
    elif action_upper == "REJECT":
        model.status = IncidentStatus.REJECTED.value
    elif action_upper == "FLAG":
        model.status = IncidentStatus.AWAITING_REVIEW.value
    elif action_upper == "EDIT":
        model.status = IncidentStatus.APPROVED.value

    model.reviewer_notes = notes
    model.updated_at = datetime.now(timezone.utc)

    # Log human review action into enterprise audit trail
    log = AuditLogModel(
        id=f"AUD-REV-{datetime.now(timezone.utc).strftime('%H%M%S')}",
        incident_id=incident_id,
        timestamp_utc=datetime.now(timezone.utc).isoformat(),
        user_or_agent=reviewer,
        action=f"HUMAN_REVIEW_{action_upper}",
        details_json=json.dumps({"notes": notes, "action": action_upper})
    )
    db.add(log)
    db.commit()

    # Update memory state if active
    state = ACTIVE_PIPELINES.get(incident_id)
    if state:
        state.status = IncidentStatus(model.status)
        state.reviewer_notes = notes

    return {
        "status": "success",
        "incident_id": incident_id,
        "new_incident_status": model.status,
        "action": action_upper,
        "notes": notes
    }

@router.post("/{incident_id}/regenerate")
def trigger_regeneration(
    incident_id: str,
    feedback: str = Body(default="Human requested regeneration with revised constraints", embed=True),
    db: Session = Depends(get_db)
):
    repo = IncidentRepository(db)
    model = repo.get_incident(incident_id)
    if not model:
        raise HTTPException(status_code=404, detail="Incident not found")

    state = ACTIVE_PIPELINES.get(incident_id)
    if not state:
        raise HTTPException(status_code=400, detail="Incident pipeline state not loaded in memory")

    state.status = IncidentStatus.REGENERATING
    state.retry_count = 0
    state.reviewer_notes = f"Regeneration triggered: {feedback}"
    
    # Re-run pipeline with feedback
    processed_state = orchestrator.run_pipeline(state)
    ACTIVE_PIPELINES[incident_id] = processed_state
    repo.save_pipeline_state(processed_state)

    return {
        "status": "success",
        "incident_id": incident_id,
        "incident_status": processed_state.status.value,
        "retry_count": processed_state.retry_count,
        "rca_root_cause": processed_state.rca_result.root_cause if processed_state.rca_result else None
    }

@router.get("/{incident_id}/audit")
def get_audit_trail(incident_id: str, db: Session = Depends(get_db)):
    repo = IncidentRepository(db)
    model = repo.get_incident(incident_id)
    if not model:
        raise HTTPException(status_code=404, detail="Incident not found")

    logs = db.query(AuditLogModel).filter(AuditLogModel.incident_id == incident_id).order_by(AuditLogModel.timestamp_utc.asc()).all()
    
    return {
        "incident_id": incident_id,
        "audit_logs": [
            {
                "id": l.id,
                "timestamp_utc": l.timestamp_utc,
                "actor": l.user_or_agent,
                "action": l.action,
                "details": json.loads(l.details_json) if l.details_json else {}
            } for l in logs
        ]
    }
