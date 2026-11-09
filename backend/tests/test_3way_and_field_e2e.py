"""End-to-end HTTP tests for the 3-way intent head and embedding field matcher."""

from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.rag.entities import match_field_by_embedding


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


class TestThreeWayIntentHeadE2E:
    """Verifies end-to-end HTTP routing for DECISION_REQUEST, INFORMATION_REQUEST, and UNSUPPORTED_INFORMATION."""

    def test_decision_request_routed_to_refusal_zero_llm_calls(self, client):
        """Decision queries must route to refusal without calling the LLM."""
        with patch("groq.Client") as mock_groq:
            resp = client.post(
                "/api/v1/rag/ask",
                json={"query": "Which fund should I buy for highest return?"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["resolution_type"] == "refusal"
            assert "cannot offer investment advice" in data["text"] or "cannot recommend" in data["text"] or "objective" in data["text"]
            assert mock_groq.call_count == 0

    def test_information_request_routed_to_fact_or_synthesis(self, client):
        """In-scope factual queries must resolve via fact_store or llm_synthesis."""
        resp = client.post(
            "/api/v1/rag/ask",
            json={"query": "What is the expense ratio of HDFC Small Cap Fund?"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["resolution_type"] in ("fact_store", "llm_synthesis")
        assert "0.68%" in data["text"] or "TER" in data["text"] or "expense ratio" in data["text"].lower()

    def test_unsupported_information_request_routed_to_not_found(self, client):
        """Unsupported factual queries (e.g. volatility, Sharpe ratio, historical returns) must route to not_found template."""
        resp = client.post(
            "/api/v1/rag/ask",
            json={"query": "What is the standard deviation and Sharpe ratio of HDFC Top 100?"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["resolution_type"] in ("not_found", "out_of_scope")
        assert "I don't have that information" in data["text"]
        assert "TER, exit load, minimum SIP, NAV, AUM" in data["text"]


class TestEmbeddingFieldMatching:
    """Verifies embedding field matcher behavior above and below the 0.52 cosine threshold."""

    def test_field_matching_above_threshold(self):
        """'minimum lumpsum' should match 'min_lumpsum' with similarity >= 0.52."""
        match = match_field_by_embedding("minimum lumpsum", threshold=0.52)
        assert match is not None
        field_name, score = match
        assert field_name == "min_lumpsum"
        assert score >= 0.52, f"Score {score:.3f} was below 0.52"

    def test_field_matching_above_threshold_e2e_http(self, client):
        """End-to-end HTTP request with embedded field synonym resolves to fact_store."""
        resp = client.post(
            "/api/v1/rag/ask",
            json={"query": "What is the minimum lumpsum investment for HDFC Small Cap Fund?"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["resolution_type"] == "fact_store"
        assert data["field"] == "min_lumpsum"
        assert "₹100" in data["text"]

    def test_field_matching_below_threshold(self):
        """Non-supported metrics (e.g., standard deviation) should fail threshold (< 0.52) and return None."""
        match = match_field_by_embedding("standard deviation and beta coefficient", threshold=0.52)
        assert match is None

    def test_field_matching_below_threshold_e2e_http(self, client):
        """End-to-end HTTP query with non-supported field routes safely to not-found."""
        resp = client.post(
            "/api/v1/rag/ask",
            json={"query": "What is the beta volatility coefficient of HDFC Small Cap Fund?"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["resolution_type"] in ("not_found", "out_of_scope")
        assert "I don't have that information" in data["text"]
