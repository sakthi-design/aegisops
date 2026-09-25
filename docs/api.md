# REST API SPECIFICATION
## AegisOps Incident Intelligence Platform API (`/api`)

---

### Core Endpoints

#### 1. System Health
- **`GET /api/health`**
  - **Response:**
    ```json
    {
      "status": "healthy",
      "timestamp_utc": "2026-09-25T14:30:00Z",
      "environment": "production",
      "llm_provider": "mock",
      "knowledge_base": { "indexed": true, "total_chunks": 18 }
    }
    ```

#### 2. Incidents Management
- **`POST /api/incidents`**
  - Create a new incident container.
  - **Request Body:**
    ```json
    {
      "title": "Payment Gateway Timeout",
      "description": "503 responses on checkout endpoint",
      "created_by": "PagerDuty"
    }
    ```
- **`GET /api/incidents`**
  - List all incidents with status, severity, and computed MTTD/MTTR.
- **`GET /api/incidents/{id}`**
  - Get complete incident state, metrics, report, and evidence graph.
- **`POST /api/incidents/{id}/process`**
  - Triggers the complete deterministic + multi-agent synthesis pipeline.

#### 3. Ingestion Gateway
- **`POST /api/incidents/{id}/ingest`**
  - Ingest raw file (`.log`, `.json`, `.csv`, `.md`, `.pdf`) or direct text string.
  - Automatically identifies source type (Slack, Datadog, Jira, Log, CI/CD).

#### 4. Forensic Telemetry & Timeline
- **`GET /api/incidents/{id}/timeline`**
  - Returns chronologically sorted forensic events, correlated event clusters, and detected temporal conflicts.
- **`GET /api/incidents/{id}/rca`**
  - Returns root cause finding, 5-Whys analysis, failure path, and action items.
- **`GET /api/incidents/{id}/evidence-graph`**
  - Returns nodes and edges representing the complete causal DAG.

#### 5. Human Review & Audit
- **`POST /api/incidents/{id}/review`**
  - Record human decision: `APPROVE`, `FLAG`, `REJECT`, `EDIT`.
- **`POST /api/incidents/{id}/regenerate`**
  - Trigger regeneration with specific feedback constraints.
- **`GET /api/incidents/{id}/audit`**
  - Retrieve enterprise audit logs and data redaction details.

#### 6. Multi-Format Exporters
- **`GET /api/incidents/{id}/export/pdf`** -> `application/pdf`
- **`GET /api/incidents/{id}/export/markdown`** -> `text/markdown`
- **`GET /api/incidents/{id}/export/html`** -> `text/html`
- **`GET /api/incidents/{id}/export/json`** -> `application/json`

#### 7. Scientific Benchmarks
- **`GET /api/evaluation/metrics`**
- **`GET /api/evaluation/baselines`**
- **`GET /api/evaluation/ablation`**
