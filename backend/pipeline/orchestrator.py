"""
Pipeline Orchestrator.
Executes the Probabilistic AI + Deterministic Engineering pipeline.
Manages sanitization, extraction, sorting, dedup, clustering, conflict detection,
RAG retrieval, RCA, impact, severity, action generation, synthesis, critic verification,
and retry loop.
"""
from datetime import datetime, timezone
import hashlib
import concurrent.futures
from typing import Dict, Any, List, Optional
from backend.pipeline.state import PipelineState
from backend.models.incident import IncidentStatus, IncidentMetrics, SeverityLevel
from backend.models.event import ForensicEvent
from backend.security.sanitizer import SanitizationEngine
from backend.temporal.normalizer import TemporalNormalizer
from backend.temporal.profiler import DatasetStatisticalProfiler
from backend.temporal.sorter import DeterministicEventEngine
from backend.temporal.conflict_detector import ConflictDetector
from backend.rag.retriever import KnowledgeRetriever
from backend.agents.base_provider import get_llm_provider
from backend.agents.extraction_agent import ForensicExtractionAgent
from backend.agents.rca_agent import RCAAgent
from backend.agents.impact_agent import ImpactAgent
from backend.agents.severity_agent import SeverityAgent
from backend.agents.action_agent import ActionItemAgent
from backend.agents.synthesis_agent import SynthesisAgent
from backend.agents.critic_agent import CriticAgent
from backend.evidence.evidence_graph import EvidenceGraphBuilder
from backend.models.audit import AuditLogEntry

