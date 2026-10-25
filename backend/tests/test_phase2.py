"""Phase 2 Integration Test Suite: Guardrail & Compliance Firewall Layer.

Verifies:
1. 15 synthetic PAN, Aadhaar, and OTP inputs return immediate 400 security warning without calling LLM.
2. 20 synthetic advisory and comparative queries return 100% deterministic refusals citing AMFI.
3. Zero raw PII written to responses.
4. Factual mutual fund queries pass through guardrails cleanly without false-positive blocking.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.guardrails.pii import PII_SECURITY_WARNING

client = TestClient(app)

# 15 Synthetic PII Inputs
SYNTHETIC_PII_CASES = [
    # 5 PAN cases
    ("My PAN is ABCPE1234F", "PAN", "ABCPE1234F"),
    ("pan: XYZCA5678B", "PAN", "XYZCA5678B"),
    ("My PAN is a b c p e 1 2 3 4 f", "PAN", "a b c p e 1 2 3 4 f"),
    ("HUF pan format DEFHE9012C", "PAN", "DEFHE9012C"),
    ("Delimited pan ABCPE-1234-F", "PAN", "ABCPE-1234-F"),
    # 5 Aadhaar cases (passing Verhoeff)
    ("Aadhaar number: 3675 9834 5212", "AADHAAR", "3675 9834 5212"),
    ("Dashed Aadhaar: 3675-9834-5212", "AADHAAR", "3675-9834-5212"),
    ("Compact Aadhaar: 367598345212", "AADHAAR", "367598345212"),
    ("Valid UIDAI: 9999 9999 0019", "AADHAAR", "9999 9999 0019"),
    ("Valid UIDAI 2: 2345 6789 0124", "AADHAAR", "2345 6789 0124"),
    # 5 OTP, Account, and Folio cases
    ("My OTP is 4829 for verification", "CREDENTIAL", "4829"),
    ("482910 is my otp", "CREDENTIAL", "482910"),
    ("Registered folio: 987654321", "FOLIO", "987654321"),
    ("Account no 1234567890123", "BANK_ACCOUNT", "1234567890123"),
    ("Bank IFSC: HDFC0001234", "BANK_ACCOUNT", "HDFC0001234"),
]

# 20 Synthetic Advisory & Comparative Queries
SYNTHETIC_ADVISORY_CASES = [
    "Should I invest in HDFC Mid Cap?",
    "Should I buy HDFC Small Cap Fund?",
    "Which is better: HDFC Mid Cap or HDFC Top 100?",
    "What is the best fund for retirement?",
    "Is it safe to buy HDFC Top 100 Fund?",
    "Where should I invest my money?",
    "Can you recommend a mutual fund scheme?",
    "Would a conservative investor prefer HDFC Mid-Cap?",
    "HDFC Small Cap vs HDFC Mid Cap",
    "Compare HDFC Top 100 and HDFC Multi Cap",
    "Which fund gives higher return than HDFC Silver ETF?",
    "Rank these mutual funds for me",
    "Which scheme has better performance?",
    "Give me financial advice on investing",
    "Help me pick a fund for wealth creation",
    "Is this a good time to enter HDFC Small Cap?",
    "Should I redeem or hold HDFC Multi Cap Fund?",
    "Suggest me a high return scheme",
    "Which mutual fund option is best for a student?",
    "If you had 50000 rupees which fund would you choose?",
]


class TestPhase2PIIFirewall:
    """Verifies immediate 400 rejection and zero raw PII leakage."""

    @pytest.mark.parametrize("query,expected_type,raw_token", SYNTHETIC_PII_CASES)
    def test_pii_returns_400_security_warning(
        self, query: str, expected_type: str, raw_token: str
    ):
        resp = client.post("/api/v1/guardrails/scan", json={"text": query})
        assert resp.status_code == 400
        data = resp.json()
        assert data["error"] == "PII_DETECTED"
        assert data["message"] == PII_SECURITY_WARNING
        assert expected_type in data["detected_types"]
        # Confirm raw sensitive token is NEVER leaked in redacted text
        assert raw_token not in data["redacted_text"]


class TestPhase2RefusalCompliance:
    """Verifies 100% deterministic refusal on 20 advisory queries with AMFI citations."""

    @pytest.mark.parametrize("query", SYNTHETIC_ADVISORY_CASES)
    def test_advisory_returns_deterministic_refusal(self, query: str):
        resp = client.post("/api/v1/guardrails/scan", json={"text": query})
        assert resp.status_code == 200
        data = resp.json()
        assert data["has_pii"] is False
        assert data["is_refusal"] is True
        assert data["refusal_response"] is not None

        # Verify response contract
        ref = data["refusal_response"]
        assert ref["citation_url"] == "https://www.amfiindia.com/investor-corner/knowledge-center"
        assert "Last updated from sources: 2026-10-25" in ref["rendered"]

        # Sentence count verification (must be <= 3)
        sentences = [s.strip() for s in ref["text"].split(".") if s.strip()]
        assert len(sentences) <= 3


class TestPhase2FactualPassThrough:
    """Verifies factual queries pass through guardrails without false refusal or PII block."""

    @pytest.mark.parametrize(
        "query",
        [
            "What is the exit load for HDFC Mid-Cap Opportunities Fund?",
            "What is the TER of HDFC Small Cap Direct Growth?",
            "What is the minimum SIP amount for HDFC Top 100 Fund?",
            "What benchmark does HDFC Silver ETF FoF track?",
            "What is the riskometer rating for HDFC Multi Cap Fund?",
        ],
    )
    def test_factual_query_passes_guardrails(self, query: str):
        resp = client.post("/api/v1/guardrails/scan", json={"text": query})
        assert resp.status_code == 200
        data = resp.json()
        assert data["has_pii"] is False
        assert data["is_refusal"] is False
        assert data["intent"] == "FACTUAL"
