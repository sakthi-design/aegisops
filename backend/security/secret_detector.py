"""
Security Engine: Secret and Credential Detection via Pattern Matching and Shannon Entropy.
"""
import re
import math
from typing import Tuple, List, Dict

SECRET_PATTERNS = {
    "OPENAI_API_KEY": re.compile(r"sk-[a-zA-Z0-9_-]{20,64}"),
    "AWS_ACCESS_KEY": re.compile(r"\b(AKIA|ABIA|ACCA)[0-9A-Z]{16}\b"),
    "AWS_SECRET_KEY": re.compile(r"(?i)aws_secret_access_key\s*[:=]\s*([a-zA-Z0-9/+=]{40})"),
    "SLACK_TOKEN": re.compile(r"xox[baprs]-[0-9A-Za-z]{10,48}"),
    "GITHUB_TOKEN": re.compile(r"gh[pousr]-[0-9a-zA-Z]{36}"),
    "JWT_TOKEN": re.compile(r"\beyJ[a-zA-Z0-9_-]{10,}\.eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}\b"),
    "GENERIC_BEARER_TOKEN": re.compile(r"(?i)bearer\s+([a-zA-Z0-9_\-\.]{24,})"),
    "PASSWORD_ASSIGNMENT": re.compile(r"(?i)(password|passwd|pwd|db_pass|secret_key)\s*[:=]\s*['\"]?([^\s'\";\n]+)['\"]?"),
    "PRIVATE_IPV4": re.compile(r"\b(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3})\b"),
}

def calculate_shannon_entropy(data: str) -> float:
    """Calculates the Shannon entropy of a string to identify cryptographic random secrets."""
    if not data:
        return 0.0
    entropy = 0.0
    length = len(data)
    frequencies = {}
    for char in data:
        frequencies[char] = frequencies.get(char, 0) + 1
    for count in frequencies.values():
        p = count / length
        entropy -= p * math.log2(p)
    return entropy

def detect_and_mask_secrets(text: str) -> Tuple[str, List[Dict[str, str]]]:
    """
    Scans text, masks all matched credentials with [REDACTED_<TYPE>],
    and produces an audit record of masked secrets without leaking secret values.
    """
    audit_records = []
    sanitized = text

    # 1. Regex Pattern Matching
    for sec_type, pattern in SECRET_PATTERNS.items():
        matches = list(pattern.finditer(sanitized))
        for m in reversed(matches):
            raw_match = m.group(0)
            replacement = f"[REDACTED_{sec_type}]"
            start, end = m.span()
            sanitized = sanitized[:start] + replacement + sanitized[end:]
            audit_records.append({
                "secret_type": sec_type,
                "length": len(raw_match),
                "replacement": replacement
            })

    # 2. Entropy Scan on alphanumeric tokens of length > 24
    tokens = re.findall(r"\b[A-Za-z0-9+/=]{24,64}\b", sanitized)
    for token in tokens:
        # Ignore already redacted placeholders
        if token.startswith("REDACTED"):
            continue
        entropy = calculate_shannon_entropy(token)
        # Random keys typically have entropy > 4.2
        if entropy > 4.2:
            replacement = "[REDACTED_HIGH_ENTROPY_SECRET]"
            sanitized = sanitized.replace(token, replacement)
            audit_records.append({
                "secret_type": "HIGH_ENTROPY_TOKEN",
                "length": len(token),
                "entropy": round(entropy, 2),
                "replacement": replacement
            })

    return sanitized, audit_records
