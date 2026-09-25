"""
REST API endpoints for AegisOps Trained AIOps Machine Learning Models.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from backend.ml.inference_engine import predictor

router = APIRouter(prefix="/ml", tags=["AIOps Machine Learning"])

class LogPredictionRequest(BaseModel):
    log_message: str = Field(..., description="Raw log line or telemetry string to evaluate", json_schema_extra={"example": "HikariCP pool saturation: ActiveConnections=100/100, connection acquire timeout after 30000ms"})

class LogBatchPredictionRequest(BaseModel):
    log_messages: List[str] = Field(..., description="List of raw log lines to evaluate simultaneously in vectorized mode", min_length=1)

class IncidentPredictionRequest(BaseModel):
    incident_text: str = Field(..., description="Incident description, failure summary, or alert symptoms", json_schema_extra={"example": "PostgreSQL database queries locked on transactions table, causing 503 gateway timeouts during checkout."})

class PrecedentSearchRequest(BaseModel):
    query: str = Field(..., description="Query to match against 250+ historical post-mortems and SRE runbooks", json_schema_extra={"example": "BGP route leak cloudflare prefix filters"})
    top_k: int = Field(3, ge=1, le=10, description="Number of historical incidents to retrieve")

@router.get("/metrics", summary="Get Trained Models Performance Metrics")
def get_model_metrics() -> Dict[str, Any]:
    metrics = predictor.get_metrics()
    if not metrics:
        raise HTTPException(status_code=404, detail="Training metrics not found. Please run training pipeline.")
    return {
        "status": "active",
        "models": metrics
    }

@router.post("/predict-log", summary="Predict Log Anomaly (AegisLogNet)")
def predict_log_anomaly(req: LogPredictionRequest) -> Dict[str, Any]:
    res = predictor.predict_log(req.log_message)
    if "error" in res:
        raise HTTPException(status_code=500, detail=res["error"])
    return res

@router.post("/predict-log-batch", summary="Vectorized Batch Log Anomaly Prediction (AegisLogNet)")
def predict_log_batch_anomaly(req: LogBatchPredictionRequest) -> Dict[str, Any]:
    results = predictor.predict_log_batch(req.log_messages)
    anomalies_count = sum(1 for r in results if r.get("is_anomaly"))
    return {
        "total_evaluated": len(results),
        "anomalies_detected": anomalies_count,
        "anomaly_rate": round(anomalies_count / max(len(results), 1), 4),
        "results": results
    }

@router.post("/predict-rca", summary="Predict Root Cause Category (AegisRCA-Pro)")
def predict_rca_root_cause(req: IncidentPredictionRequest) -> Dict[str, Any]:
    res = predictor.predict_rca(req.incident_text)
    if "error" in res:
        raise HTTPException(status_code=500, detail=res["error"])
    return res

@router.post("/predict-severity", summary="Predict Incident Severity (AegisTriage-Rank)")
def predict_severity(req: IncidentPredictionRequest) -> Dict[str, Any]:
    res = predictor.predict_severity(req.incident_text)
    if "error" in res:
        raise HTTPException(status_code=500, detail=res["error"])
    return res

@router.post("/query-precedents", summary="Search Historical Outages & Runbooks (AegisKnowledgeIndex)")
def search_precedents(req: PrecedentSearchRequest) -> List[Dict[str, Any]]:
    return predictor.query_precedents(req.query, top_k=req.top_k)
