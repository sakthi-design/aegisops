"""
AegisOps — ML Inference Engine.
Loads trained models (AegisLogNet, AegisRCA-Pro, AegisTriage-Rank, AegisKnowledgeIndex)
and provides ultra-fast deterministic ML inference & historical precedent retrieval.
"""

import os
import json
import logging
import joblib
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger("AegisInference")

MODEL_DIR = Path(__file__).resolve().parent.parent / "trained_models"

RECOMMENDED_REMEDIATIONS = {
    "database_and_storage_saturation": (
        "1. Check pg_stat_activity / SHOW PROCESSLIST for locked queries.\n"
        "2. Kill long-running unindexed table scans (SELECT pg_terminate_backend(pid)).\n"
        "3. Increase connection pool max connections temporarily and add missing indexes."
    ),
    "memory_and_resource_exhaustion": (
        "1. Capture heap dump / core dump before pod restart.\n"
        "2. Identify leaking object retention or unbounded caching.\n"
        "3. Increase container memory cgroup limit and scale pod replicas horizontally."
    ),
    "bad_deployment_and_regression": (
        "1. Execute immediate rolling rollback to previous stable commit SHA (git revert / helm rollback).\n"
        "2. Check error diff between release tags.\n"
        "3. Verify staging smoke tests before re-attempting rollout."
    ),
    "network_and_routing_failure": (
        "1. Verify BGP routing tables and prefix filters with upstream transit providers.\n"
        "2. Flush internal CoreDNS cache and inspect ingress proxy upstream health.\n"
        "3. Fail over traffic to secondary standby availability zone / CDN edge."
    ),
    "certificate_and_auth_failure": (
        "1. Renew and deploy emergency wildcard TLS certificate to ingress gateway.\n"
        "2. Verify OAuth2 / JWKS endpoint availability and certificate thumbprint.\n"
        "3. Temporarily extend token validity grace window if security policy permits."
    ),
    "concurrency_and_deadlocks": (
        "1. Review thread dumps for circular lock dependencies / Mutex contention.\n"
        "2. Decouple synchronous calls using asynchronous Kafka message buffering.\n"
        "3. Enable circuit breakers and rate limiting to shed concurrent load."
    ),
    "upstream_and_third_party_dependency": (
        "1. Activate fallback vendor / secondary payment gateway provider.\n"
        "2. Enable circuit breaker to return graceful cached responses / queued orders.\n"
        "3. Post external status page update to inform end-users."
    )
}

