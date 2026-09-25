"""
SQLAlchemy Database Schema for Enterprise Persistence.
Supports SQLite and PostgreSQL.
"""
from datetime import datetime, timezone
import json
from sqlalchemy import Column, String, Integer, Float, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class IncidentModel(Base):
    __tablename__ = "incidents"

    id = Column(String(64), primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(32), default="NEW", index=True)
    severity = Column(String(16), default="UNCLASSIFIED", index=True)
    created_by = Column(String(64), default="system")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Serialized JSON Metrics
    metrics_json = Column(Text, nullable=True)
    report_json = Column(Text, nullable=True)
    evidence_graph_json = Column(Text, nullable=True)
    reviewer_notes = Column(Text, nullable=True)
    audit_passed = Column(Boolean, default=True)

    events = relationship("EventModel", back_populates="incident", cascade="all, delete-orphan")
    raw_evidence = relationship("RawEvidenceModel", back_populates="incident", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLogModel", back_populates="incident", cascade="all, delete-orphan")

class RawEvidenceModel(Base):
    __tablename__ = "raw_evidence"

    id = Column(String(64), primary_key=True)
    incident_id = Column(String(64), ForeignKey("incidents.id"), index=True)
    source_type = Column(String(64), nullable=False)
    filename = Column(String(255), nullable=False)
    content_hash = Column(String(64), nullable=False)
    raw_content = Column(Text, nullable=False)
    sanitized_content = Column(Text, nullable=True)
    redaction_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    incident = relationship("IncidentModel", back_populates="raw_evidence")

class EventModel(Base):
    __tablename__ = "events"

    id = Column(String(64), primary_key=True)
    incident_id = Column(String(64), ForeignKey("incidents.id"), index=True)
    timestamp_utc = Column(String(64), nullable=False, index=True)
    epoch_timestamp = Column(Float, default=0.0, index=True)
    source_channel = Column(String(64), nullable=False)
    actor = Column(String(64), default="system")
    service_affected = Column(String(128), default="unspecified")
    action_summary = Column(Text, nullable=False)
    raw_evidence_quote = Column(Text, nullable=False)
    severity = Column(String(32), default="info")
    phase = Column(String(32), default="Triage")
    confidence = Column(Float, default=1.0)
    cluster_id = Column(String(64), nullable=True)

    incident = relationship("IncidentModel", back_populates="events")

class AuditLogModel(Base):
    __tablename__ = "audit_logs"

    id = Column(String(64), primary_key=True)
    incident_id = Column(String(64), ForeignKey("incidents.id"), index=True)
    timestamp_utc = Column(String(64), nullable=False)
    user_or_agent = Column(String(64), nullable=False)
    action = Column(String(64), nullable=False)
    details_json = Column(Text, nullable=True)

    incident = relationship("IncidentModel", back_populates="audit_logs")
