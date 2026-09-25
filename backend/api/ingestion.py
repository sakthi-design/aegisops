"""
Ingestion API Router.
Handles file uploads and direct API/webhook payloads.
"""
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Body
from sqlalchemy.orm import Session
from backend.database.session import get_db
from backend.database.repositories.incident_repo import IncidentRepository
from backend.ingestion.file_ingestor import FileIngestor
from backend.api.incidents import ACTIVE_PIPELINES
from backend.pipeline.state import PipelineState
from backend.models.incident import IncidentStatus

router = APIRouter(prefix="/incidents", tags=["Ingestion"])

@router.post("/{incident_id}/ingest", response_model=Dict[str, Any])
async def ingest_file(
    incident_id: str,
    file: UploadFile = File(None),
    raw_text: str = Form(None),
    source_type: str = Form(None),
    auto_analyze: bool = Form(True),
    db: Session = Depends(get_db)
):
    from backend.api.incidents import orchestrator, ACTIVE_PIPELINES

    repo = IncidentRepository(db)
    model = repo.get_incident(incident_id)
    if not model:
        raise HTTPException(status_code=404, detail="Incident not found")

    content = ""
    filename = "telemetry.txt"

    if file:
        filename = file.filename or "upload.txt"
        file_bytes = await file.read()
        content = file_bytes.decode("utf-8", errors="ignore")
    elif raw_text:
        content = raw_text
        filename = f"{source_type or 'telemetry'}.txt"
    else:
        raise HTTPException(status_code=400, detail="Must provide file upload or raw_text")

    # Ingestion Gateway
    ingest_result = FileIngestor.ingest(content, filename=filename)
    if source_type and source_type != "auto":
        ingest_result.source_type = source_type

    # Save to DB
    repo.add_raw_evidence(
        incident_id=incident_id,
        source_id=ingest_result.source_id,
        filename=ingest_result.filename,
        source_type=ingest_result.source_type,
        content_hash=ingest_result.content_hash,
        raw_content=content
    )

    # Reconstruct or update pipeline state directly from DB evidence
    model = repo.get_incident(incident_id)
    state = PipelineState(
        incident_id=incident_id,
        title=model.title,
        status=IncidentStatus(model.status)
    )
    for ev in model.raw_evidence:
        state.raw_inputs.append({
            "source_id": ev.id,
            "source_type": ev.source_type,
            "filename": ev.filename,
            "content": ev.raw_content
        })
    ACTIVE_PIPELINES[incident_id] = state

    auto_analysis_data = None
    if auto_analyze:
        # Execute deterministic + agentic synthesis pipeline automatically
        processed_state = orchestrator.run_pipeline(state)
        ACTIVE_PIPELINES[incident_id] = processed_state
        repo.save_pipeline_state(processed_state)
        auto_analysis_data = {
            "status": processed_state.status.value,
            "severity": processed_state.severity.value,
            "events_count": len(processed_state.sorted_events),
            "clusters_count": len(processed_state.event_clusters),
            "conflicts_count": len(processed_state.conflicts),
            "audit_passed": processed_state.audit_result.audit_passed if processed_state.audit_result else True,
            "metrics": processed_state.metrics.model_dump() if processed_state.metrics else {},
            "rca_summary": processed_state.rca_result.root_cause if processed_state.rca_result else None
        }

    return {
        "status": "success",
        "incident_id": incident_id,
        "source_id": ingest_result.source_id,
        "detected_source_type": ingest_result.source_type,
        "content_hash": ingest_result.content_hash,
        "records_count": ingest_result.total_records_count,
        "auto_analyzed": auto_analyze,
        "analysis": auto_analysis_data
    }


@router.post("/upload-and-analyze", response_model=Dict[str, Any])
async def upload_and_analyze(
    incident_id: str = Form(None),
    title: str = Form(None),
    file: UploadFile = File(...),
    source_type: str = Form(None),
    db: Session = Depends(get_db)
):
    """Direct one-step file upload and automated end-to-end pipeline analysis."""
    import uuid
    from backend.api.incidents import orchestrator, ACTIVE_PIPELINES

    repo = IncidentRepository(db)
    filename = file.filename or "telemetry.txt"
    file_bytes = await file.read()
    content = file_bytes.decode("utf-8", errors="ignore")

    # If no incident_id or incident not found, auto-create one
    target_id = incident_id
    model = repo.get_incident(target_id) if target_id else None
    if not model:
        target_id = f"INC-{uuid.uuid4().hex[:8].upper()}"
        inc_title = title or f"Incident: {filename}"
        model = repo.create_incident(
            incident_id=target_id,
            title=inc_title,
            description=f"Auto-generated container for uploaded telemetry: {filename}",
            created_by="Automated File Ingestor"
        )

    # Ingestion Gateway
    ingest_result = FileIngestor.ingest(content, filename=filename)
    if source_type and source_type != "auto":
        ingest_result.source_type = source_type

    repo.add_raw_evidence(
        incident_id=target_id,
        source_id=ingest_result.source_id,
        filename=ingest_result.filename,
        source_type=ingest_result.source_type,
        content_hash=ingest_result.content_hash,
        raw_content=content
    )

    # Reconstruct pipeline state cleanly from DB evidence to prevent duplicate inputs
    model = repo.get_incident(target_id)
    state = PipelineState(
        incident_id=target_id,
        title=model.title,
        status=IncidentStatus(model.status)
    )
    for ev in model.raw_evidence:
        state.raw_inputs.append({
            "source_id": ev.id,
            "source_type": ev.source_type,
            "filename": ev.filename,
            "content": ev.raw_content
        })
    ACTIVE_PIPELINES[target_id] = state

    # Execute full automated analysis pipeline
    processed_state = orchestrator.run_pipeline(state)
    ACTIVE_PIPELINES[target_id] = processed_state
    repo.save_pipeline_state(processed_state)

    exact_count = max(ingest_result.total_records_count, processed_state.metrics.records_count, len(processed_state.sorted_events))
    return {
        "status": "success",
        "incident_id": target_id,
        "title": model.title,
        "filename": filename,
        "records_count": exact_count,
        "events_count": exact_count,
        "milestones_count": len(processed_state.sorted_events),
        "severity": processed_state.severity.value,
        "incident_status": processed_state.status.value,
        "metrics": processed_state.metrics.model_dump() if processed_state.metrics else {},
        "rca_summary": processed_state.rca_result.root_cause if processed_state.rca_result else None
    }
