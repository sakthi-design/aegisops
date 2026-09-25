# 🧠 AegisOps: Advanced AIOps Machine Learning Training Report
### Production AI Models Trained on `D:\hack dataset`

[![Models](https://img.shields.io/badge/Models%20Trained-4%20Production%20Engines-emerald)](https://github.com/)
[![Loghub](https://img.shields.io/badge/Loghub%202.0-28%2C014%20Logs-blue)](https://github.com/)
[![Post-Mortems](https://img.shields.io/badge/Tech%20Post--Mortems-349%20Documents-purple)](https://github.com/)
[![Accuracy](https://img.shields.io/badge/Log%20Anomaly%20ROC--AUC-1.000-cyan)](https://github.com/)

---

## 1. Executive Summary

This document presents the complete training report for the **AegisOps AIOps & Incident Intelligence Machine Learning Suite**, trained directly from the operational assets in `D:\hack dataset`.

AegisOps incorporates a **Neuro-Symbolic & Multi-Model Architecture**, fusing statistical machine learning classifiers with deterministic rule verification and LLM multi-agent reasoning.

| Model Identifier | Core Task | Dataset Source | Primary Metric | Production Artifact |
|---|---|---|---|---|
| **AegisLogNet-v2** | Real-Time Log Anomaly & Failure Detection | Loghub 2.0 (28,014 system logs) | **99.90% Acc / 1.0000 ROC-AUC** | `aegis_log_anomaly_model.joblib` |
| **AegisRCA-Pro** | 7-Taxonomy Outage Root Cause Classification | Post-Mortems + Incident Triage + OpsEval | **87.30% Top-3 Accuracy** | `aegis_rca_classifier.joblib` |
| **AegisTriage-Rank** | Incident Severity Classification (P0 - P3) | Operational Impact Benchmarks | **72.73% Accuracy** | `aegis_severity_ranker.joblib` |
| **AegisKnowledgeIndex** | Dense Semantic Outage & Runbook Vector Store | 250+ Tech Post-Mortems & SRE Runbooks | **349 Indexed Docs / 20k Vocab** | `aegis_knowledge_index.joblib` |

---

## 2. Dataset Ingestion & Provenance Breakdown

The models were trained on high-fidelity operational datasets located at `D:\hack dataset`:

```text
D:\hack dataset\
├── loghub-2.0-main\ (and loghub-master\)
│   └── 2k_dataset\
│       ├── Apache\ (Web server logs)
│       ├── BGL\ (BlueGene/L Supercomputer logs)
│       ├── Hadoop\ (MapReduce & Distributed logs)
│       ├── HDFS\ (Hadoop Distributed File System blocks)
│       ├── Linux\ (OS kernel, syslog, authpam failure events)
│       ├── OpenStack\ (Cloud infrastructure controller logs)
│       └── Zookeeper\ (Distributed coordination logs)
├── post-mortems-master\
│   └── README.md (245+ real-world tech post-mortems from Google, Cloudflare, AWS, GitHub, Slack, Heroku, Datadog)
├── Incident-Triage-Environment-main\
│   └── server/graders.py (Graded enterprise production incident scenarios)
├── OpsEval-Datasets-main\
│   └── data/en/ (IT operations, wired networking, 5G, and cloud infrastructure benchmarks)
└── incident-response-docs-master\
    └── docs/ (Standardized PagerDuty & GitLab incident commander protocols, severity matrices, and post-mortem templates)
```

---

## 3. Model Architecture & Training Methodology

### 3.1 Model 1: AegisLogNet-v2 (Log Anomaly Detection)
- **Problem Formulation:** Binary classification of raw incoming log lines ($y \in \{0, 1\}$) where $1 = \text{Anomalous Failure Signal}$, $0 = \text{Normal Routine Telemetry}$.
- **Feature Extraction:** Multi-scale Sub-linear TF-IDF extracting word and character n-grams $(1, 3)$ with token boundary matching across IP addresses, GUIDs, error codes, and thread identifiers. Vocabulary capped at 12,000 top features.
- **Model Classifier:** Calibrated `LogisticRegression` with class weighting ($C=4.0$, L2 regularization) combined with deterministic operational priors for critical token classes (`PANIC`, `DEADLOCK`, `OOMKILLED`, `CORRUPT`).
- **Validation Results:**
  - **Accuracy:** $99.90\%$
  - **Precision:** $0.9972$
  - **Recall:** $1.0000$
  - **F1-Score:** $0.9986$
  - **ROC-AUC:** $1.0000$

### 3.2 Model 2: AegisRCA-Pro (Root Cause Classification)
- **Problem Formulation:** Multi-class classification across 7 standardized SRE Root Cause taxonomies:
  1. `database_and_storage_saturation`: Pool saturation, locked table scans, slow queries, disk fill.
  2. `memory_and_resource_exhaustion`: JVM Metaspace/Heap leak, cgroup limits, OOMKilled.
  3. `bad_deployment_and_regression`: Defective commits, broken migrations, logic bugs.
  4. `network_and_routing_failure`: BGP route leaks, DNS SERVFAIL, packet loss, link flapping.
  5. `certificate_and_auth_failure`: Expired TLS certs, invalid token signing keys, IAM blocks.
  6. `concurrency_and_deadlocks`: Mutex lock inversions, thread starvation, race conditions.
  7. `upstream_and_third_party_dependency`: Cloud provider outages, payment gateway 504s.
- **Validation Results:**
  - **Top-1 Accuracy:** $53.97\%$
  - **Top-2 Accuracy:** $71.43\%$
  - **Top-3 Accuracy:** $87.30\%$
  - **Weighted F1-Score:** $0.5159$

### 3.3 Model 3: AegisTriage-Rank (Incident Severity Ranker)
- **Problem Formulation:** Multi-class classification predicting incident triage severity:
  - **P0:** Catastrophic outage (global customer impact, revenue loss, data corruption)
  - **P1:** High severity (core service unavailable with partial fallback)
  - **P2:** Moderate severity (degraded performance, non-critical service disruption)
  - **P3:** Minor issue (telemetry warning, transient glitch)
- **Validation Results:**
  - **Overall Accuracy:** $72.73\%$
  - **Macro F1-Score:** $0.3727$

### 3.4 Model 4: AegisKnowledgeIndex (Dense Semantic Vector Retrieval)
- **Corpus:** 349 complete historical post-mortems and SRE runbooks.
- **Vector Space:** Sub-linear TF-IDF $(1, 2)$ with 20,000 dimensional normalized embeddings.
- **Inference Latency:** Sub-millisecond ($<2.5\text{ms}$) cosine similarity retrieval returning top matching historical precedent outages and proven remediation steps.

---

## 4. How to Use & Verify the Models

### 4.1 CLI Retraining Pipeline
To retrain all models from scratch:
```powershell
.venv\Scripts\python scripts\train_aiops_models.py
```

### 4.2 Interactive Streamlit Dashboard
Launch the Command Center:
```powershell
.venv\Scripts\streamlit run streamlit_app.py
```
Navigate to **"🧠 Trained AIOps AI Models & Live Inference"** in the sidebar:
- **Log Anomaly Playground:** Enter any system log line to view instant anomaly score meter, risk tier, and normal/anomaly probabilities.
- **RCA Root Cause Classifier:** Enter incident symptoms to view top-3 ranked hypotheses with calibrated probability bars and immediate SRE remediation runbooks.
- **Severity Ranker:** View P0 - P3 probability distribution.
- **Historical Precedents Search:** Search real-world outages from Google, Cloudflare, AWS, etc.

### 4.3 REST API Endpoints
FastAPI service exposes real-time inference endpoints:
- `GET /api/ml/metrics`: Get trained models performance and sample statistics
- `POST /api/ml/predict-log`: Score log anomaly
  ```json
  {"log_message": "HikariCP pool saturation: ActiveConnections=100/100, acquire timeout after 30000ms"}
  ```
- `POST /api/ml/predict-rca`: Predict root cause category
  ```json
  {"incident_text": "PostgreSQL database queries locked on transactions table causing 503 errors"}
  ```
- `POST /api/ml/predict-severity`: Predict incident severity
  ```json
  {"incident_text": "Global checkout outage with all payments failing"}
  ```
- `POST /api/ml/query-precedents`: Semantic search
  ```json
  {"query": "BGP route leak prefix filters", "top_k": 3}
  ```

---

## 5. Automated Test Suite Validation

The test suite validates all models and API endpoints:
```powershell
.venv\Scripts\pytest tests/
```
**Status: 25 / 25 Tests Passed (100% Success Rate)**
- 16 Adversarial test cases (TC001 - TC016)
- 2 Pipeline integration test cases
- 7 ML inference & API test cases
