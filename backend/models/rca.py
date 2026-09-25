"""
Root Cause Analysis, Blast Radius / Impact, and Action Items schemas.
"""
from typing import List, Optional
from enum import Enum
from pydantic import BaseModel, Field

class ClaimType(str, Enum):
    OBSERVED_FACT = "OBSERVED_FACT"          # Directly backed by explicit log or telemetry
    INFERRED_CONCLUSION = "INFERRED_CONCLUSION" # Deduced from chronological chain of events
    UNRESOLVED_HYPOTHESIS = "UNRESOLVED_HYPOTHESIS" # Suspected but unproven by evidence

class GroundedClaim(BaseModel):
    claim_id: str
    claim_text: str
    claim_type: ClaimType
    confidence_score: float = Field(ge=0.0, le=1.0)
    supporting_event_ids: List[str]
    supporting_evidence_quotes: List[str]

class FiveWhysItem(BaseModel):
    step: int
    why: str
    answer: str
    supporting_event_id: Optional[str] = None
    confidence: float = 1.0

class RCAResult(BaseModel):
    root_cause: str
    is_conclusive: bool = True
    inconclusive_reason: Optional[str] = None
    failure_path: List[str] = Field(default_factory=list)
    five_whys: List[FiveWhysItem] = Field(default_factory=list)
    contributing_factors: List[str] = Field(default_factory=list)
    confidence_score: float = 1.0
    grounded_claims: List[GroundedClaim] = Field(default_factory=list)

class ImpactAnalysis(BaseModel):
    affected_services: List[str] = Field(default_factory=list)
    affected_regions: List[str] = Field(default_factory=list)
    user_impact_summary: str
    failed_requests_estimate: Optional[str] = "Impact metric unavailable from supplied telemetry."
    revenue_impact_estimate: Optional[str] = "Impact metric unavailable from supplied telemetry."
    sla_slo_breached: bool = False
    duration_minutes: float = 0.0

class ActionItemPriority(str, Enum):
    IMMEDIATE = "P0 - Immediate Hotfix"
    SHORT_TERM = "P1 - Short-Term Hardening"
    LONG_TERM = "P2 - Long-Term Architectural Prevention"

class ActionItem(BaseModel):
    task: str
    owner_role: str
    priority: ActionItemPriority
    deadline: str
    success_metric: str
    evidence_basis: List[str] = Field(default_factory=list)

class AuditResult(BaseModel):
    audit_passed: bool
    issue_type: Optional[str] = None
    issue_description: Optional[str] = None
    contradicting_event_id: Optional[str] = None
    checked_claims_count: int = 0
    passed_claims_count: int = 0
