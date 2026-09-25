"""
Deterministic Conflict Detection Engine.
Detects contradictions between operational sources (e.g. Slack conversation vs Jira ticket)
and flags TEMPORAL_CONFLICT rather than silently hallucinating a single arbitrary resolution.
"""
from typing import List
from backend.models.event import ForensicEvent, TemporalConflict

class ConflictDetector:
    @staticmethod
    def detect_conflicts(events: List[ForensicEvent]) -> List[TemporalConflict]:
        conflicts: List[TemporalConflict] = []
        conflict_counter = 1

        # Key action phrases that indicate critical state transitions
        action_keywords = ["rollback", "restart", "deploy", "failover", "mitigate", "resolve", "patch"]

        for i in range(len(events)):
            evt_a = events[i]
            action_a_lower = evt_a.action_summary.lower()
            
            matching_keyword = next((kw for kw in action_keywords if kw in action_a_lower), None)
            if not matching_keyword:
                continue

            for j in range(i + 1, len(events)):
                evt_b = events[j]
                action_b_lower = evt_b.action_summary.lower()

                # If same action keyword mentioned in different source channels
                if matching_keyword in action_b_lower and evt_a.source_channel != evt_b.source_channel:
                    # If services match or are related
                    if evt_a.service_affected == evt_b.service_affected or "unspecified" in [evt_a.service_affected, evt_b.service_affected]:
                        delta = abs(evt_a.epoch_timestamp - evt_b.epoch_timestamp)
                        # If difference is between 60s and 3600s, flag as conflicting reports
                        if 60.0 <= delta <= 3600.0:
                            conflicts.append(TemporalConflict(
                                conflict_id=f"CONF-{conflict_counter:03d}",
                                event_id_a=evt_a.event_id,
                                event_id_b=evt_b.event_id,
                                source_a=evt_a.source_channel,
                                source_b=evt_b.source_channel,
                                timestamp_a_utc=evt_a.timestamp_utc,
                                timestamp_b_utc=evt_b.timestamp_utc,
                                delta_seconds=delta,
                                description=(
                                    f"Temporal conflict on '{matching_keyword}' operation: "
                                    f"Source '{evt_a.source_channel}' reported at {evt_a.timestamp_utc}, "
                                    f"whereas source '{evt_b.source_channel}' reported at {evt_b.timestamp_utc} "
                                    f"(difference of {int(delta)} seconds)."
                                ),
                                resolution_status="UNRESOLVED"
                            ))
                            conflict_counter += 1

        return conflicts
