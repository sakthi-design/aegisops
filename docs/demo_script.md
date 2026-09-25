# DEMONSTRATION SCRIPT
## Step-by-Step Evaluator & Stakeholder Walkthrough

---

### Step 1: Launch Application
Run the platform with the Python virtual environment:
```powershell
.venv\Scripts\uvicorn backend.main:app --reload --port 8000
```
Open browser to `http://localhost:8000`.

---

### Step 2: The Command Center Overview
1. Show the **AegisOps Dashboard**:
   - Point out the active incident: `INC-2026-PAY-882`.
   - Explain the computed metrics:
     - **MTTD:** `14m 20s` (computed strictly in Python using UTC timestamps).
     - **MTTR:** `35m 30s` (resolution timestamp minus start timestamp).
     - **Critic Pass Rate:** `99.2%`.
   - Highlight that the system enforces: **"Never trust the LLM with deterministic operations."**

---

### Step 3: Forensic Timeline & Temporal Conflict Detection
1. Click **Forensic Timeline** tab.
2. Note the banner: **`TEMPORAL CONFLICT DETECTED`**:
   - Discrepancy detected between Slack (rollback reported at 14:20:00Z) and Jira (rollback recorded at 14:24:00Z).
   - Explain: Naive LLMs silently fabricate an arbitrary timestamp. AegisOps deterministically identifies the 240-second discrepancy and alerts the incident commander.
3. Filter by phases: `Detection`, `Triage`, `Mitigation`, `Resolution`.
4. Point out that every event displays:
   - Source channel (Slack, Datadog, Jira, Log)
   - Verbatim raw evidence quote directly from the ingested payload.

---

### Step 4: Root Cause Analysis & 5-Whys
1. Click **RCA & 5-Whys** tab.
2. Show the grounded Root Cause:
   - *"Deployment triggered unindexed database queries on payment-processor, exhausting connection pool."*
3. Inspect the **5-Whys Investigation**:
   - Each step cites an exact event ID (`EVT-001`, `EVT-004`).
   - If telemetry is insufficient, the system explicitly outputs: *"Root cause inconclusive based on telemetry provided"*, preventing hallucinations.

---

### Step 5: Causal Evidence DAG Graph
1. Click **Evidence DAG Graph** tab.
2. Walk through the interactive visual graph:
   - Incident node &rarr; Event nodes &rarr; Affected Services &rarr; Deployment (`commit d7a8e21`) &rarr; Verified Post-Mortem Claims.

---

### Step 6: Adversarial Critic & Human Review Gate
1. Click **Human Review & Sign-Off** tab.
2. Review the **Adversarial Critic Audit**:
   - Explains how all metrics (e.g. 82% connection pool), services, and commit SHAs were verified against source quotes.
3. Demonstrate Human Action:
   - Click **Approve & Certify** with notes: *"Verified and certified by On-Call Commander"*.
   - Show status transition to `APPROVED`.

---

### Step 7: Exporting Post-Mortem Artifacts
1. Click **Post-Mortem Export** tab.
2. Click **Download PDF**:
   - Opens the publication-ready PDF containing Executive Summary, Metrics Table, Timeline, 5-Whys, and Action Items.
3. Click **Download Markdown**:
   - Produces GitHub/Confluence ready markdown with checklist action items.

---

### Step 8: Scientific Benchmark & Ablation Study
1. Click **Evaluation & Ablation** tab.
2. Present the empirical comparison:
   - Baseline A (Single LLM) vs Baseline B (Extraction Only) vs AegisOps Proposed Platform.
   - Show the Ablation Study demonstrating why each component (Deterministic Sort, RAG, Adversarial Critic, Secret Scrubber) is required.

---

### Step 9: Running the Automated Adversarial Suite
Run in terminal:
```powershell
.venv\Scripts\pytest tests/
```
Show 18/18 passing tests covering TC001 to TC016.
