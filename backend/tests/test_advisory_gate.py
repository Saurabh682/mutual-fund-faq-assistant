"""Unit tests verifying that the Advisory Gate runs before any LLM invocation.

Ensures that advisory, comparative, and projection queries (including un-regexed clauses
caught by the embedding-prototype classifier) never invoke the Groq LLM client,
even if the LLM mock is configured to raise 429 or NOT_FOUND.
"""

from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.guardrails.intent import classify_intent, classify_clause_level_intent
from app.guardrails.intent_prototype import classify_clause_prototype

client = TestClient(app)


def test_prototype_classifier_distinguishes_advisory_and_factual():
    """Verifies that the embedding prototype classifier separates advisory from factual."""
    cat_adv, adv_s, fac_s = classify_clause_prototype("will it outperform the benchmark")
    assert cat_adv == "ADVISORY"
    assert adv_s > fac_s

    cat_fac, adv_f, fac_f = classify_clause_prototype("What is the TER of HDFC Top 100?")
    assert cat_fac == "FACTUAL"
    assert fac_f > adv_f


def test_llm_never_called_for_advisory_query():
    """Proves the Groq LLM client is never invoked for advisory queries."""
    with patch("app.rag.synthesizer.ConstrainedSynthesizer._call_llm") as mock_llm:
        mock_llm.side_effect = RuntimeError("FATAL: LLM was invoked for an advisory query!")

        # 1. Direct advisory query
        resp = client.post("/api/v1/rag/ask", json={"query": "Should I invest in HDFC Small Cap Fund right now?"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["resolution_type"] == "refusal"
        assert "investment advice" in data["rendered"]
        assert mock_llm.call_count == 0

        # 2. Comparative outperformance query
        resp2 = client.post("/api/v1/rag/ask", json={"query": "Will HDFC Silver ETF FoF outperform HDFC Top 100 over the next 5 years?"})
        assert resp2.status_code == 200
        data2 = resp2.json()
        assert data2["resolution_type"] == "refusal"
        assert mock_llm.call_count == 0


def test_llm_never_called_even_if_mock_raises_429():
    """Proves that even when LLM client is set to raise Groq 429 rate limit, advisory queries never touch it."""
    with patch("app.rag.synthesizer.ConstrainedSynthesizer._call_llm") as mock_llm:
        mock_llm.side_effect = Exception("429 rate limit exceeded")

        resp = client.post("/api/v1/rag/ask", json={"query": "Can you guarantee that HDFC Mid-Cap Opportunities will deliver 15% annual returns?"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["resolution_type"] == "refusal"
        assert mock_llm.call_count == 0


def test_compound_query_returns_compound_without_llm():
    """Proves mixed factual + advisory queries return deterministic 2-sentence compound answer without calling LLM."""
    with patch("app.rag.synthesizer.ConstrainedSynthesizer._call_llm") as mock_llm:
        mock_llm.side_effect = RuntimeError("FATAL: LLM was invoked for compound query!")

        query = "What is the TER of HDFC Mid Cap and should I invest in it?"
        resp = client.post("/api/v1/rag/ask", json={"query": query})
        assert resp.status_code == 200
        data = resp.json()
        assert data["resolution_type"] == "compound"
        assert mock_llm.call_count == 0
        assert "investment advice" in data["rendered"]
        assert "%" in data["rendered"]
