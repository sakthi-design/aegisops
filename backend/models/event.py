"""
Forensic Event, Event Cluster, and Temporal Conflict schemas.
"""
from typing import Optional, List
from pydantic import BaseModel, Field

class ForensicEvent(BaseModel):
    event_id: str = Field(..., description="Unique event identifier (e.g. EVT-001)")
    timestamp_utc: str = Field(..., description="Normalized ISO 8601 UTC timestamp")
    epoch_timestamp: float = Field(default=0.0, description="Unix timestamp for deterministic sorting")
    source_channel: str = Field(..., description="Source system (e.g. slack, datadog, jira, log)")
    actor: str = Field(default="system", description="Engineer or automated system performing action")
    service_affected: str = Field(default="unspecified", description="Service or component name")
    action_summary: str = Field(..., description="Concise statement of action or observed event")
    raw_evidence_quote: str = Field(..., description="Exact textual evidence citation from ingested data")
    severity: str = Field(default="info", description="Local severity: info, warning, error, critical")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Forensic extraction confidence score")
    phase: str = Field(default="Triage", description="Incident phase: Detection, Triage, Mitigation, Resolution")
    cluster_id: Optional[str] = Field(default=None, description="Assigned event cluster identifier")

class EventCluster(BaseModel):
    cluster_id: str
    cluster_name: str
    description: str
    event_ids: List[str]
    start_time_utc: str
    end_time_utc: str
    primary_service: str

class TemporalConflict(BaseModel):
    conflict_id: str
    event_id_a: str
    event_id_b: str
    source_a: str
    source_b: str
    timestamp_a_utc: str
    timestamp_b_utc: str
    delta_seconds: float
    description: str
    resolution_status: str = Field(default="UNRESOLVED", description="UNRESOLVED, RESOLVED_MANUAL, RESOLVED_AUTO")
