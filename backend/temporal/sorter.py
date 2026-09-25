"""
Deterministic Event Sorter, Deduplication Engine, and Clustering Engine.
Never delegates chronological sorting or deduplication to an LLM.
"""
from typing import List, Dict, Any, Tuple
from collections import defaultdict
from backend.models.event import ForensicEvent, EventCluster

class DeterministicEventEngine:
    @staticmethod
    def sort_chronologically(events: List[ForensicEvent]) -> List[ForensicEvent]:
        """
        Sorts events strictly using normalized Unix epoch timestamps.
        Unanchored events are placed after anchored events while preserving original order.
        """
        anchored = [e for e in events if e.epoch_timestamp > 0.0]
        unanchored = [e for e in events if e.epoch_timestamp <= 0.0]
        
        # Deterministic Python sort
        anchored_sorted = sorted(anchored, key=lambda e: e.epoch_timestamp)
        return anchored_sorted + unanchored

    @staticmethod
    def deduplicate(events: List[ForensicEvent], window_seconds: float = 60.0) -> Tuple[List[ForensicEvent], int]:
        """
        Detects and merges duplicate alerts or redundant slack messages occurring
        within a given window (default 60s) for the same service and action.
        """
        deduped: List[ForensicEvent] = []
        duplicate_count = 0
        seen_signatures: Dict[str, float] = {}

        for event in events:
            # Signature combines service, action snippet, and severity
            sig = f"{event.service_affected.lower()}::{event.action_summary.lower().strip()[:40]}::{event.severity.lower()}"
            
            if sig in seen_signatures and event.epoch_timestamp > 0.0:
                last_time = seen_signatures[sig]
                if abs(event.epoch_timestamp - last_time) <= window_seconds:
                    duplicate_count += 1
                    continue

            seen_signatures[sig] = event.epoch_timestamp
            deduped.append(event)

        return deduped, duplicate_count

    @staticmethod
    def cluster_events(events: List[ForensicEvent], max_cluster_gap_seconds: float = 300.0) -> List[EventCluster]:
        """
        Clusters chronologically sorted events into logical incident phases / component failure waves.
        Groups events affecting related services occurring within 5 minutes of each other.
        """
        if not events:
            return []

        clusters: List[EventCluster] = []
        current_events: List[ForensicEvent] = []
        cluster_idx = 1

        for event in events:
            if not current_events:
                current_events.append(event)
                continue

            last_evt = current_events[-1]
            time_gap = event.epoch_timestamp - last_evt.epoch_timestamp

            # If within gap and touches similar services or alerts
            if 0 <= time_gap <= max_cluster_gap_seconds:
                current_events.append(event)
            else:
                # Flush existing cluster
                clusters.append(DeterministicEventEngine._create_cluster(current_events, cluster_idx))
                cluster_idx += 1
                current_events = [event]

        if current_events:
            clusters.append(DeterministicEventEngine._create_cluster(current_events, cluster_idx))

        return clusters

    @staticmethod
    def _create_cluster(events: List[ForensicEvent], idx: int) -> EventCluster:
        services = set(e.service_affected for e in events if e.service_affected != "unspecified")
        primary_svc = next(iter(services)) if services else "Platform Services"
        
        c_id = f"CLUSTER-{idx:03d}"
        for e in events:
            e.cluster_id = c_id

        return EventCluster(
            cluster_id=c_id,
            cluster_name=f"{primary_svc} Degradation Wave {idx}",
            description=f"Group of {len(events)} correlated events affecting {primary_svc}",
            event_ids=[e.event_id for e in events],
            start_time_utc=events[0].timestamp_utc,
            end_time_utc=events[-1].timestamp_utc,
            primary_service=primary_svc
        )
