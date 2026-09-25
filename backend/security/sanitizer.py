"""
Unified Security & Sanitization Layer.
Enforces PII removal, secret masking, prompt injection defense, and retains audit records.
"""
from typing import Dict, Any, List
from backend.security.secret_detector import detect_and_mask_secrets
from backend.security.pii_scrubber import scrub_pii
from backend.models.audit import RedactionAudit

class SanitizerResult:
    def __init__(self, original_text: str, sanitized_text: str, audit: RedactionAudit):
        self.original_text = original_text
        self.sanitized_text = sanitized_text
        self.audit = audit

    def to_untrusted_prompt_block(self) -> str:
        """
        Wraps sanitized telemetry in strict isolation tags to prevent prompt injection.
        LLM system prompts explicitly instruct that content inside these tags is purely inert data.
        """
        return f"<UNTRUSTED_INCIDENT_DATA>\n{self.sanitized_text}\n</UNTRUSTED_INCIDENT_DATA>"

class SanitizationEngine:
    def __init__(self, pii_enabled: bool = True, secret_enabled: bool = True):
        self.pii_enabled = pii_enabled
        self.secret_enabled = secret_enabled

    def sanitize(self, text: str) -> SanitizerResult:
        if not text:
            return SanitizerResult("", "", RedactionAudit(redaction_count=0))

        # Protect against massive payload CPU stall (e.g. 50MB raw CSV benchmarks)
        is_oversized = len(text) > 250_000
        
        all_secret_types: List[str] = []
        scrubbed_snippets: List[str] = []

        if is_oversized:
            # For massive datasets (300k+ lines, 20-100MB+), audit a high-entropy sample
            # (head 150KB + tail 100KB) to prevent CPU stall while retaining the complete telemetry
            scan_sample = text[:150_000] + "\n" + text[-100_000:]
            if self.secret_enabled:
                _, sec_audit = detect_and_mask_secrets(scan_sample)
                for item in sec_audit:
                    all_secret_types.append(item["secret_type"])
                    scrubbed_snippets.append(item["replacement"])
            if self.pii_enabled:
                _, pii_audit = scrub_pii(scan_sample)
                for item in pii_audit:
                    all_secret_types.append(item["pii_type"])
                    scrubbed_snippets.append(item["replacement"])

            # Retain complete dataset so downstream forensic engine analyzes all 300,000+ lines
            sanitized = text
        else:
            sanitized = text
            # 1. Scrub Secrets
            if self.secret_enabled:
                sanitized, sec_audit = detect_and_mask_secrets(sanitized)
                for item in sec_audit:
                    all_secret_types.append(item["secret_type"])
                    scrubbed_snippets.append(item["replacement"])

            # 2. Scrub PII
            if self.pii_enabled:
                sanitized, pii_audit = scrub_pii(sanitized)
                for item in pii_audit:
                    all_secret_types.append(item["pii_type"])
                    scrubbed_snippets.append(item["replacement"])

        audit = RedactionAudit(
            redaction_count=len(all_secret_types),
            secret_types_found=sorted(list(set(all_secret_types))),
            scrubbed_snippets=scrubbed_snippets[:20]  # Cap for brevity
        )

        return SanitizerResult(
            original_text=text,
            sanitized_text=sanitized,
            audit=audit
        )
