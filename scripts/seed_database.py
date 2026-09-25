"""
Database and Demonstration Seeder.
Creates a realistic enterprise P0 incident with multi-source telemetry:
1. Slack conversations with responder triage and masked secrets
2. Datadog p99 latency & saturation alert JSON
3. Jira incident ticket PAY-9921
4. Microservice application logs with HikariCP exhaustion
5. CI/CD deployment record with commit SHA
Then runs the complete deterministic + multi-agent pipeline and stores results.
"""
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.database.session import SessionLocal, init_db
from backend.database.repositories.incident_repo import IncidentRepository
from backend.pipeline.state import PipelineState
from backend.pipeline.orchestrator import IncidentOrchestrator
from backend.models.incident import IncidentStatus

def seed_demo_incident():
    init_db()
    db = SessionLocal()
    repo = IncidentRepository(db)
    orchestrator = IncidentOrchestrator()

    incident_id = "INC-2026-PAY-882"
    title = "Core Payment Gateway Connection Pool Saturation & HTTP 503 Cascade"
    description = "Critical payment authorization failure impacting checkout transactions across North America and Europe."
    
    print(f"Creating incident {incident_id}...")
    repo.create_incident(incident_id=incident_id, title=title, description=description, created_by="PagerDuty Automation")

    # 1. Multi-source operational evidence
    slack_data = """[2026-09-25T14:02:10Z] @alex (SRE Lead): @channel We are seeing customer checkout errors spiking on payment-processor. Anyone deploy recently?
[2026-09-25T14:03:45Z] @dev_sarah: Yes, we deployed release v2.4.1 (commit d7a8e21) about 12 minutes ago.
[2026-09-25T14:04:20Z] @alex: Contact me on alert email alex.sre@fintech-corp.internal or phone +1-555-019-2834 if needed.
[2026-09-25T14:05:00Z] @marcus (DBA): Checking payments-db-primary. Database CPU is normal but HikariCP pool connections reached 82% capacity and locking.
[2026-09-25T14:20:00Z] @alex: I am executing rollback to release v2.4.0 now to restore service.
[2026-09-25T14:25:30Z] @alex: Rollback completed. Traffic normalizing, error rates back to zero."""

    datadog_data = """{
  "alert_type": "error",
  "event_type": "datadog_monitor_alert",
  "title": "[P0 ALERT] payment-processor p99 latency exceeded 5000ms threshold",
  "timestamp": "2026-09-25T14:01:30Z",
  "service": "payment-processor",
  "tags": ["env:production", "service:payment-processor", "team:payments"],
  "text": "Monitor payment-processor-latency triggered: p99 latency reached 6200ms on ingress-alb-prod. 14.8% error rate observed."
}"""

    jira_data = """{
  "key": "PAY-9921",
  "fields": {
    "issuetype": {"name": "Incident"},
    "summary": "Production Payment Gateway 503 Outage",
    "priority": {"name": "P0"},
    "created": "2026-09-25T14:02:00Z",
    "updated": "2026-09-25T14:26:00Z",
    "description": "Customer payments failing with HTTP 503 Service Unavailable. Engineers verified rollback executed at 14:24:00Z by SRE.",
    "resolution": {"name": "Resolved"}
  }
}"""

    log_data = """2026-09-25 14:00:15 [INFO] payment-processor: Processing normal transaction volume (420 tx/sec)
2026-09-25 14:01:20 [WARN] payment-processor: HikariPool-1 - Connection acquisition time 3200ms exceeds warning threshold
2026-09-25 14:02:05 [ERROR] payment-processor: HikariPool-1 - Connection pool reached 82% capacity. Active: 82/100, pending: 412
2026-09-25 14:02:50 [ERROR] api-gateway-service: Upstream payment-processor returned 503 Service Unavailable on POST /v1/charges
2026-09-25 14:24:10 [INFO] payment-processor: Graceful termination initiated for release v2.4.1
2026-09-25 14:25:00 [INFO] payment-processor: Release v2.4.0 started successfully. Connection pool active: 14/100"""

    cicd_data = """[2026-09-25T13:50:00Z] GitHub Actions workflow 'deploy-production' completed successfully for commit d7a8e21 by author dev_sarah. Artifact: payment-processor:v2.4.1."""

    # Ingest evidence
    sources = [
        ("slack_chat.txt", "slack", slack_data),
        ("datadog_alert.json", "datadog", datadog_data),
        ("jira_ticket.json", "jira", jira_data),
        ("payment_processor.log", "application_log", log_data),
        ("github_deploy.log", "cicd", cicd_data)
    ]

    raw_inputs = []
    for fname, stype, content in sources:
        ev = repo.add_raw_evidence(
            incident_id=incident_id,
            source_id=f"src_{fname.split('.')[0]}",
            filename=fname,
            source_type=stype,
            content_hash=f"hash_{fname}",
            raw_content=content
        )
        raw_inputs.append({
            "source_id": ev.id,
            "source_type": stype,
            "filename": fname,
            "content": content
        })

    # Prepare PipelineState
    state = PipelineState(
        incident_id=incident_id,
        title=title,
        status=IncidentStatus.NEW,
        raw_inputs=raw_inputs
    )

    print("Executing full multi-agent + deterministic synthesis pipeline...")
    processed_state = orchestrator.run_pipeline(state)
    
    # Save to database
    repo.save_pipeline_state(processed_state)
    print("Incident pipeline executed successfully!")
    print(f"- Status: {processed_state.status.value}")
    print(f"- Severity: {processed_state.severity.value}")
    print(f"- Events Extracted: {len(processed_state.sorted_events)}")
    print(f"- Clusters Formed: {len(processed_state.event_clusters)}")
    print(f"- Temporal Conflicts Flagged: {len(processed_state.conflicts)}")
    print(f"- MTTD: {processed_state.metrics.mttd_formatted}")
    print(f"- MTTR: {processed_state.metrics.mttr_formatted}")
    print(f"- Critic Audit Passed: {processed_state.audit_result.audit_passed}")
    print(f"- Root Cause: {processed_state.rca_result.root_cause}")
    db.close()

if __name__ == "__main__":
    seed_demo_incident()
