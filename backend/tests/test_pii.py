"""Test Suite for EVAL-P2.1: PII Detection & Checksum Verification.

Tests 30 synthetic PII inputs:
- 10 PAN numbers (valid formatting, spaced, lowercase, and invalid 4th-char entity status).
- 10 Aadhaar numbers (valid Verhoeff checksums vs corrupted/benign 12-digit numbers).
- 10 Bank account, folio, and OTP/credential sequences.
"""

import pytest
from app.guardrails.pii import (
    PII_SECURITY_WARNING,
    scan_pii,
    verhoeff_checksum,
    verhoeff_validate,
)


class TestVerhoeffAlgorithm:
    """Verifies Dihedral D5 Verhoeff checksum calculation and validation."""

    def test_verhoeff_checksum_basic(self):
        # Known standard test vectors
        assert verhoeff_checksum("23") == "6"
        assert verhoeff_validate("236") is True
        assert verhoeff_validate("235") is False

    def test_verhoeff_aadhaar_validation(self):
        valid_aadhaars = [
            "367598345212",
            "999999990019",
            "234567890124",
            "543210987652",
            "876543210988",
        ]
        for v in valid_aadhaars:
            assert verhoeff_validate(v) is True, f"Expected {v} to be valid"
            # Invalidate check digit
            corrupted = v[:-1] + ("0" if v[-1] != "0" else "1")
            assert verhoeff_validate(corrupted) is False, f"Expected {corrupted} to be invalid"


class TestPANDetection:
    """Tests 10 PAN inputs covering formatting, entity types, spacing, and delimiters."""

    @pytest.mark.parametrize(
        "query,expected_detected",
        [
            ("My PAN is ABCPE1234F", True),
            ("Company PAN: XYZCA5678B registered with AMC", True),
            ("HUF PAN details: DEFHE9012C", True),
            ("Please check pan abcpe1234f for KYC", True),
            ("My pan is a b c p e 1 2 3 4 f", True),
            ("Delimited pan format ABCPE-1234-F", True),
            ("Trust PAN is ABCTE4321A", True),
            ("This is an invalid entity char ABCZE1234F", False),
            ("Non-entity number ABC1E1234F", False),
            ("Malformed non-PAN sequence ABCPE12345", False),
        ],
    )
    def test_pan_scanning(self, query: str, expected_detected: bool):
        has_pii, detected_types, redacted = scan_pii(query)
        if expected_detected:
            assert has_pii is True
            assert "PAN" in detected_types
            assert "[PAN_REDACTED]" in redacted
        else:
            assert "PAN" not in detected_types


class TestAadhaarDetection:
    """Tests 10 Aadhaar inputs verifying Verhoeff validation and false positive immunity."""

    @pytest.mark.parametrize(
        "query,expected_detected",
        [
            ("Aadhaar: 3675 9834 5212", True),
            ("Aadhaar with hyphens: 3675-9834-5212", True),
            ("Compact Aadhaar: 367598345212", True),
            ("Valid Aadhaar 2: 9999 9999 0019", True),
            ("Valid Aadhaar 3: 2345 6789 0124", True),
            ("Corrupted check digit: 3675 9834 5210", False),
            ("Random 12 digit number: 1234 5678 9012", False),
            ("Fund corpus AUM figure: 987654321098", False),
            ("Corrupted Aadhaar 2: 2345 6789 0120", False),
            ("Benign 10-digit number: 9876543210", False),
        ],
    )
    def test_aadhaar_scanning(self, query: str, expected_detected: bool):
        has_pii, detected_types, redacted = scan_pii(query)
        if expected_detected:
            assert has_pii is True
            assert "AADHAAR" in detected_types
            assert "[AADHAAR_REDACTED]" in redacted
        else:
            assert "AADHAAR" not in detected_types


class TestAccountFolioCredentialDetection:
    """Tests 10 Bank account, folio, and credential inputs."""

    @pytest.mark.parametrize(
        "query,expected_type,expected_redacted_token",
        [
            ("My account no is 1234567890123", "BANK_ACCOUNT", "[ACCOUNT_REDACTED]"),
            ("Transfer to a/c: 987654321012", "BANK_ACCOUNT", "[ACCOUNT_REDACTED]"),
            ("Bank IFSC is HDFC0001234", "BANK_ACCOUNT", "[ACCOUNT_REDACTED]"),
            ("Branch IFSC: sbin0005678", "BANK_ACCOUNT", "[ACCOUNT_REDACTED]"),
            ("My folio number is 12345/67", "FOLIO", "[FOLIO_REDACTED]"),
            ("Registered folio: 987654321", "FOLIO", "[FOLIO_REDACTED]"),
            ("Folio no 45678910", "FOLIO", "[FOLIO_REDACTED]"),
            ("My OTP is 4829 for verification", "CREDENTIAL", "[CREDENTIAL_REDACTED]"),
            ("Account password: 123456", "CREDENTIAL", "[CREDENTIAL_REDACTED]"),
            ("482910 is my otp", "CREDENTIAL", "[CREDENTIAL_REDACTED]"),
        ],
    )
    def test_credentials_and_accounts(
        self, query: str, expected_type: str, expected_redacted_token: str
    ):
        has_pii, detected_types, redacted = scan_pii(query)
        assert has_pii is True
        assert expected_type in detected_types
        assert expected_redacted_token in redacted


def test_benign_financial_query_not_blocked():
    """Confirms factual questions about NAV, TER, and amounts are never blocked as PII."""
    benign_queries = [
        "What is the exit load for HDFC Mid-Cap Opportunities Fund?",
        "Is there a lock-in period for HDFC Small Cap Fund?",
        "The NAV is 213.423 rupees as of yesterday.",
        "Can I invest 100 rupees in SIP?",
        "AUM of the fund is 101856.06 Cr.",
    ]
    for q in benign_queries:
        has_pii, detected, _ = scan_pii(q)
        assert has_pii is False, f"Benign query falsely blocked: {q}"
        assert len(detected) == 0