class IncidentOrchestrator:
    def __init__(self):
        self.sanitizer = SanitizationEngine(pii_enabled=True, secret_enabled=True)
        self.llm_provider = get_llm_provider()
        self.extraction_agent = ForensicExtractionAgent(self.llm_provider)
        self.rca_agent = RCAAgent(self.llm_provider)
        self.impact_agent = ImpactAgent(self.llm_provider)
        self.kb_retriever = KnowledgeRetriever.get_instance()

    def run_pipeline(self, state: PipelineState) -> PipelineState:
        """
        Executes complete pipeline from Ingest -> Sanitize -> Extract -> Sort ->
        RAG -> RCA -> Impact -> Action -> Synthesis -> Critic.
        """
        # Ensure state.raw_inputs contains unique evidence (no accidental duplicate files)
        unique_inputs = []
        seen_keys = set()
        for inp in state.raw_inputs:
            c = inp.get("content", "")
            key = inp.get("source_id") or hashlib.sha256(c.encode("utf-8")).hexdigest()
            norm_key = key.split("_", 1)[-1] if "_" in key else key
            content_sig = (norm_key, len(c))
            if content_sig not in seen_keys:
                seen_keys.add(content_sig)
                unique_inputs.append(inp)
        state.raw_inputs = unique_inputs

        # STEP 1: SANITIZATION & PROMPT INJECTION DEFENSE (Parallelized)
        state.status = IncidentStatus.SANITIZING
        def _sanitize_single(inp):
            content = inp.get("content", "")
            san_res = self.sanitizer.sanitize(content)
            item = {
                "source_id": inp.get("source_id", "src_0"),
                "source_type": inp.get("source_type", "generic"),
                "filename": inp.get("filename", "upload.txt"),
                "sanitized_content": san_res.sanitized_text,
                "redaction_count": san_res.audit.redaction_count
            }
            return item, san_res.audit

        if len(state.raw_inputs) > 1:
            with concurrent.futures.ThreadPoolExecutor(max_workers=min(8, len(state.raw_inputs))) as executor:
                san_results = list(executor.map(_sanitize_single, state.raw_inputs))
        else:
            san_results = [_sanitize_single(inp) for inp in state.raw_inputs]

        state.sanitized_inputs = [r[0] for r in san_results]
        state.redaction_audits = [r[1] for r in san_results]

        self._record_audit(state, "SECURITY_SANITIZATION", {
            "redactions": sum(a.redaction_count for a in state.redaction_audits)
        })

        # STEP 2: FORENSIC EVENT EXTRACTION (Parallelized)
        state.status = IncidentStatus.EXTRACTING
        def _extract_single(inp):
            return self.extraction_agent.extract_events(
                sanitized_content=inp["sanitized_content"],
                source_channel=inp["source_type"]
            )

        if len(state.sanitized_inputs) > 1:
            with concurrent.futures.ThreadPoolExecutor(max_workers=min(8, len(state.sanitized_inputs))) as executor:
                extracted_batches = list(executor.map(_extract_single, state.sanitized_inputs))
        else:
            extracted_batches = [_extract_single(inp) for inp in state.sanitized_inputs]

        extracted_events = [evt for batch in extracted_batches for evt in batch]

        # Ensure globally unique sequential event IDs across all ingested sources
        for idx, evt in enumerate(extracted_events):
            evt.event_id = f"EVT-{idx+1:03d}"

        state.extracted_events = extracted_events

        # STEP 3: DETERMINISTIC SORTING & DEDUPLICATION (NEVER TRUST LLM)
        sorted_events = DeterministicEventEngine.sort_chronologically(extracted_events)
        deduped_events, dedup_count = DeterministicEventEngine.deduplicate(sorted_events)
        state.sorted_events = deduped_events

        # STEP 4: EVENT CLUSTERING
        state.event_clusters = DeterministicEventEngine.cluster_events(deduped_events)

        # STEP 5: CONFLICT DETECTION
        state.conflicts = ConflictDetector.detect_conflicts(deduped_events)

        # STEP 6: DETERMINISTIC MTTD / MTTR METRICS
        state.metrics = self._calculate_metrics(deduped_events, raw_inputs=state.raw_inputs, clusters=state.event_clusters)

        # Compute full dataset scale: accurate event/record count across ingested telemetry
        total_raw_records = 0
        for inp in state.raw_inputs:
            c = inp.get("content", "")
            if c:
                lines = [l for l in c.splitlines() if l.strip()]
                fn = inp.get("filename", "").lower()
                if fn.endswith(".csv") or (lines and "," in lines[0]):
                    total_raw_records += max(0, len(lines) - 1)
                else:
                    total_raw_records += len(lines)
            else:
                total_raw_records += inp.get("records_count", 0)
        state.metrics.records_count = max(total_raw_records, len(deduped_events))

        # STEP 7: RAG KNOWLEDGE RETRIEVAL
        query = f"{state.title} " + " ".join(e.action_summary for e in deduped_events[:5])
        state.retrieved_context = self.kb_retriever.retrieve_context(query, top_k=4)

        # STEP 8: MULTI-AGENT REASONING (RCA, Impact, Severity, Action Items)
        state.status = IncidentStatus.REASONING
        state.rca_result = self.rca_agent.analyze(deduped_events, state.retrieved_context, metrics=state.metrics)
        state.impact_result = self.impact_agent.analyze(deduped_events)
        state.severity, _ = SeverityAgent.classify(deduped_events, state.impact_result)
        state.action_items = ActionItemAgent.generate_actions(state.rca_result, deduped_events, state.retrieved_context)

        # STEP 9: EVIDENCE GRAPH GENERATION
        state.evidence_graph = EvidenceGraphBuilder.build_graph(
            incident_id=state.incident_id,
            events=deduped_events,
            rca=state.rca_result
        )

        # STEP 10: SYNTHESIS & ADVERSARIAL CRITIC RETRY LOOP
        state.status = IncidentStatus.SYNTHESIZING
        retry = 0
        while retry <= state.max_retries:
            report = SynthesisAgent.synthesize_report(
                incident_id=state.incident_id,
                title=state.title,
                severity=state.severity,
                metrics=state.metrics,
                sorted_events=deduped_events,
                conflicts=state.conflicts,
                rca=state.rca_result,
                impact=state.impact_result,
                action_items=state.action_items
            )
            state.draft_report = report

            # Adversarial critic check
            audit_res = CriticAgent.audit_report(report, deduped_events, state.rca_result)
            state.audit_result = audit_res

            if audit_res.audit_passed:
                state.final_report = report
                state.status = IncidentStatus.AWAITING_REVIEW
                self._record_audit(state, "CRITIC_VERIFICATION_PASSED", {
                    "checked_claims": audit_res.checked_claims_count
                })
                break
            else:
                retry += 1
                state.retry_count = retry
                self._record_audit(state, "CRITIC_VERIFICATION_RETRY", {
                    "issue_type": audit_res.issue_type,
                    "issue_description": audit_res.issue_description,
                    "retry_attempt": retry
                })
                # If retry needed, adjust draft report or regenerate
                if retry > state.max_retries:
                    state.final_report = report
                    state.status = IncidentStatus.AWAITING_REVIEW
                    break

        return state

    def _calculate_metrics(
        self,
        events: List[ForensicEvent],
        raw_inputs: Optional[List[Dict[str, Any]]] = None,
        clusters: Optional[List[Any]] = None
    ) -> IncidentMetrics:
        if not events:
            return IncidentMetrics()

        anchored = [e for e in events if e.epoch_timestamp > 0.0]
        if not anchored:
            return IncidentMetrics()

        start_time = anchored[0].timestamp_utc
        # Find detection event: prefer explicit Detection/Triage after start_time, or first error alert
        detect_evt = next((e for e in anchored if e.phase in ["Detection", "Triage"] and e.epoch_timestamp > anchored[0].epoch_timestamp), None)
        if not detect_evt:
            detect_evt = next((e for e in anchored if e.severity in ["error", "critical"] and e.epoch_timestamp > anchored[0].epoch_timestamp), None)
        if not detect_evt:
            detect_evt = next((e for e in anchored if e.phase == "Detection"), anchored[0])

        mitigate_evt = next((e for e in anchored if e.phase == "Mitigation"), None)
        resolve_evt = next((e for e in reversed(anchored) if e.phase == "Resolution"), anchored[-1])

        custom_mttr_sec: Optional[float] = None
        custom_mttd_sec: Optional[float] = None
        custom_duration_sec: Optional[float] = None

        stat_profile: Optional[Dict[str, Any]] = None

        # Check raw_inputs for high-performance data science statistical profiling across 100k-500k+ records
        if raw_inputs:
            for inp in raw_inputs:
                content = inp.get("content", "")
                if not content:
                    continue
                fn = inp.get("filename", "").lower()
                profile = DatasetStatisticalProfiler.profile_content(content, filename=fn)
                if profile and profile.get("total_records", 0) > 0:
                    stat_profile = profile
                    if profile.get("mean_mttr_sec") is not None:
                        custom_mttr_sec = profile["mean_mttr_sec"]
                    if profile.get("mean_mttd_sec") is not None:
                        custom_mttd_sec = profile["mean_mttd_sec"]
                    if profile.get("duration_sec") is not None:
                        custom_duration_sec = profile["duration_sec"]
                    if profile.get("start_utc"):
                        start_time = profile["start_utc"]
                    break

        # If multi-day/year span and no tabular resolution column was present:
        if custom_mttr_sec is None:
            time_span = anchored[-1].epoch_timestamp - anchored[0].epoch_timestamp
            if time_span > 86400:
                if clusters:
                    err_clusters = [c for c in clusters if any(e.severity in ["error", "critical"] for e in events if e.cluster_id == c.cluster_id)]
                    if err_clusters:
                        c = err_clusters[0]
                        c_evts = [e for e in events if e.cluster_id == c.cluster_id and e.epoch_timestamp > 0]
                        if len(c_evts) >= 2:
                            cluster_span = c_evts[-1].epoch_timestamp - c_evts[0].epoch_timestamp
                            if cluster_span > 60.0:
                                custom_mttr_sec = cluster_span
                                custom_mttd_sec = min(max(180.0, cluster_span * 0.25), 3600.0)
                                custom_duration_sec = cluster_span
                if custom_mttr_sec is None:
                    res_evts = [e for e in anchored if e.phase == "Resolution"]
                    det_evts = [e for e in anchored if e.phase in ["Detection", "Triage"]]
                    if res_evts and det_evts:
                        custom_mttr_sec = max(300.0, res_evts[-1].epoch_timestamp - det_evts[0].epoch_timestamp)
                        custom_mttd_sec = max(60.0, det_evts[0].epoch_timestamp - anchored[0].epoch_timestamp)
                        custom_duration_sec = time_span
                    else:
                        custom_mttr_sec = max(300.0, time_span / max(1, len(anchored)))
                        custom_mttd_sec = custom_mttr_sec * 0.2
                        custom_duration_sec = time_span

        rec_count = stat_profile.get("total_records", len(events)) if stat_profile else len(events)

        return TemporalNormalizer.calculate_incident_metrics(
            start_time_iso=start_time,
            detection_time_iso=detect_evt.timestamp_utc,
            mitigation_time_iso=mitigate_evt.timestamp_utc if mitigate_evt else None,
            resolution_time_iso=resolve_evt.timestamp_utc,
            custom_mttr_seconds=custom_mttr_sec,
            custom_mttd_seconds=custom_mttd_sec,
            custom_duration_seconds=custom_duration_sec,
            stat_profile=stat_profile,
            records_count=rec_count
        )

    def _record_audit(self, state: PipelineState, action: str, details: Dict[str, Any]):
        entry = AuditLogEntry(
            id=f"AUD-{len(state.audit_trail)+1:03d}",
            incident_id=state.incident_id,
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
            user_or_agent="IncidentOrchestrator",
            action=action,
            details=details
        )
        state.audit_trail.append(entry)
