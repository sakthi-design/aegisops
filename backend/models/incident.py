"""
Domain models and Pydantic v2 schemas for Incidents.
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class SeverityLevel(str, Enum):
    P0 = "P0"  # Critical Outage
    P1 = "P1"  # High Impact
    P2 = "P2"  # Medium Impact
    P3 = "P3"  # Low Impact
    UNCLASSIFIED = "UNCLASSIFIED"

class IncidentStatus(str, Enum):
    NEW = "NEW"
    INGESTING = "INGESTING"
    SANITIZING = "SANITIZING"
    EXTRACTING = "EXTRACTING"
    REASONING = "REASONING"
    SYNTHESIZING = "SYNTHESIZING"
    VERIFYING = "VERIFYING"
    AWAITING_REVIEW = "AWAITING_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    REGENERATING = "REGENERATING"

class IncidentPhase(str, Enum):
    DETECTION = "Detection"
    TRIAGE = "Triage"
    MITIGATION = "Mitigation"
    RESOLUTION = "Resolution"
    POST_INCIDENT = "Post-Incident"
    UNKNOWN = "Unknown"

class IncidentBase(BaseModel):
    title: str = Field(..., description="Descriptive title of the incident")
    description: Optional[str] = None
    created_by: str = Field(default="system", description="Author or system triggering the incident")

class IncidentCreate(IncidentBase):
    pass

class IncidentMetrics(BaseModel):
    start_time_utc: Optional[str] = None
    detection_time_utc: Optional[str] = None
    mitigation_time_utc: Optional[str] = None
    resolution_time_utc: Optional[str] = None
    mttd_seconds: Optional[float] = None
    mttd_formatted: Optional[str] = None
    mttr_seconds: Optional[float] = None
    mttr_formatted: Optional[str] = None
    total_duration_seconds: Optional[float] = None
    total_duration_formatted: Optional[str] = None
    total_duration_minutes: Optional[float] = None
    records_count: int = 0
    # Data Science & Incident Intelligence Profiling
    critical_alerts_count: int = 0
    high_alerts_count: int = 0
    total_alerts_count: int = 0
    sla_met_count: int = 0
    sla_breached_count: int = 0
    sla_breach_rate_pct: float = 0.0
    p50_mttr_formatted: Optional[str] = None
    p95_mttr_formatted: Optional[str] = None
    top_failure_categories: List[Dict[str, Any]] = Field(default_factory=list)
    statistical_profile: Optional[Dict[str, Any]] = None

class IncidentResponse(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    status: IncidentStatus
    severity: SeverityLevel
    created_at: str
    updated_at: str
    metrics: IncidentMetrics
    source_count: int = 0
    event_count: int = 0
    conflict_count: int = 0
    audit_passed: Optional[bool] = None
    reviewer_notes: Optional[str] = None
