"""
Full Integration Tests for FastAPI Endpoints.
Tests incident creation, multi-source file ingestion, processing,
timeline queries, RCA, Human-in-the-Loop review, and export formats.
"""
import pytest
from fastapi.testclient import TestClient
from backend.main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_health_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "knowledge_base" in data

def test_incident_lifecycle(client):
    # 1. Create incident
    create_res = client.post("/api/incidents", json={
        "title": "Integration Test Checkout Failure",
        "description": "Integration testing incident flow",
        "created_by": "PyTest Suite"
    })
    assert create_res.status_code == 200
    inc_data = create_res.json()
    inc_id = inc_data["id"]

    # 2. Ingest telemetry
    ingest_res = client.post(
        f"/api/incidents/{inc_id}/ingest",
        data={"raw_text": "2026-09-25T14:00:00Z [ERROR] payment-processor: Connection pool 82% saturated\n2026-09-25T14:15:00Z [INFO] payment-processor: Rollback completed"}
    )
    assert ingest_res.status_code == 200
    assert ingest_res.json()["status"] == "success"

    # 3. Process Incident
    proc_res = client.post(f"/api/incidents/{inc_id}/process")
    assert proc_res.status_code == 200
    proc_data = proc_res.json()
    assert proc_data["events_count"] >= 2
    assert proc_data["status"] == "AWAITING_REVIEW"

    # 4. Get Timeline
    tl_res = client.get(f"/api/incidents/{inc_id}/timeline")
    assert tl_res.status_code == 200
    assert len(tl_res.json()["events"]) >= 2

    # 5. Get RCA
    rca_res = client.get(f"/api/incidents/{inc_id}/rca")
    assert rca_res.status_code == 200
    assert "root_cause" in rca_res.json()["rca"]

    # 6. Human Review Approval
    rev_res = client.post(f"/api/incidents/{inc_id}/review", json={
        "action": "APPROVE",
        "notes": "Verified by SRE Lead",
        "reviewer": "Alex Morgan"
    })
    assert rev_res.status_code == 200
    assert rev_res.json()["new_incident_status"] == "APPROVED"

    # 7. Exports
    md_res = client.get(f"/api/incidents/{inc_id}/export/markdown")
    assert md_res.status_code == 200
    assert "# Incident Post-Mortem" in md_res.text

    pdf_res = client.get(f"/api/incidents/{inc_id}/export/pdf")
    assert pdf_res.status_code == 200
    assert pdf_res.headers["content-type"] == "application/pdf"
