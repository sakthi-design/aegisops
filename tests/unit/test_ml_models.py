"""
Unit and Integration tests for AegisOps Trained Machine Learning Models.
Validates AegisLogNet, AegisRCA-Pro, AegisTriage-Rank, and AegisKnowledgeIndex.
"""
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.ml.inference_engine import predictor

client = TestClient(app)

def test_ml_models_loaded():
    metrics = predictor.get_metrics()
    assert metrics is not None
    assert "log_anomaly_model" in metrics
    assert "rca_classifier" in metrics
    assert "severity_ranker" in metrics
    assert "knowledge_index" in metrics

def test_log_anomaly_prediction_anomaly():
    res = predictor.predict_log("HikariCP pool saturation: ActiveConnections=100/100, connection acquire timeout after 30000ms")
    assert res["is_anomaly"] is True
    assert res["anomaly_score"] >= 0.5
    assert res["risk_tier"] in ["HIGH", "CRITICAL"]

def test_log_anomaly_prediction_normal():
    res = predictor.predict_log("10.0.1.4 - - [25/Sep/2026:14:02:10 +0000] \"GET /healthz HTTP/1.1\" 200 45")
    assert res["is_anomaly"] is False
    assert res["anomaly_score"] < 0.5
    assert res["risk_tier"] in ["NORMAL", "ELEVATED"]

def test_rca_root_cause_prediction():
    res = predictor.predict_rca("PostgreSQL database connection pool exhausted due to unindexed slow query on orders table.")
    assert "primary_cause" in res
    assert "top_hypotheses" in res
    assert len(res["top_hypotheses"]) == 3
    assert res["primary_confidence"] > 0
    assert "recommended_mitigation" in res

def test_severity_prediction():
    res = predictor.predict_severity("Complete production checkout outage. All payment transactions failing globally with 503.")
    assert res["predicted_severity"] in ["P0", "P1"]
    assert "severity_distribution" in res

def test_precedent_retrieval():
    res = predictor.query_precedents("BGP route leak cloudflare prefix filters", top_k=2)
    assert isinstance(res, list)
    assert len(res) > 0
    assert "similarity_score" in res[0]

def test_api_ml_endpoints():
    # Metrics
    r_metrics = client.get("/api/ml/metrics")
    assert r_metrics.status_code == 200
    assert "models" in r_metrics.json()

    # Log Predict
    r_log = client.post("/api/ml/predict-log", json={
        "log_message": "CRITICAL: database deadlock detected on account ledger"
    })
    assert r_log.status_code == 200
    assert r_log.json()["is_anomaly"] is True

    # RCA Predict
    r_rca = client.post("/api/ml/predict-rca", json={
        "incident_text": "BGP route leak from core transit provider advertised internal private IP space"
    })
    assert r_rca.status_code == 200
    assert r_rca.json()["primary_cause"] == "network_and_routing_failure"

    # Severity Predict
    r_sev = client.post("/api/ml/predict-severity", json={
        "incident_text": "Minor UI alignment glitch on profile page"
    })
    assert r_sev.status_code == 200
    assert "predicted_severity" in r_sev.json()
