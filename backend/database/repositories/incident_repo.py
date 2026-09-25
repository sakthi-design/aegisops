"""
Incident Repository for Database Access.
"""
from typing import List, Optional, Dict, Any
import json
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from backend.database.schema import IncidentModel, RawEvidenceModel, EventModel, AuditLogModel
from backend.models.incident import IncidentResponse, IncidentMetrics, SeverityLevel, IncidentStatus
from backend.pipeline.state import PipelineState

class IncidentRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_incident(self, incident_id: str, title: str, description: str = "", created_by: str = "system") -> IncidentModel:
        existing = self.get_incident(incident_id)
        if existing:
            existing.title = title
            existing.description = description
            self.db.commit()
            return existing

        incident = IncidentModel(
            id=incident_id,
            title=title,
            description=description,
            status=IncidentStatus.NEW.value,
            severity=SeverityLevel.UNCLASSIFIED.value,
            created_by=created_by,
            metrics_json=json.dumps(IncidentMetrics().model_dump())
        )
        self.db.add(incident)
        self.db.commit()
        self.db.refresh(incident)
        return incident

    def get_incident(self, incident_id: str) -> Optional[IncidentModel]:
        return self.db.query(IncidentModel).filter(IncidentModel.id == incident_id).first()

    def list_incidents(self) -> List[IncidentModel]:
        return self.db.query(IncidentModel).order_by(IncidentModel.created_at.desc()).all()

    def save_pipeline_state(self, state: PipelineState) -> IncidentModel:
        inc = self.get_incident(state.incident_id)
        if not inc:
            inc = self.create_incident(state.incident_id, state.title)

        inc.status = state.status.value
        inc.severity = state.severity.value
        inc.metrics_json = json.dumps(state.metrics.model_dump())
        inc.report_json = json.dumps(state.final_report) if state.final_report else None
        inc.evidence_graph_json = json.dumps(state.evidence_graph) if state.evidence_graph else None
        inc.audit_passed = state.audit_result.audit_passed if state.audit_result else True
        inc.reviewer_notes = state.reviewer_notes
        inc.updated_at = datetime.now(timezone.utc)

        # Clear and repopulate events with bulk batching for maximum speed
        self.db.query(EventModel).filter(EventModel.incident_id == inc.id).delete()
        evt_models = [
            EventModel(
                id=f"{inc.id}_{idx}_{e.event_id}",
                incident_id=inc.id,
                timestamp_utc=e.timestamp_utc,
                epoch_timestamp=e.epoch_timestamp,
                source_channel=e.source_channel,
                actor=e.actor,
                service_affected=e.service_affected,
                action_summary=e.action_summary,
                raw_evidence_quote=e.raw_evidence_quote,
                severity=e.severity,
                phase=e.phase,
                confidence=e.confidence,
                cluster_id=e.cluster_id
            )
            for idx, e in enumerate(state.sorted_events)
        ]
        if evt_models:
            self.db.bulk_save_objects(evt_models)

        # Save audit logs
        for idx, log in enumerate(state.audit_trail):
            log_model = AuditLogModel(
                id=f"{inc.id}_{idx}_{log.id}",
                incident_id=inc.id,
                timestamp_utc=log.timestamp_utc,
                user_or_agent=log.user_or_agent,
                action=log.action,
                details_json=json.dumps(log.details)
            )
            self.db.merge(log_model)

        self.db.commit()
        self.db.refresh(inc)
        return inc

    def add_raw_evidence(
        self,
        incident_id: str,
        source_id: str,
        filename: str,
        source_type: str,
        content_hash: str,
        raw_content: str,
        sanitized_content: str = "",
        redaction_count: int = 0
    ) -> RawEvidenceModel:
        ev_id = f"{incident_id}_{source_id}"
        existing = self.db.query(RawEvidenceModel).filter(RawEvidenceModel.id == ev_id).first()
        if existing:
            existing.raw_content = raw_content
            existing.content_hash = content_hash
            self.db.commit()
            return existing

        ev = RawEvidenceModel(
            id=ev_id,
            incident_id=incident_id,
            source_type=source_type,
            filename=filename,
            content_hash=content_hash,
            raw_content=raw_content,
            sanitized_content=sanitized_content,
            redaction_count=redaction_count
        )
        self.db.add(ev)
        self.db.commit()
        return ev

    def delete_incident(self, incident_id: str) -> bool:
        inc = self.get_incident(incident_id)
        if not inc:
            return False
        self.db.query(EventModel).filter(EventModel.incident_id == incident_id).delete()
        self.db.query(RawEvidenceModel).filter(RawEvidenceModel.incident_id == incident_id).delete()
        self.db.query(AuditLogModel).filter(AuditLogModel.incident_id == incident_id).delete()
        self.db.delete(inc)
        self.db.commit()
        return True

    def clear_all_incidents(self) -> int:
        count = self.db.query(IncidentModel).count()
        self.db.query(EventModel).delete()
        self.db.query(RawEvidenceModel).delete()
        self.db.query(AuditLogModel).delete()
        self.db.query(IncidentModel).delete()
        self.db.commit()
        return count
