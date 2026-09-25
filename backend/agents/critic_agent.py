"""
Adversarial Fact Checker / Critic Agent.
Audits synthesized incident report against raw telemetry and forensic claims.
Triggers regeneration on hallucinated services, metric contradictions, or fake SHAs.
"""
from typing import Dict, Any, List
import re
from backend.models.event import ForensicEvent
from backend.models.rca import RCAResult, AuditResult
from backend.evidence.claim_verifier import ClaimVerifier

class CriticAgent:
    @staticmethod
    def audit_report(
        report: Dict[str, Any],
        events: List[ForensicEvent],
        rca: RCAResult
    ) -> AuditResult:
        # 1. Verify Grounded Claims via ClaimVerifier
        claim_result = ClaimVerifier.verify_claims(rca.grounded_claims, events)
        if not claim_result.audit_passed:
            return claim_result

        # 2. Check for Hallucinated Commit SHAs
        # If report mentions a git commit SHA, verify that SHA exists in raw telemetry quotes
        all_quotes = " ".join(e.raw_evidence_quote for e in events)
        report_text = str(report)

        report_shas = set(re.findall(r"\b[0-9a-f]{7,40}\b", report_text, re.IGNORECASE))
        for sha in report_shas:
            # Ignore common non-SHA hex or words
            if len(sha) < 7 or sha.isdigit() or sha.lower() in ["default", "success", "failure"]:
                continue
            if sha not in all_quotes:
                return AuditResult(
                    audit_passed=False,
                    issue_type="HALLUCINATED_COMMIT_SHA",
                    issue_description=f"Report mentions commit SHA '{sha}' which is not present in raw operational evidence.",
                    checked_claims_count=len(rca.grounded_claims),
                    passed_claims_count=0
                )

        # 3. Check for Hallucinated Services
        # Ensure any service mentioned in the executive summary appears in the extracted event stream
        known_services = set(e.service_affected.lower() for e in events if e.service_affected != "unspecified")
        exec_summary = report.get("section_01_executive_summary", "").lower()
        
        # Candidate services formatted with -service or -processor
        mentioned_candidates = re.findall(r"\b[a-z0-9_\-]+(?:-service|-processor|-api)\b", exec_summary)
        for cand in mentioned_candidates:
            if known_services and cand not in known_services:
                return AuditResult(
                    audit_passed=False,
                    issue_type="HALLUCINATED_SERVICE",
                    issue_description=f"Executive summary mentions service '{cand}' which was never observed in incident telemetry.",
                    checked_claims_count=len(rca.grounded_claims),
                    passed_claims_count=0
                )

        return AuditResult(
            audit_passed=True,
            checked_claims_count=len(rca.grounded_claims),
            passed_claims_count=len(rca.grounded_claims)
        )
