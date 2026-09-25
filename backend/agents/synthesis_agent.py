"""
Incident Synthesis Agent.
Assembles the complete 20-section audit-ready Post-Mortem Report in structured JSON,
adhering strictly to computed metrics (MTTD/MTTR) and verified evidence quotes.
"""
from typing import Dict, Any, List
from backend.models.incident import IncidentResponse, IncidentMetrics, SeverityLevel
from backend.models.event import ForensicEvent, TemporalConflict
from backend.models.rca import RCAResult, ImpactAnalysis, ActionItem, ActionItemPriority

class SynthesisAgent:
    @staticmethod
    def synthesize_report(
        incident_id: str,
        title: str,
        severity: SeverityLevel,
        metrics: IncidentMetrics,
        sorted_events: List[ForensicEvent],
        conflicts: List[TemporalConflict],
        rca: RCAResult,
        impact: ImpactAnalysis,
        action_items: List[ActionItem]
    ) -> Dict[str, Any]:
        # Phase grouping
        detection_events = [e for e in sorted_events if e.phase == "Detection"]
        triage_events = [e for e in sorted_events if e.phase == "Triage"]
        mitigation_events = [e for e in sorted_events if e.phase == "Mitigation"]
        resolution_events = [e for e in sorted_events if e.phase == "Resolution"]

        # What went well & what went wrong based on deterministic metrics
        went_well = []
        went_wrong = []

        if metrics.mttd_seconds is not None and metrics.mttd_seconds < 300:
            went_well.append(f"Rapid detection: MTTD was {metrics.mttd_formatted} within SLA threshold.")
        else:
            went_wrong.append(f"Detection latency was elevated ({metrics.mttd_formatted or 'Unanchored'}).")

        if mitigation_events:
            went_well.append(f"Engineers executed active mitigation ({len(mitigation_events)} mitigation actions recorded).")

        if conflicts:
            went_wrong.append(f"Discrepancies identified between incident channels ({len(conflicts)} temporal conflicts detected).")

        if not went_well:
            went_well.append("On-call responders engaged and initiated forensic triage.")
        if not went_wrong:
            primary_svc = sorted_events[0].service_affected if (sorted_events and sorted_events[0].service_affected and sorted_events[0].service_affected != "unspecified") else "affected system"
            went_wrong.append(f"Initial monitoring alarms did not isolate degradation in {primary_svc} prior to operational cascade.")

        corrective_actions = [a.model_dump() for a in action_items if a.priority == ActionItemPriority.IMMEDIATE]
        preventive_actions = [a.model_dump() for a in action_items if a.priority in [ActionItemPriority.SHORT_TERM, ActionItemPriority.LONG_TERM]]

        ds_stats = metrics.statistical_profile or {}
        rec_count = metrics.records_count or len(sorted_events)
        total_alerts = metrics.total_alerts_count or (metrics.critical_alerts_count + metrics.high_alerts_count)
        top_cats = metrics.top_failure_categories or []

        exec_summary_parts = [
            f"On {metrics.start_time_utc or 'recorded timestamp'}, an incident titled '{title}' occurred with severity {severity.value}."
        ]
        if rec_count > 500:
            top_cat_summary = f", predominantly localized in {top_cats[0].get('category')} ({top_cats[0].get('count'):,} failures, {top_cats[0].get('pct')}% blast radius)" if top_cats else ""
            exec_summary_parts.append(
                f"Data science profiling across {rec_count:,} operational records confirmed {total_alerts:,} critical and high-priority alarms{top_cat_summary}."
            )
            exec_summary_parts.append(
                f"Empirical resolution metrics demonstrate a mean MTTR of {metrics.mttr_formatted} (P50 Median: {metrics.p50_mttr_formatted or '--'}, P95 Tail: {metrics.p95_mttr_formatted or '--'}) with an SLA breach rate of {metrics.sla_breach_rate_pct}% ({metrics.sla_breached_count:,} breached tickets)."
            )
        else:
            exec_summary_parts.append(f"{impact.user_impact_summary}")
        
        exec_summary_parts.append(f"Root Cause: {rca.root_cause}")
        exec_summary = " ".join(exec_summary_parts)

        report = {
            "section_01_executive_summary": exec_summary,
            "section_02_incident_metadata": {
                "incident_id": incident_id,
                "title": title,
                "severity": severity.value,
                "total_records_scanned": rec_count,
                "total_events_analyzed": rec_count,
                "total_forensic_milestones": len(sorted_events),
                "conflicts_detected": len(conflicts),
                "is_conclusive_rca": rca.is_conclusive
            },
            "section_03_severity": {
                "level": severity.value,
                "affected_services": impact.affected_services,
                "sla_breached": impact.sla_slo_breached or (metrics.sla_breached_count > 0),
                "sla_breach_rate_pct": metrics.sla_breach_rate_pct,
                "sla_breached_count": metrics.sla_breached_count
            },
            "section_04_business_customer_impact": {
                "summary": impact.user_impact_summary,
                "regions": impact.affected_regions,
                "failed_requests": impact.failed_requests_estimate,
                "revenue_impact": impact.revenue_impact_estimate,
                "duration_minutes": impact.duration_minutes
            },
            "section_05_mttd": {
                "seconds": metrics.mttd_seconds,
                "formatted": metrics.mttd_formatted,
                "detection_time_utc": metrics.detection_time_utc
            },
            "section_06_mttr": {
                "seconds": metrics.mttr_seconds,
                "formatted": metrics.mttr_formatted,
                "p50_median": metrics.p50_mttr_formatted,
                "p95_tail": metrics.p95_mttr_formatted,
                "resolution_time_utc": metrics.resolution_time_utc
            },
            "section_07_timeline": [
                {
                    "event_id": e.event_id,
                    "timestamp_utc": e.timestamp_utc,
                    "actor": e.actor,
                    "service": e.service_affected,
                    "action": e.action_summary,
                    "severity": e.severity,
                    "phase": e.phase,
                    "quote": e.raw_evidence_quote
                } for e in sorted_events[:100]
            ],
            "section_08_detection_phase": [e.action_summary for e in detection_events] or ["Detected via initial system telemetry."],
            "section_09_triage_phase": [e.action_summary for e in triage_events] or ["Responders verified service health and logs."],
            "section_10_mitigation_phase": [e.action_summary for e in mitigation_events] or ["Remediation operations initiated."],
            "section_11_resolution_phase": [e.action_summary for e in resolution_events] or ["Telemetry returned to healthy baselines."],
            "section_12_root_cause": rca.root_cause,
            "section_13_5_whys": [w.model_dump() for w in rca.five_whys],
            "section_14_contributing_factors": rca.contributing_factors,
            "section_15_what_went_well": went_well,
            "section_16_what_went_wrong": went_wrong,
            "section_17_corrective_actions": corrective_actions,
            "section_18_preventive_actions": preventive_actions,
            "section_19_evidence_references": [
                {
                    "event_id": e.event_id,
                    "source": e.source_channel,
                    "quote": e.raw_evidence_quote
                } for e in sorted_events[:15]
            ],
            "section_20_confidence_uncertainty": {
                "confidence_score": rca.confidence_score,
                "evidence_count": len(sorted_events),
                "conflicts_count": len(conflicts),
                "claims": [c.model_dump() for c in rca.grounded_claims]
            },
            "section_21_data_science_statistical_profile": {
                "total_records_profiled": rec_count,
                "mean_mttr": metrics.mttr_formatted,
                "p50_median_mttr": metrics.p50_mttr_formatted,
                "p95_tail_mttr": metrics.p95_mttr_formatted,
                "critical_alerts_count": metrics.critical_alerts_count,
                "high_alerts_count": metrics.high_alerts_count,
                "total_alerts_count": total_alerts,
                "sla_met_count": metrics.sla_met_count,
                "sla_breached_count": metrics.sla_breached_count,
                "sla_breach_rate_pct": metrics.sla_breach_rate_pct,
                "top_failure_categories": top_cats,
                "priorities_distribution": ds_stats.get("priorities_distribution", {})
            }
        }
        return report