class AIOpsPredictor:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AIOpsPredictor, cls).__new__(cls)
            cls._instance._load_models()
        return cls._instance

    def _load_models(self):
        self.log_model = None
        self.rca_model = None
        self.severity_model = None
        self.knowledge_index = None
        self.metrics = {}

        try:
            metrics_file = MODEL_DIR / "training_metrics.json"
            if metrics_file.exists():
                with open(metrics_file, "r", encoding="utf-8") as f:
                    self.metrics = json.load(f)

            log_file = MODEL_DIR / "aegis_log_anomaly_model.joblib"
            if log_file.exists():
                self.log_model = joblib.load(log_file)

            rca_file = MODEL_DIR / "aegis_rca_classifier.joblib"
            if rca_file.exists():
                self.rca_model = joblib.load(rca_file)

            sev_file = MODEL_DIR / "aegis_severity_ranker.joblib"
            if sev_file.exists():
                self.severity_model = joblib.load(sev_file)

            kb_file = MODEL_DIR / "aegis_knowledge_index.joblib"
            if kb_file.exists():
                self.knowledge_index = joblib.load(kb_file)

            logger.info("Successfully loaded all 4 trained AIOps models.")
        except Exception as e:
            logger.error(f"Error loading trained models: {e}")

    def predict_log(self, raw_message: str) -> Dict[str, Any]:
        """Classifies a log message as normal or anomalous combining ML and operational priors."""
        results = self.predict_log_batch([raw_message])
        return results[0] if results else {"error": "Prediction failed"}

    def predict_log_batch(self, raw_messages: List[str]) -> List[Dict[str, Any]]:
        """
        Vectorized batch classification of log messages.
        Processes thousands of log entries simultaneously in a single matrix operation.
        """
        if not self.log_model:
            return [{"error": "AegisLogNet model not loaded"}] * len(raw_messages)
        if not raw_messages:
            return []

        probas = self.log_model.predict_proba(raw_messages)
        results = []

        for raw_msg, proba in zip(raw_messages, probas):
            ml_score = float(proba[1])
            upper_msg = raw_msg.upper()
            if any(tok in upper_msg for tok in ["CRITICAL", "FATAL", "PANIC", "DEADLOCK", "OOMKILLED", "OUTOFMEMORY"]):
                anomaly_score = max(ml_score, 0.85)
            elif any(tok in upper_msg for tok in ["ERROR", "EXCEPTION", "FAILED", "TIMEOUT", "REFUSED", "POOL SATURATION"]):
                anomaly_score = max(ml_score, 0.65)
            elif any(tok in upper_msg for tok in ["INFO", "DEBUG", "TRACE", "SUCCESS", "OPERATING NORMALLY"]):
                anomaly_score = min(ml_score, 0.25)
            else:
                anomaly_score = ml_score

            is_anomaly = anomaly_score >= 0.5
            if anomaly_score >= 0.8:
                risk = "CRITICAL"
            elif anomaly_score >= 0.5:
                risk = "HIGH"
            elif anomaly_score >= 0.2:
                risk = "ELEVATED"
            else:
                risk = "NORMAL"

            results.append({
                "raw_message": raw_msg,
                "is_anomaly": is_anomaly,
                "anomaly_score": round(anomaly_score, 4),
                "risk_tier": risk,
                "normal_probability": round(1.0 - anomaly_score, 4)
            })

        return results

    def predict_rca(self, incident_text: str) -> Dict[str, Any]:
        """Classifies root cause category and returns top-3 hypotheses."""
        if not self.rca_model:
            return {"error": "AegisRCA-Pro model not loaded"}

        proba = self.rca_model.predict_proba([incident_text])[0]
        classes = self.rca_model.classes_

        # Rank predictions
        ranked_indices = np.argsort(proba)[::-1]
        top_causes = []
        for idx in ranked_indices[:3]:
            cat = classes[idx]
            top_causes.append({
                "category": cat,
                "display_name": cat.replace("_", " ").title(),
                "probability": round(float(proba[idx]), 4),
                "percentage": f"{round(float(proba[idx]) * 100, 1)}%"
            })

        primary = top_causes[0]["category"]
        remediation = RECOMMENDED_REMEDIATIONS.get(primary, "Perform triage based on standard operational runbook.")

        return {
            "primary_cause": primary,
            "primary_display_name": top_causes[0]["display_name"],
            "primary_confidence": top_causes[0]["probability"],
            "top_hypotheses": top_causes,
            "recommended_mitigation": remediation
        }

    def predict_severity(self, incident_text: str) -> Dict[str, Any]:
        """Predicts incident severity (P0, P1, P2, P3)."""
        if not self.severity_model:
            return {"error": "AegisTriage-Rank model not loaded"}

        proba = self.severity_model.predict_proba([incident_text])[0]
        classes = self.severity_model.classes_

        distribution = {cls_name: round(float(p), 4) for cls_name, p in zip(classes, proba)}
        pred_sev = classes[np.argmax(proba)]

        return {
            "predicted_severity": pred_sev,
            "confidence": round(float(np.max(proba)), 4),
            "severity_distribution": distribution
        }

    def query_precedents(self, incident_text: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Retrieves top-k historical post-mortems and runbooks matching the query."""
        if not self.knowledge_index:
            return []

        vectorizer = self.knowledge_index["vectorizer"]
        doc_embeddings = self.knowledge_index["embeddings"]
        documents = self.knowledge_index["documents"]

        query_vec = vectorizer.transform([incident_text])
        similarities = cosine_similarity(query_vec, doc_embeddings)[0]

        top_indices = np.argsort(similarities)[::-1][:top_k]
        results = []
        for idx in top_indices:
            score = float(similarities[idx])
            if score > 0.02: # Minimum relevance threshold
                doc = documents[idx].copy()
                doc["similarity_score"] = round(score, 4)
                doc["match_percentage"] = f"{round(score * 100, 1)}%"
                results.append(doc)
                
        return results

    def get_metrics(self) -> Dict[str, Any]:
        return self.metrics

# Global singleton
predictor = AIOpsPredictor()
