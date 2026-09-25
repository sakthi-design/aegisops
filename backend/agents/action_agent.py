"""
Action Item Specialist Agent.
Generates concrete, measurable, evidence-backed corrective and preventive actions.
Guarantees NO vague recommendations like "Improve monitoring".
"""
from typing import List, Dict, Any
from backend.models.event import ForensicEvent
from backend.models.rca import RCAResult, ActionItem, ActionItemPriority

class ActionItemAgent:
    @staticmethod
    def generate_actions(
        rca: RCAResult,
        sorted_events: List[ForensicEvent],
        context_chunks: List[Dict[str, Any]]
    ) -> List[ActionItem]:
        actions: List[ActionItem] = []

        # Find primary service and evidence citations
        evidence_ids = [e.event_id for e in sorted_events if e.severity in ["error", "critical"]][:4]
        if not evidence_ids and sorted_events:
            evidence_ids = [sorted_events[0].event_id]

        primary_service = sorted_events[0].service_affected if sorted_events else "Service"

        all_text = " ".join((e.action_summary + " " + e.raw_evidence_quote + " " + e.service_affected).lower() for e in sorted_events)

        is_mem_issue = any(k in all_text for k in ["oom", "memory", "heap", "gc", "ram", "leak"])
        is_net_issue = any(k in all_text for k in ["timeout", "latency", "503", "504", "502", "gateway", "socket", "dns", "refused", "reset"])
        is_disk_issue = any(k in all_text for k in ["disk", "space", "storage", "inode", "io error"])
        is_db_issue = any(k in all_text for k in ["pool", "database", "connection", "query", "deadlock", "postgres", "mysql", "sql", "unindexed"])
        is_deploy_issue = any(k in all_text for k in ["deploy", "release", "commit", "rollout"])

        if is_mem_issue:
            actions.append(ActionItem(
                task=f"Capture process heap dump and increase container memory limit quota for {primary_service}.",
                owner_role="Core Platform Engineering",
                priority=ActionItemPriority.IMMEDIATE,
                deadline="24 Hours",
                success_metric=f"Memory utilization on {primary_service} stabilizes below 75% under sustained load.",
                evidence_basis=evidence_ids
            ))
            actions.append(ActionItem(
                task=f"Configure memory saturation alerts in Prometheus/Datadog for {primary_service} at 85% cgroup threshold.",
                owner_role="SRE Observability Team",
                priority=ActionItemPriority.SHORT_TERM,
                deadline="7 Days",
                success_metric="Automated alert fires prior to OOM killer intervention.",
                evidence_basis=evidence_ids
            ))
            actions.append(ActionItem(
                task=f"Integrate automated memory leak profiling gate in CI/CD pipeline to catch unbounded buffer retention.",
                owner_role="Quality & Reliability Engineering",
                priority=ActionItemPriority.LONG_TERM,
                deadline="30 Days",
                success_metric="Zero memory leak regressions merged to production branches.",
                evidence_basis=evidence_ids
            ))
        elif is_net_issue:
            actions.append(ActionItem(
                task=f"Deploy adaptive circuit breakers and traffic backpressure shedding on {primary_service} inbound RPCs.",
                owner_role="Platform Infrastructure & SRE",
                priority=ActionItemPriority.IMMEDIATE,
                deadline="24 Hours",
                success_metric="Service rejects excess traffic gracefully with HTTP 429 rather than cascading 5xx timeouts.",
                evidence_basis=evidence_ids
            ))
            actions.append(ActionItem(
                task=f"Align upstream gateway timeouts and implement exponential backoff retry jitter for {primary_service}.",
                owner_role="API Gateway Engineering",
                priority=ActionItemPriority.SHORT_TERM,
                deadline="7 Days",
                success_metric="Retry storms shed within 2 seconds of downstream degradation.",
                evidence_basis=evidence_ids
            ))
            actions.append(ActionItem(
                task=f"Execute automated network latency chaos experiments to validate fault tolerance boundaries.",
                owner_role="Chaos Engineering Team",
                priority=ActionItemPriority.LONG_TERM,
                deadline="30 Days",
                success_metric="Synthetic 500ms latency injections do not degrade customer transactions.",
                evidence_basis=evidence_ids
            ))
        elif is_disk_issue:
            actions.append(ActionItem(
                task=f"Purge orphaned temporary files and expand storage volume allocation on {primary_service}.",
                owner_role="Storage & Cloud Infrastructure Team",
                priority=ActionItemPriority.IMMEDIATE,
                deadline="24 Hours",
                success_metric=f"Available disk space on {primary_service} increases to >40% free headroom.",
                evidence_basis=evidence_ids
            ))
            actions.append(ActionItem(
                task="Deploy automated log rotation daemon and configure disk watermark alerting at 80% capacity.",
                owner_role="SRE Infrastructure Team",
                priority=ActionItemPriority.SHORT_TERM,
                deadline="7 Days",
                success_metric="Automatic purge triggers before storage reaches critical watermark.",
                evidence_basis=evidence_ids
            ))
            actions.append(ActionItem(
                task="Enable dynamic persistent volume auto-expansion in cluster manifests for all stateful services.",
                owner_role="DevOps Platform Team",
                priority=ActionItemPriority.LONG_TERM,
                deadline="30 Days",
                success_metric="Storage expands automatically without manual engineer intervention.",
                evidence_basis=evidence_ids
            ))
        elif is_db_issue:
            has_index = "index" in all_text or "unindex" in all_text or "query" in all_text
            fix_task = f"Create missing composite btree index on filtered query columns in {primary_service} database schema." if has_index else f"Optimize database connection pool sizing and connection lifetime on {primary_service}."
            actions.append(ActionItem(
                task=fix_task,
                owner_role="Database Platform & Core Backend Team",
                priority=ActionItemPriority.IMMEDIATE,
                deadline="24 Hours",
                success_metric="Query latency p99 drops below 150ms under peak load.",
                evidence_basis=evidence_ids
            ))
            actions.append(ActionItem(
                task="Configure connection pool saturation alerting in Prometheus/Datadog at 80% utilization with 60-second sustain window.",
                owner_role="SRE Observability Team",
                priority=ActionItemPriority.SHORT_TERM,
                deadline="7 Days",
                success_metric="Automated alert fires during synthetic saturation testing.",
                evidence_basis=evidence_ids
            ))
            actions.append(ActionItem(
                task="Integrate automated query plan analyzer (EXPLAIN ANALYZE linter) in CI/CD pipeline to block unindexed table scans on production schema migrations.",
                owner_role="CI/CD Infrastructure Team",
                priority=ActionItemPriority.LONG_TERM,
                deadline="30 Days",
                success_metric="Zero PRs with unindexed sequential scans merged into main branch.",
                evidence_basis=evidence_ids
            ))
        elif is_deploy_issue:
            actions.append(ActionItem(
                task="Implement automated canary rollback triggered on HTTP 5xx error rate exceeding 1.0% over a 3-minute evaluation window.",
                owner_role="DevOps & Release Engineering",
                priority=ActionItemPriority.IMMEDIATE,
                deadline="48 Hours",
                success_metric="Canary deployments automatically abort without manual engineer intervention.",
                evidence_basis=evidence_ids
            ))
            actions.append(ActionItem(
                task="Audit deployment pre-flight health checks and establish strict synthetic smoke test verification step before traffic cutover.",
                owner_role="Quality Assurance & SRE",
                priority=ActionItemPriority.SHORT_TERM,
                deadline="14 Days",
                success_metric="Smoke test suite validates all critical user journeys prior to 100% routing.",
                evidence_basis=evidence_ids
            ))
            actions.append(ActionItem(
                task="Integrate progressive canary analysis with automated traffic shaping and anomaly rollback.",
                owner_role="SRE Release Team",
                priority=ActionItemPriority.LONG_TERM,
                deadline="30 Days",
                success_metric="Zero customer-impacting deployment regressions reaching 100% stage.",
                evidence_basis=evidence_ids
            ))
        else:
            actions.append(ActionItem(
                task=f"Establish granular health probes and automated circuit breaking on {primary_service} inbound RPCs.",
                owner_role="Core Services Engineering",
                priority=ActionItemPriority.IMMEDIATE,
                deadline="48 Hours",
                success_metric="Service isolates failure within 3 seconds of downstream timeout.",
                evidence_basis=evidence_ids
            ))
            actions.append(ActionItem(
                task=f"Update runbook documentation and alerting thresholds for {primary_service} in SRE central repository.",
                owner_role="SRE On-Call Team",
                priority=ActionItemPriority.SHORT_TERM,
                deadline="7 Days",
                success_metric="Verified runbook link attached to PagerDuty alert definition.",
                evidence_basis=evidence_ids
            ))
            actions.append(ActionItem(
                task=f"Conduct end-to-end resilience architectural review across all dependencies of {primary_service}.",
                owner_role="Principal Architecture Guild",
                priority=ActionItemPriority.LONG_TERM,
                deadline="30 Days",
                success_metric="All critical dependencies implement graceful fallback degradation modes.",
                evidence_basis=evidence_ids
            ))

        return actions
