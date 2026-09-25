"""
Claim Verifier and Factuality Checker.
Verifies that generated narrative claims are mathematically and textually grounded
in extracted forensic evidence quotes.
"""
from typing import List, Dict, Any, Tuple
import re
from backend.models.event import ForensicEvent
from backend.models.rca import GroundedClaim, AuditResult

class ClaimVerifier:
    @staticmethod
    def verify_claims(
        claims: List[GroundedClaim],
        events: List[ForensicEvent]
    ) -> AuditResult:
        if not claims:
            return AuditResult(
                audit_passed=True,
                checked_claims_count=0,
                passed_claims_count=0
            )

        event_map = {e.event_id: e for e in events}
        passed_count = 0

        for claim in claims:
            # 1. Check if supporting event IDs exist in the incident
            if not claim.supporting_event_ids:
                return AuditResult(
                    audit_passed=False,
                    issue_type="UNSUPPORTED_CLAIM",
                    issue_description=f"Claim '{claim.claim_id}' lacks supporting event ID citations.",
                    checked_claims_count=len(claims),
                    passed_claims_count=passed_count
                )

            for eid in claim.supporting_event_ids:
                if eid not in event_map:
                    return AuditResult(
                        audit_passed=False,
                        issue_type="INVALID_EVIDENCE_CITATION",
                        issue_description=f"Claim references non-existent event ID '{eid}'.",
                        checked_claims_count=len(claims),
                        passed_claims_count=passed_count
                    )

            # 2. Check for metric contradictions
            # E.g. If claim states 100% saturation but evidence states 82%
            claim_pct = re.findall(r"\b(\d+)%", claim.claim_text)
            for cpct in claim_pct:
                for eid in claim.supporting_event_ids:
                    quote = event_map[eid].raw_evidence_quote
                    evidence_pct = re.findall(r"\b(\d+)%", quote)
                    if evidence_pct and cpct not in evidence_pct:
                        return AuditResult(
                            audit_passed=False,
                            issue_type="METRIC_CONTRADICTION",
                            issue_description=(
                                f"Claim asserts metric {cpct}%, but evidence quote in {eid} says: '{quote}'"
                            ),
                            contradicting_event_id=eid,
                            checked_claims_count=len(claims),
                            passed_claims_count=passed_count
                        )

            passed_count += 1

        return AuditResult(
            audit_passed=True,
            checked_claims_count=len(claims),
            passed_claims_count=passed_count
        )
