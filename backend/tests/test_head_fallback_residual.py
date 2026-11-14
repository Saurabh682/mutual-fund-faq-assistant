"""Regression tests: the head fallback in classify_intent must judge supported lookups by residual.

Root cause (2026-11-14 eval): with no regex or factual-keyword hit, classify_intent scored the
whole query with the embedding head / prototype guardrail, which fail closed and refused plain
glossary, procedure and scheme-fact questions. Supported lookups are now judged on the words
left after removing the scheme/field aliases; unresolved queries keep the whole-query check.
"""

import pytest

from app.guardrails.intent import _decision_residual, classify_intent
from app.rag.entities import resolve_entities


@pytest.mark.parametrize(
    "query",
    [
        "Define Net Asset Value in mutual fund schemes.",
        "What is the cut-off timing for debt mutual fund redemptions?",
        "who manages hdfc silver etf fund of fund",
        "Is HDFC Multi Cap Fund labeled as high risk or very high risk?",
    ],
)
def test_supported_lookup_is_not_refused(query):
    assert classify_intent(query).is_refusal is False


@pytest.mark.parametrize(
    "query",
    [
        # Held-out decision prototypes the regex layer misses, alone and wrapped around a lookup.
        "Help me decide how to distribute fifty thousand rupees across these funds.",
        "Is it prudent to commit spare cash into this fund ahead of elections?",
        "Who manages HDFC Mid-Cap Opportunities Fund and is it advisable to shift capital from large caps to small caps today",
    ],
)
def test_decision_requests_still_refused(query):
    assert classify_intent(query).is_refusal is True


@pytest.mark.parametrize(
    "query",
    [
        # A factual keyword short-circuits classify_intent; the clause-level compound path
        # is the layer that must refuse the decision half.
        # Leaked on d398a61: CLAUSE_SPLIT_PATTERN did not split on "and define"/"and explain".
        "Is it prudent to commit spare cash into this fund ahead of elections and define NAV",
        "Help me decide how to distribute fifty thousand rupees across these funds and explain expense ratio",
        "Should I continue my monthly contribution if markets keep declining and state the lock-in for HDFC Top 100",
        "Explain expense ratio and tell me if this is a suitable moment to exit my mutual fund positions",
    ],
)
def test_hybrid_lookup_plus_decision_refused_end_to_end(query):
    from fastapi.testclient import TestClient
    from app.main import _IP_REQUEST_TIMESTAMPS, app

    _IP_REQUEST_TIMESTAMPS.clear()
    data = TestClient(app).post("/api/v1/rag/ask", json={"query": query}).json()
    assert data["resolution_type"] in ("refusal", "compound")


def test_residual_strips_only_the_resolved_scheme():
    query = "Who manages HDFC Mid-Cap Opportunities Fund and shift from large caps to small caps"
    residual = _decision_residual(query, resolve_entities(query))
    assert "large caps" in residual and "small caps" in residual
