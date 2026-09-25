"""
Pipeline State Schema for Multi-Agent Orchestration.
Maintains state transitions, extracted artifacts, telemetry, and validation audits.
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from backend.models.incident import IncidentResponse, IncidentMetrics, SeverityLevel, IncidentStatus
from backend.models.event import ForensicEvent, EventCluster, TemporalConflict
from backend.models.rca import RCAResult, ImpactAnalysis, ActionItem, AuditResult
from backend.models.audit import RedactionAudit, AuditLogEntry

class PipelineState(BaseModel):
    incident_id: str
    title: str
    status: IncidentStatus = IncidentStatus.NEW
    raw_inputs: List[Dict[str, Any]] = Field(default_factory=list)
    sanitized_inputs: List[Dict[str, Any]] = Field(default_factory=list)
    redaction_audits: List[RedactionAudit] = Field(default_factory=list)
    
    extracted_events: List[ForensicEvent] = Field(default_factory=list)
    sorted_events: List[ForensicEvent] = Field(default_factory=list)
    event_clusters: List[EventCluster] = Field(default_factory=list)
    conflicts: List[TemporalConflict] = Field(default_factory=list)
    
    retrieved_context: List[Dict[str, Any]] = Field(default_factory=list)
    metrics: IncidentMetrics = Field(default_factory=IncidentMetrics)
    severity: SeverityLevel = SeverityLevel.UNCLASSIFIED
    
    rca_result: Optional[RCAResult] = None
    impact_result: Optional[ImpactAnalysis] = None
    action_items: List[ActionItem] = Field(default_factory=list)
    
    draft_report: Optional[Dict[str, Any]] = None
    audit_result: Optional[AuditResult] = None
    evidence_graph: Optional[Dict[str, Any]] = None
    
    retry_count: int = 0
    max_retries: int = 3
    final_report: Optional[Dict[str, Any]] = None
    reviewer_notes: Optional[str] = None
    audit_trail: List[AuditLogEntry] = Field(default_factory=list)
