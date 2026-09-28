"""
Security Engine: Cryptographic Hashing and Deterministic Salted HMAC Pseudonymization.
Enforces SHA-256 evidence integrity and tamper-proof audit trails.
"""
import hashlib
import hmac
from typing import Optional

# Constant salt for deterministic token pseudonymization in the workspace
AEGISOPS_SALT = b"aegisops_enterprise_zero_trust_salt_2026_deterministic"

def compute_content_sha256(content: str) -> str:
    """
    Computes a cryptographic SHA-256 hash (64 hex characters) of string content.
    Used for tamper-proof telemetry evidence verification and audit logs.
    """
    if not content:
        return hashlib.sha256(b"").hexdigest()
    return hashlib.sha256(content.encode("utf-8")).hexdigest()

def compute_hmac_sha256(secret_val: str, salt: Optional[bytes] = None, length: int = 12) -> str:
    """
    Computes a deterministic, salted HMAC-SHA256 hash for sensitive tokens/PII.
    Enforces zero-data leakage while allowing security analysts to correlate
    repeated mentions of the same redacted entity across distributed logs.
    """
    if not secret_val:
        return ""
    active_salt = salt if salt is not None else AEGISOPS_SALT
    h = hmac.new(active_salt, secret_val.encode("utf-8"), hashlib.sha256)
    full_hex = h.hexdigest()
    return full_hex[:length] if length > 0 else full_hex

def verify_content_integrity(content: str, expected_sha256: str) -> bool:
    """
    Performs constant-time verification of content against an expected SHA-256 hash.
    Protects against timing attacks.
    """
    actual_sha256 = compute_content_sha256(content)
    return hmac.compare_digest(actual_sha256.lower(), expected_sha256.lower())
