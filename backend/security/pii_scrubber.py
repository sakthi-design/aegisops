"""
Security Engine: Personally Identifiable Information (PII) Scrubber.
"""
import re
from typing import Tuple, List, Dict

PII_PATTERNS = {
    "EMAIL": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b"),
    "PHONE_NUMBER": re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
    "CREDIT_CARD": re.compile(r"\b(?:\d{4}[ -]?){3}\d{4}\b"),
    "SSN": re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
}

def scrub_pii(text: str) -> Tuple[str, List[Dict[str, str]]]:
    """
    Scrubs emails, phone numbers, credit card sequences, and SSNs.
    Returns (sanitized_text, audit_list).
    """
    audit = []
    sanitized = text

    for pii_type, pattern in PII_PATTERNS.items():
        matches = list(pattern.finditer(sanitized))
        for m in reversed(matches):
            raw = m.group(0)
            replacement = f"[REDACTED_{pii_type}]"
            start, end = m.span()
            sanitized = sanitized[:start] + replacement + sanitized[end:]
            audit.append({
                "pii_type": pii_type,
                "length": len(raw),
                "replacement": replacement
            })

    return sanitized, audit
