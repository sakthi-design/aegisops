"""
Severity Classification Agent.
Evaluates incident severity (P0, P1, P2, P3) based on enterprise operational policy,
impact scope, and affected service criticality.
"""
from typing import List, Tuple
from backend.models.incident import SeverityLevel
from backend.models.event import ForensicEvent
from backend.models.rca import ImpactAnalysis

class SeverityAgent:
    CRITICAL_SERVICES = ["payment-processor", "auth-service", "payments-db", "database", "api-gateway"]

    @classmethod
    def classify(cls, events: List[ForensicEvent], impact: ImpactAnalysis) -> Tuple[SeverityLevel, str]:
        if not events:
            return SeverityLevel.P3, "Default low severity: No operational events detected."

        has_critical_error = any(e.severity == "critical" for e in events)
        has_error = any(e.severity == "error" for e in events)
        
        touches_critical_svc = any(
            any(crit in e.service_affected.lower() for crit in cls.CRITICAL_SERVICES)
            for e in events
        )

        # Policy evaluation:
        # P0: Critical severity event or critical core service outage
        if has_critical_error and touches_critical_svc:
            return (
                SeverityLevel.P0,
                "Classified P0 (Critical Outage): Outage of critical payment/database path with active customer disruption."
            )
        
        if has_critical_error or (has_error and touches_critical_svc):
            return (
                SeverityLevel.P1,
                "Classified P1 (High Impact): Severe degradation of core microservice requiring immediate engineering intervention."
            )

        if has_error:
            return (
                SeverityLevel.P2,
                "Classified P2 (Medium Impact): Isolated component errors or threshold breach with partial service redundancy."
            )

        return (
            SeverityLevel.P3,
            "Classified P3 (Low Impact): Informational or minor telemetry event with no detected user facing failure."
        )
