"""
Evidence Graph DAG Engine.
Builds an explainable causal graph connecting Incidents, Events, Services, Actors,
Deployments, Alerts, Actions, and Post-Mortem Claims.
"""
from typing import List, Dict, Any
from backend.models.event import ForensicEvent
from backend.models.rca import RCAResult, GroundedClaim

class EvidenceGraphBuilder:
    @staticmethod
    def build_graph(
        incident_id: str,
        events: List[ForensicEvent],
        rca: RCAResult
    ) -> Dict[str, Any]:
        nodes: List[Dict[str, Any]] = []
        edges: List[Dict[str, Any]] = []
        seen_nodes = set()

        def add_node(node_id: str, label: str, node_type: str, metadata: Dict[str, Any] = None):
            if node_id not in seen_nodes:
                seen_nodes.add(node_id)
                nodes.append({
                    "id": node_id,
                    "label": label,
                    "type": node_type,
                    "metadata": metadata or {}
                })

        def add_edge(source: str, target: str, relationship: str):
            edges.append({
                "source": source,
                "target": target,
                "relationship": relationship
            })

        # 1. Incident Root Node
        add_node(incident_id, f"Incident {incident_id}", "incident")

        # 2. Add Services & Actors
        for e in events:
            # Event Node
            add_node(e.event_id, f"{e.action_summary[:35]}...", "event", {
                "timestamp_utc": e.timestamp_utc,
                "phase": e.phase,
                "severity": e.severity,
                "quote": e.raw_evidence_quote
            })
            add_edge(incident_id, e.event_id, "CONTAINS_EVENT")

            # Service Node
            if e.service_affected and e.service_affected != "unspecified":
                svc_id = f"SVC-{e.service_affected}"
                add_node(svc_id, e.service_affected, "service")
                add_edge(e.event_id, svc_id, "AFFECTS_SERVICE")

            # Actor Node
            if e.actor and e.actor != "system":
                actor_id = f"ACTOR-{e.actor}"
                add_node(actor_id, f"@{e.actor}", "actor")
                add_edge(actor_id, e.event_id, "TRIGGERED")

            # Check if Deployment
            if "deploy" in e.action_summary.lower():
                dep_id = f"DEP-{e.event_id}"
                add_node(dep_id, "Production Deployment", "deployment")
                add_edge(dep_id, e.event_id, "INITIATED_BY")

        # 3. Connect Chronological Event Sequence
        for i in range(len(events) - 1):
            add_edge(events[i].event_id, events[i+1].event_id, "PRECEDES")

        # 4. Connect Root Cause and Grounded Claims
        rca_node_id = f"RCA-{incident_id}"
        add_node(rca_node_id, rca.root_cause[:45] + "...", "root_cause", {
            "full_root_cause": rca.root_cause,
            "is_conclusive": rca.is_conclusive,
            "confidence": rca.confidence_score
        })
        add_edge(incident_id, rca_node_id, "EXPLAINS_ROOT_CAUSE")

        # Connect claims to supporting events
        for claim in rca.grounded_claims:
            add_node(claim.claim_id, claim.claim_text[:40] + "...", "claim", {
                "claim_type": claim.claim_type.value,
                "confidence": claim.confidence_score
            })
            add_edge(rca_node_id, claim.claim_id, "CLAIMS")
            for eid in claim.supporting_event_ids:
                if eid in seen_nodes:
                    add_edge(claim.claim_id, eid, "SUPPORTED_BY_EVIDENCE")

        return {
            "incident_id": incident_id,
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "nodes": nodes,
            "edges": edges
        }
