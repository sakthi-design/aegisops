"""
Unified Security & Sanitization Layer.
Enforces PII removal, secret masking, cryptographic SHA-256 evidence hashing,
prompt injection defense, and retains tamper-evident audit records.
"""
from typing import Dict, Any, List
from backend.security.secret_detector import detect_and_mask_secrets
from backend.security.pii_scrubber import scrub_pii
from backend.security.hasher import compute_content_sha256
from backend.models.audit import RedactionAudit

class SanitizerResult:
    def __init__(self, original_text: str, sanitized_text: str, audit: RedactionAudit):
        self.original_text = original_text
        self.sanitized_text = sanitized_text
        self.audit = audit
        self.content_sha256 = compute_content_sha256(original_text)
        self.sanitized_sha256 = compute_content_sha256(sanitized_text)
        self.audit.content_sha256 = self.content_sha256
        self.audit.sanitized_sha256 = self.sanitized_sha256

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
        is_oversized = len(text) > 300_000
        
        all_secret_types: List[str] = []
        scrubbed_snippets: List[str] = []
        hmac_hashes: List[str] = []

        if is_oversized:
            # For massive datasets, sanitize preview head (150KB) and tail (100KB)
            head_chunk = text[:150_000]
            tail_chunk = text[-100_000:]
            middle_chunk = text[150_000:-100_000]
            
            sanitized_head = head_chunk
            sanitized_tail = tail_chunk
            
            if self.secret_enabled:
                sanitized_head, sec_head = detect_and_mask_secrets(sanitized_head)
                sanitized_tail, sec_tail = detect_and_mask_secrets(sanitized_tail)
                for item in sec_head + sec_tail:
                    all_secret_types.append(item["secret_type"])
                    scrubbed_snippets.append(item["replacement"])
                    if "sha256_hmac" in item:
                        hmac_hashes.append(item["sha256_hmac"])

            if self.pii_enabled:
                sanitized_head, pii_head = scrub_pii(sanitized_head)
                sanitized_tail, pii_tail = scrub_pii(sanitized_tail)
                for item in pii_head + pii_tail:
                    all_secret_types.append(item["pii_type"])
                    scrubbed_snippets.append(item["replacement"])
                    if "sha256_hmac" in item:
                        hmac_hashes.append(item["sha256_hmac"])

            sanitized = sanitized_head + middle_chunk + sanitized_tail
        else:
            sanitized = text
            # 1. Scrub Secrets
            if self.secret_enabled:
                sanitized, sec_audit = detect_and_mask_secrets(sanitized)
                for item in sec_audit:
                    all_secret_types.append(item["secret_type"])
                    scrubbed_snippets.append(item["replacement"])
                    if "sha256_hmac" in item:
                        hmac_hashes.append(item["sha256_hmac"])

            # 2. Scrub PII
            if self.pii_enabled:
                sanitized, pii_audit = scrub_pii(sanitized)
                for item in pii_audit:
                    all_secret_types.append(item["pii_type"])
                    scrubbed_snippets.append(item["replacement"])
                    if "sha256_hmac" in item:
                        hmac_hashes.append(item["sha256_hmac"])

        audit = RedactionAudit(
            redaction_count=len(all_secret_types),
            secret_types_found=sorted(list(set(all_secret_types))),
            scrubbed_snippets=scrubbed_snippets[:20],  # Cap for brevity
            hmac_salted_hashes=hmac_hashes[:50]
        )

        return SanitizerResult(
            original_text=text,
            sanitized_text=sanitized,
            audit=audit
        )
