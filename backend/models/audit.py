"""
Enterprise Audit Trail and Compliance models.
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class RedactionAudit(BaseModel):
    redaction_count: int = 0
    secret_types_found: List[str] = Field(default_factory=list)
    scrubbed_snippets: List[str] = Field(default_factory=list)
    content_sha256: Optional[str] = None
    sanitized_sha256: Optional[str] = None
    hmac_salted_hashes: List[str] = Field(default_factory=list)

class AuditLogEntry(BaseModel):
    id: str
    incident_id: str
    timestamp_utc: str
    user_or_agent: str
    action: str
    input_hash: Optional[str] = None
    model_name: Optional[str] = None
    prompt_version: Optional[str] = None
    validation_status: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
