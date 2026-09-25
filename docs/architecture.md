# ARCHITECTURE & SYSTEM DESIGN DOCUMENT
## AegisOps: Automated Incident Narrative Synthesis Platform

---

## 1. Executive Summary & Core Principle
AegisOps is an enterprise-grade Incident Intelligence Platform that solves the fundamental flaws of naive LLM summarization:
- **LLMs Hallucinate Numbers & Timestamps**: LLMs cannot reliably perform distributed timestamp arithmetic, timezone alignment, or chronological sorting.
- **LLMs Over-confidently Invent Root Causes**: Naive summarizers invent causal links not supported by telemetry.
- **LLMs are Vulnerable to Data-as-Instruction Injection**: Malicious or malformed log lines alter reasoning flow.

**Our Core Architectural Principle:**
> **NEVER TRUST THE LLM WITH DETERMINISTIC OPERATIONS.**  
> Probabilistic AI handles semantic extraction, reasoning, and narrative phrasing.  
> Deterministic Engineering handles timestamp normalization, chronological sorting, deduplication, conflict detection, MTTD/MTTR math, and cryptographic evidence hashing.

---

## 2. End-to-End Pipeline Flow

```mermaid
flowchart TD
    A[Multi-Source Evidence\nSlack, Datadog, Jira, Logs, CI/CD] --> B[Ingestion Gateway\nFile Parsers & Type Detection]
    B --> C[Security & Sanitization Engine\nPII, Secret Masking & Untrusted Data Wrapper]
    C --> D[Temporal Normalization Engine\nTimezone to UTC & Relative Time Anchor]
    D --> E[Forensic Event Extraction Agent\nVerbatim Evidence Quotes & Actor Attribution]
    E --> F[Deterministic State Engine\nPython Sorting, Dedup & Clustering]
    F --> G[Conflict Detection Engine\nDiscrepancy Identification: Slack vs Jira]
    G --> H[Hybrid RAG Knowledge Layer\nBM25 + Dense Vectors over Runbooks & Topology]
    H --> I[Multi-Agent Reasoning Council]
    
    subgraph Reasoning ["Multi-Agent Reasoning Council"]
        I1[RCA Specialist Agent\n5-Whys & Failure Path]
        I2[Impact Analysis Agent\nBlast Radius & Metrics]
        I3[Severity Agent\nP0-P3 Enterprise Policy]
        I4[Action Item Agent\nMeasurable Tasks & Owners]
    end
    I --> Reasoning
    Reasoning --> J[Incident Synthesis Agent\n20-Section Post-Mortem]
    J --> K[Adversarial Critic / Fact Checker\nChecks Quotes, Metrics, SHAs & Services]
    
    K -- Fails Audit --> J
    K -- Passes Audit --> L[Human-in-the-Loop Review Center\nApprove, Flag, Reject, Edit]
    L --> M[Post-Mortem Distribution\nPDF, Markdown, HTML, JSON]
```

---

## 3. Sequence Diagram: Outage to Verified Post-Mortem

```mermaid
sequenceDiagram
    autonumber
    participant Ops as Operations Telemetry
    participant Ingest as Ingestion Gateway
    participant Sec as Security Engine
    participant Temp as Temporal & Event Engine
    participant RAG as Knowledge Base (RAG)
    participant Agents as Multi-Agent Council
    participant Critic as Adversarial Critic
    participant Human as SRE Commander
    
    Ops->>Ingest: Stream Slack logs, alerts, Jira tickets
    Ingest->>Sec: Raw unstructured telemetry
    Note over Sec: Scrub API Keys, Passwords, PII.<br/>Wrap in <UNTRUSTED_INCIDENT_DATA>
    Sec->>Temp: Sanitized operational stream
    Note over Temp: Deterministic UTC Sort,<br/>Deduplication, Conflict Check,<br/>Calculate MTTD & MTTR
    Temp->>RAG: Query service topology & failure runbooks
    RAG-->>Agents: Relevant architectural context
    Agents->>Agents: RCA, 5-Whys, Impact, Action Items
    Agents->>Critic: Synthesized Draft Post-Mortem
    Note over Critic: Verify every percentage, service,<br/>and commit SHA against raw evidence
    Critic-->>Human: Verified Post-Mortem (AUDIT PASSED)
    Human->>Human: Review, approve, and sign off
    Human->>Ingest: Export certified PDF / Markdown
```

---

## 4. Entity-Relationship (ER) Schema

```mermaid
erDiagram
    INCIDENT ||--o{ RAW_EVIDENCE : contains
    INCIDENT ||--o{ FORENSIC_EVENT : generates
    INCIDENT ||--o{ EVENT_CLUSTER : groups
    INCIDENT ||--o{ AUDIT_LOG : tracks
    INCIDENT ||--o| REPORT : synthesizes
    
    INCIDENT {
        string id PK
        string title
        string status
        string severity
        datetime created_at
        text metrics_json
    }
    
    RAW_EVIDENCE {
        string id PK
        string incident_id FK
        string source_type
        string filename
        string content_hash
        text raw_content
        int redaction_count
    }
    
    FORENSIC_EVENT {
        string id PK
        string incident_id FK
        string timestamp_utc
        float epoch_timestamp
        string source_channel
        string actor
        string service_affected
        string action_summary
        string raw_evidence_quote
        string severity
        string phase
    }
    
    AUDIT_LOG {
        string id PK
        string incident_id FK
        string timestamp_utc
        string user_or_agent
        string action
        text details_json
    }
```
