"""
Security Engine: Personally Identifiable Information (PII) Scrubber with Cryptographic Hashing.
"""
import re
from typing import Tuple, List, Dict
from backend.security.hasher import compute_hmac_sha256

PII_PATTERNS = {
    "EMAIL": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b"),
    "PHONE_NUMBER": re.compile(r"\b(?:[+]?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
    "CREDIT_CARD": re.compile(r"\b(?:\d{4}[ -]?){3}\d{4}\b"),
    "SSN": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "CUSTOMER_ID": re.compile(r"\b(?i:CUST|CUSTOMER)[-_]?[0-9A-Za-z]*[0-9][0-9A-Za-z]*\b"),
    "TICKET_ID": re.compile(r"\b(?i:TCKT|TICKET)[-_]?[0-9A-Za-z]*[0-9][0-9A-Za-z]*\b")
}

def scrub_pii(text: str) -> Tuple[str, List[Dict[str, str]]]:
    """
    Scrubs emails, phone numbers, credit card sequences, SSNs, customer IDs, and ticket IDs.
    Replaces sensitive data with deterministic cryptographic HMAC-SHA256 pseudonym tokens:
    [REDACTED_<TYPE>][SHA256:<HASH>].
    Returns (sanitized_text, audit_list).
    """
    if not text:
        return "", []

    audit = []
    sanitized = text

    for pii_type, pattern in PII_PATTERNS.items():
        matches = list(pattern.finditer(sanitized))
        for m in reversed(matches):
            raw = m.group(0)
            token_hash = compute_hmac_sha256(raw, length=12)
            replacement = f"[REDACTED_{pii_type}][SHA256:{token_hash}]"
            start, end = m.span()
            sanitized = sanitized[:start] + replacement + sanitized[end:]
            audit.append({
                "pii_type": pii_type,
                "length": len(raw),
                "replacement": replacement,
                "sha256_hmac": token_hash
            })

    return sanitized, audit
