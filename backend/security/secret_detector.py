"""
Security Engine: Secret and Credential Detection via Pattern Matching, Shannon Entropy,
and Cryptographic HMAC-SHA256 Pseudonymization.
"""
import re
import math
from typing import Tuple, List, Dict
from backend.security.hasher import compute_hmac_sha256

SECRET_PATTERNS = {
    "OPENAI_API_KEY": re.compile(r"sk-[a-zA-Z0-9_-]{20,64}"),
    "AWS_ACCESS_KEY": re.compile(r"\b(AKIA|ABIA|ACCA)[0-9A-Z]{16}\b"),
    "AWS_SECRET_KEY": re.compile(r"(?i)aws_secret_access_key\s*[:=]\s*([a-zA-Z0-9/+=]{40})"),
    "SLACK_TOKEN": re.compile(r"xox[baprs]-[0-9A-Za-z]{10,48}"),
    "GITHUB_TOKEN": re.compile(r"gh[pousr]-[0-9a-zA-Z]{36}"),
    "JWT_TOKEN": re.compile(r"\beyJ[a-zA-Z0-9_-]{10,}\.eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}\b"),
    "GENERIC_BEARER_TOKEN": re.compile(r"(?i)bearer\s+([a-zA-Z0-9_\-\.]{24,})"),
    "PASSWORD_ASSIGNMENT": re.compile(r"""(?i)\b(password|passwd|pwd|db_pass|secret_key)\s*[:=]\s*(?:['"]([^'"\r\n]+)['"]|(?!(?:password|passwd|pwd|db_pass|secret_key)\b)([^\s'",;]+))"""),
    "PRIVATE_IPV4": re.compile(r"\b(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3})\b"),
}

def calculate_shannon_entropy(data: str) -> float:
    """Calculates the Shannon entropy of a string to identify cryptographic random secrets."""
    if not data:
        return 0.0
    entropy = 0.0
    length = len(data)
    frequencies: Dict[str, int] = {}
    for char in data:
        frequencies[char] = frequencies.get(char, 0) + 1
    for count in frequencies.values():
        p = count / length
        entropy -= p * math.log2(p)
    return entropy

def detect_and_mask_secrets(text: str) -> Tuple[str, List[Dict[str, str]]]:
    """
    Scans text, masks all matched credentials with cryptographic SHA256 HMAC tags:
    [REDACTED_<TYPE>][SHA256:<HASH>], and produces a tamper-proof audit record.
    """
    if not text:
        return "", []

    audit_records = []
    sanitized = text

    # 1. Regex Pattern Matching
    for sec_type, pattern in SECRET_PATTERNS.items():
        matches = list(pattern.finditer(sanitized))
        for m in reversed(matches):
            raw_match = m.group(0)

            if sec_type == "PASSWORD_ASSIGNMENT":
                key_prefix = m.group(1)
                secret_raw = m.group(2) or m.group(3) or raw_match
                token_hash = compute_hmac_sha256(secret_raw, length=12)
                replacement = f"{key_prefix}=[REDACTED_PASSWORD][SHA256:{token_hash}]"
            elif sec_type == "AWS_SECRET_KEY":
                secret_raw = m.group(1) if m.groups() else raw_match
                token_hash = compute_hmac_sha256(secret_raw, length=12)
                replacement = f"aws_secret_access_key=[REDACTED_AWS_SECRET_KEY][SHA256:{token_hash}]"
            elif sec_type == "GENERIC_BEARER_TOKEN":
                secret_raw = m.group(1) if m.groups() else raw_match
                token_hash = compute_hmac_sha256(secret_raw, length=12)
                replacement = f"Bearer [REDACTED_GENERIC_BEARER_TOKEN][SHA256:{token_hash}]"
            else:
                token_hash = compute_hmac_sha256(raw_match, length=12)
                replacement = f"[REDACTED_{sec_type}][SHA256:{token_hash}]"

            start, end = m.span()
            sanitized = sanitized[:start] + replacement + sanitized[end:]
            audit_records.append({
                "secret_type": sec_type,
                "length": len(raw_match),
                "replacement": replacement,
                "sha256_hmac": token_hash
            })

    # 2. Entropy Scan on alphanumeric tokens of length > 24
    tokens = re.findall(r"\b[A-Za-z0-9+/=]{24,64}\b", sanitized)
    for token in tokens:
        # Ignore already redacted placeholders or hashes
        if token.startswith("REDACTED") or "SHA256" in token:
            continue
        entropy = calculate_shannon_entropy(token)
        # Random keys typically have entropy > 4.2
        if entropy > 4.2:
            token_hash = compute_hmac_sha256(token, length=12)
            replacement = f"[REDACTED_HIGH_ENTROPY_SECRET][SHA256:{token_hash}]"
            sanitized = sanitized.replace(token, replacement)
            audit_records.append({
                "secret_type": "HIGH_ENTROPY_TOKEN",
                "length": len(token),
                "entropy": round(entropy, 2),
                "replacement": replacement,
                "sha256_hmac": token_hash
            })

    return sanitized, audit_records
