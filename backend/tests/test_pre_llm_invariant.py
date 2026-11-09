"""Unit tests verifying the Hard Pre-LLM Invariant and Structural Comparison Rule.

Ensures that:
1. Any decision request (recommendation, timing, ranking, suitability, forecast)
   never reaches the LLM client.
2. Any query naming two or more schemes without a supported fact field is
   structurally classified as a comparison request and refused without calling the LLM.
3. If the LLM client is ever called when the decision check fires, the test fails loudly.
"""

from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient

from app.main import app, _IP_REQUEST_TIMESTAMPS
from app.rag.synthesizer import ConstrainedSynthesizer

client = TestClient(app)


def failing_mock_llm(self, system_prompt, user_prompt, *args, **kwargs):
    """Mock LLM that raises an error or fails if called."""
    pytest.fail(
        f"HARD PRE-LLM INVARIANT VIOLATED: LLM was invoked with user_prompt: {user_prompt[:150]}"
    )


@pytest.mark.parametrize(
    "query",
    [
        "Which mutual fund scheme is the best pick for retirement?",
        "Should I allocate my savings into equity funds today?",
        "Will the Small Cap fund beat inflation over the next decade?",
        "Rank these funds from most promising to least promising.",
        "Can you choose the safest scheme for elderly parents?",
        "Is now the right moment to redeem my mutual fund units?",
    ],
)
def test_decision_requests_never_call_llm(query: str):
    """Decision requests are blocked by intent guardrails and never call the LLM."""
    _IP_REQUEST_TIMESTAMPS.clear()
    with patch.object(ConstrainedSynthesizer, "_call_llm", failing_mock_llm):
        resp = client.post("/api/v1/rag/ask", json={"query": query})
        assert resp.status_code == 200
        data = resp.json()
        assert data["resolution_type"] == "refusal"
        assert "cannot" in data["text"].lower() or "consult" in data["text"].lower()


@pytest.mark.parametrize(
    "query",
    [
        "Is Small Cap or Mid-Cap the smarter pick today?",
        "Which is better between HDFC Top 100 and HDFC Small Cap?",
        "Compare HDFC Multi Cap with HDFC Mid-Cap Opportunities Fund.",
        "Choose between HDFC Large Cap and HDFC Silver FoF for my portfolio.",
    ],
)
def test_multi_scheme_comparison_without_field_never_calls_llm(query: str):
    """Queries naming two or more schemes without a supported fact field are refused without calling LLM."""
    _IP_REQUEST_TIMESTAMPS.clear()
    with patch.object(ConstrainedSynthesizer, "_call_llm", failing_mock_llm):
        resp = client.post("/api/v1/rag/ask", json={"query": query})
        assert resp.status_code == 200
        data = resp.json()
        assert data["resolution_type"] == "refusal"
        assert "compare" in data["text"].lower() or "cannot" in data["text"].lower()


def test_hard_pre_llm_invariant_synthesizer_direct():
    """Direct invariant check inside ConstrainedSynthesizer.synthesize blocks decision queries."""
    synth = ConstrainedSynthesizer()
    with patch.object(ConstrainedSynthesizer, "_call_llm", failing_mock_llm):
        result = synth.synthesize(
            query="Which fund should I buy for 2026?",
            context_chunks=["Some mock facts"],
            primary_url="https://groww.in",
            doc_date="2026-11-05",
        )
        assert result.is_valid is True
        assert "cannot offer investment advice" in result.text or "objective, factual" in result.text
        assert "HARD_PRE_LLM_INVARIANT_DECISION_BLOCKED" in result.violation_reasons
