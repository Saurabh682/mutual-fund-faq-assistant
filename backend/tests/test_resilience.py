"""Unit tests verifying API resilience, rate limits, timeouts, and Groq 429 retries.

Covers Task 5 requirements:
- Groq 429 triggers one jittered retry before deadline.
- Groq timeout returns verified safe fallback.
- Per-IP rate limiting (20 requests/minute) returns 429.
- Maximum query length (1,000 characters) returns 400.
"""

import time
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from app.main import app, _IP_REQUEST_TIMESTAMPS
from app.rag.synthesizer import ConstrainedSynthesizer, SynthesisResult

client = TestClient(app)


def test_groq_429_triggers_jitter_retry():
    """Proves that a 429 error triggers exactly one retry with jitter if time remains."""
    synth = ConstrainedSynthesizer(api_key="mock_key", model="mock_model")
    synth.client = MagicMock()

    call_count = 0

    def mock_create(**kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise Exception("Error code: 429 - Rate limit reached")
        mock_resp = MagicMock()
        mock_resp.choices = [MagicMock(message=MagicMock(content="HDFC Top 100 TER is 0.80%."))]
        return mock_resp

    synth.client.chat.completions.create = mock_create

    # Call with ample time remaining (deadline_t in future)
    result = synth._call_llm("sys", "user", deadline_t=time.perf_counter() + 1.0)
    assert result == "HDFC Top 100 TER is 0.80%."
    assert call_count == 2, f"Expected exactly 2 attempts (1 initial + 1 retry), got {call_count}"


def test_groq_timeout_returns_fallback():
    """Proves that a timeout or deadline expiry returns safe fallback without crash."""
    synth = ConstrainedSynthesizer(api_key="mock_key", model="mock_model")
    synth.client = MagicMock()

    def mock_timeout(**kwargs):
        raise TimeoutError("Deadline exceeded prior to Groq call")

    synth.client.chat.completions.create = mock_timeout

    res = synth.synthesize(
        query="What is the TER?",
        context_chunks=["The total expense ratio of the fund is 0.80% per annum."],
        primary_url="https://groww.in/mutual-funds/hdfc-top-100",
        doc_date="2026-11-05",
    )
    assert res.is_valid is True
    assert res.deadline_fallback_used is True
    assert "0.80%" in res.rendered or "timed out" in res.rendered


def test_rate_limit_exceeded_returns_429():
    """Proves that sending > 20 requests per minute from one IP returns HTTP 429."""
    _IP_REQUEST_TIMESTAMPS.clear()

    # First 20 requests should succeed (not return 429)
    for i in range(20):
        resp = client.get("/api/v1/facts/schemes")
        assert resp.status_code == 200, f"Request {i+1} failed with {resp.status_code}"

    # 21st request from same client should return 429
    resp_21 = client.get("/api/v1/facts/schemes")
    assert resp_21.status_code == 429
    data = resp_21.json()
    assert data["error"] == "rate limit exceeded"
    assert "retry_after" in data

    # Clear timestamps so other tests aren't blocked
    _IP_REQUEST_TIMESTAMPS.clear()


def test_input_too_long_returns_400():
    """Proves that a query exceeding 1,000 characters returns HTTP 400."""
    long_query = "What is the TER? " + ("x" * 1005)
    resp = client.post("/api/v1/rag/ask", json={"query": long_query})
    assert resp.status_code == 400
    data = resp.json()
    assert data["error"] == "query too long"
    assert data["max_chars"] == 1000
