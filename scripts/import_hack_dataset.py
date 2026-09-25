"""
Script to import and organize operational data and knowledge base documents
from D:\\hack dataset into the project repository structure.
"""
import os
import shutil
from pathlib import Path

DATASET_ROOT = Path("D:/hack dataset")
PROJECT_ROOT = Path(__file__).resolve().parent.parent

def import_knowledge_base():
    """Import operational guidelines, runbooks, and policies from incident-response-docs."""
    ir_docs = DATASET_ROOT / "incident-response-docs-master" / "docs"
    kb_dest = PROJECT_ROOT / "data" / "knowledge_base"
    
    if not ir_docs.exists():
        print(f"Warning: {ir_docs} not found.")
        return

    # 1. Runbooks & operational procedures
    runbooks_dir = kb_dest / "runbooks"
    runbooks_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy relevant docs
    mapping = {
        ir_docs / "during" / "during_an_incident.md": runbooks_dir / "incident_commander_protocol.md",
        ir_docs / "during" / "security_incident_response.md": runbooks_dir / "security_incident_runbook.md",
        ir_docs / "during" / "external_communication_guidelines.md": runbooks_dir / "external_comms_procedure.md",
        ir_docs / "oncall" / "escalation.md": kb_dest / "policies" / "escalation_policy.md",
        ir_docs / "after" / "post_mortem_process.md": kb_dest / "policies" / "post_mortem_policy.md",
        ir_docs / "after" / "post_mortem_template.md": kb_dest / "policies" / "post_mortem_template.md",
        ir_docs / "after" / "effective_post_mortems.md": kb_dest / "policies" / "effective_post_mortems.md",
        ir_docs / "before" / "different_types_of_incident.md": kb_dest / "policies" / "severity_classification_matrix.md",
    }
    
    for src, dst in mapping.items():
        if src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            print(f"[KB] Copied {src.name} -> {dst.relative_to(PROJECT_ROOT)}")

    # 2. Add System Architecture & Database Runbooks
    arch_file = kb_dest / "architecture" / "system_architecture.md"
    arch_file.write_text("""# Production Core Banking & Payments Architecture

## Services Topology
- **Edge Layer:** Cloudflare CDN & WAF -> AWS ALB (`ingress-alb-prod`)
- **API Gateway:** Envoy Proxy / Kong Gateway (`api-gateway-service`)
  - Rate limiting: 10,000 req/sec
  - Timeout: 5000ms
  - Health check endpoint: `/healthz`
- **Authentication Service:** Auth0 + OAuth2 Token Verifier (`auth-service-v2`)
- **Checkout & Order Service:** Go microservice (`order-service`)
- **Payment Processing Engine:** Java Spring Boot (`payment-processor`)
  - Database: Aurora PostgreSQL Multi-AZ (`payments-db-primary`, `payments-db-replica-1`)
  - Connection Pool: HikariCP (Max connections: 100, min idle: 20, connection timeout: 3000ms)
  - Circuit Breaker: Resilience4j to 3rd-party banking rails (Stripe / Adyen)
- **Message Broker:** Apache Kafka Cluster (3 brokers, replication factor: 3)
  - Topics: `payment.initiated`, `payment.authorized`, `payment.failed`, `order.events`
- **Cache Cluster:** Redis Sentinel Cluster (`redis-session-cache`)

## Dependency Graph
`ingress-alb-prod` -> `api-gateway-service` -> `payment-processor` -> `payments-db-primary`
`payment-processor` -> `redis-session-cache`
`payment-processor` -> `Kafka Broker 1,2,3`
`payment-processor` -> `Stripe Payment Gateway (External)`
""", encoding="utf-8")

    db_runbook = kb_dest / "runbooks" / "database_pool_exhaustion_runbook.md"
    db_runbook.write_text("""# Runbook: Aurora PostgreSQL Connection Pool Exhaustion & High Latency

## Symptoms
- HTTP 503 / 504 errors on `/api/v1/payments/charge`
- HikariCP pool saturation alert: `ActiveConnections > 85%` for > 60s
- Slow query logs: Queries on `transactions` table with sequential scans exceeding 12,000ms

## Diagnostic Steps
1. Verify active connection count on primary database:
   `SELECT count(*), state FROM pg_stat_activity GROUP BY state;`
2. Identify long-running queries holding locks:
   `SELECT pid, now() - query_start as duration, query FROM pg_stat_activity WHERE state != 'idle' ORDER BY duration DESC LIMIT 5;`
3. Inspect recent deployment history on `payment-processor` and database migration jobs.

## Immediate Mitigation
1. If unindexed query is flooding connections:
   - Terminate offending queries: `SELECT pg_terminate_backend(pid);`
   - Apply hotfix migration adding missing btree index on foreign key or filter column:
     `CREATE INDEX CONCURRENTLY idx_transactions_user_created ON transactions(user_id, created_at DESC);`
2. If connection leak suspected:
   - Perform graceful rolling restart of `payment-processor` pods.
   - Adjust HikariCP `maximumPoolSize` up to DB max limit temporarily.
""", encoding="utf-8")

    k8s_runbook = kb_dest / "runbooks" / "kubernetes_crashloop_runbook.md"
    k8s_runbook.write_text("""# Runbook: Kubernetes OOMKilled & CrashLoopBackOff

## Symptoms
- Pod state `CrashLoopBackOff`, exit code 137 (SIGKILL by Linux OOM killer)
- Service response degraded, 502 Bad Gateway at ingress

## Mitigation
1. Check dmesg / k8s events: `kubectl describe pod -l app=order-service`
2. Review memory cgroup limit: `resources.limits.memory`
3. Roll back bad deployment immediately: `kubectl rollout undo deployment/order-service`
""", encoding="utf-8")

def import_telemetry_samples():
    """Import representative log files from loghub-master for testing and ingestion."""
    loghub_root = DATASET_ROOT / "loghub-master"
    dest_dir = PROJECT_ROOT / "data" / "raw" / "loghub"
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    if not loghub_root.exists():
        print(f"Warning: {loghub_root} not found.")
        return

    targets = [
        ("Apache", "Apache_2k.log"),
        ("OpenStack", "OpenStack_2k.log"),
        ("Linux", "Linux_2k.log"),
        ("Zookeeper", "Zookeeper_2k.log"),
    ]
    
    for sub, filename in targets:
        src = loghub_root / sub / filename
        if src.exists():
            dst = dest_dir / f"{sub.lower()}_sample.log"
            shutil.copy2(src, dst)
            print(f"[Telemetry] Copied {src.name} -> {dst.relative_to(PROJECT_ROOT)}")

def import_awesome_sre():
    """Import SRE guides and references from awesome-sre-master."""
    sre_root = DATASET_ROOT / "awesome-sre-master"
    dest = PROJECT_ROOT / "data" / "knowledge_base" / "policies" / "awesome_sre_index.md"
    
    if (sre_root / "README.md").exists():
        shutil.copy2(sre_root / "README.md", dest)
        print(f"[SRE] Copied SRE index to {dest.relative_to(PROJECT_ROOT)}")

if __name__ == "__main__":
    print(f"Importing dataset assets from {DATASET_ROOT}...")
    import_knowledge_base()
    import_telemetry_samples()
    import_awesome_sre()
    print("Dataset import complete.")
