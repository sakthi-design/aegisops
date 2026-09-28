"""
Unit and Integration Tests for Cryptographic Hashing and Zero-Trust Security.
"""
import pytest
from backend.security.hasher import (
    compute_content_sha256,
    compute_hmac_sha256,
    verify_content_integrity
)
from backend.security.secret_detector import detect_and_mask_secrets, calculate_shannon_entropy
from backend.security.pii_scrubber import scrub_pii
from backend.security.sanitizer import SanitizationEngine

def test_content_sha256_deterministic():
    content = "2026-09-25T14:02:11Z [ERROR] payment-gateway timeout after 30s"
    hash1 = compute_content_sha256(content)
    hash2 = compute_content_sha256(content)
    assert len(hash1) == 64
    assert hash1 == hash2
    assert compute_content_sha256("") == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

def test_verify_content_integrity():
    content = "telemetry log content"
    valid_hash = compute_content_sha256(content)
    assert verify_content_integrity(content, valid_hash) is True
    # Tampered content
    assert verify_content_integrity(content + " tampered", valid_hash) is False

def test_hmac_sha256_pseudonymization():
    secret_a = "sk-proj-992182049103829"
    secret_b = "sk-proj-992182049103829"
    secret_c = "sk-proj-different-secret-token"
    
    hash_a = compute_hmac_sha256(secret_a)
    hash_b = compute_hmac_sha256(secret_b)
    hash_c = compute_hmac_sha256(secret_c)
    
    assert hash_a == hash_b  # Deterministic for the same secret across logs
    assert hash_a != hash_c  # Unique per secret
    assert len(hash_a) == 12

def test_detect_and_mask_secrets_with_sha256():
    raw_log = (
        "Connected using sk-proj-1234567890abcdef12345678 and AKIAIOSFODNN7EXAMPLE. "
        "Database password: db_pass='SuperSecretP@ssword2026!' on host 10.0.1.45."
    )
    sanitized, audit = detect_and_mask_secrets(raw_log)
    
    assert "sk-proj-" not in sanitized
    assert "AKIAIOSFODNN7EXAMPLE" not in sanitized
    assert "SuperSecretP@ssword2026!" not in sanitized
    assert "10.0.1.45" not in sanitized
    
    # Verify SHA-256 HMAC tags are embedded in the sanitized stream
    assert "[SHA256:" in sanitized
    assert "[REDACTED_OPENAI_API_KEY]" in sanitized
    assert "[REDACTED_AWS_ACCESS_KEY]" in sanitized
    assert "[REDACTED_PRIVATE_IPV4]" in sanitized
    assert "[REDACTED_PASSWORD]" in sanitized
    
    # Verify audit record integrity
    assert len(audit) >= 4
    for record in audit:
        assert "sha256_hmac" in record
        assert len(record["sha256_hmac"]) == 12

def test_scrub_pii_with_sha256_pseudonymization():
    text = (
        "User CUST_00861 reported issue on ticket TCKT_000001. "
        "Email: support.agent@fintech.com, Phone: +1-555-019-2834."
    )
    sanitized, audit = scrub_pii(text)
    
    assert "CUST_00861" not in sanitized
    assert "TCKT_000001" not in sanitized
    assert "support.agent@fintech.com" not in sanitized
    assert "+1-555-019-2834" not in sanitized
    
    assert "[REDACTED_CUSTOMER_ID]" in sanitized
    assert "[REDACTED_TICKET_ID]" in sanitized
    assert "[REDACTED_EMAIL]" in sanitized
    assert "[REDACTED_PHONE_NUMBER]" in sanitized
    assert "[SHA256:" in sanitized

def test_sanitization_engine_produces_tamper_proof_hashes():
    engine = SanitizationEngine()
    log = "Incident detected for customer CUST_99182 with key sk-proj-12345678901234567890."
    res = engine.sanitize(log)
    
    assert len(res.content_sha256) == 64
    assert len(res.sanitized_sha256) == 64
    assert res.content_sha256 != res.sanitized_sha256
    assert res.audit.content_sha256 == res.content_sha256
    assert res.audit.sanitized_sha256 == res.sanitized_sha256
    assert res.audit.redaction_count >= 2
    assert len(res.audit.hmac_salted_hashes) >= 2
