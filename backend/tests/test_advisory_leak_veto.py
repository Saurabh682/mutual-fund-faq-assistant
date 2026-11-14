"""Regression tests: advice requests that carried a procedural or factual keyword leaked.

Root cause (2026-11-14 end-to-end probe, 47/323 leaks): classify_intent returned at step 7
(procedural keyword, e.g. "cut-off time") or step 8 (factual keyword, e.g. "scheme") before the
embedding head ever ran, so the advice part was dropped and only the fact was answered.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app, _IP_REQUEST_TIMESTAMPS

client = TestClient(app)


def resolution(query: str) -> str:
    _IP_REQUEST_TIMESTAMPS.clear()
    resp = client.post("/api/v1/rag/ask", json={"query": query})
    assert resp.status_code == 200
    return resp.json()["resolution_type"]


LEAKED_ADVICE = [
    # factual keyword ("scheme") exited before the head
    "Which scheme would you recommend for long term wealth creation?",
    "Should an investor enter this scheme before the upcoming budget?",
    # procedure answered, advice dropped
    "Is it prudent to commit spare cash into this fund ahead of elections considering the redemption cut-off time",
    "Help me decide how to distribute fifty thousand rupees across these funds considering the redemption cut-off time",
    "Tell me if this is a suitable moment to exit my mutual fund positions considering the redemption cut-off time",
    # glossary answered, advice dropped
    "Explain expense ratio and please tell me if this fund is a worthwhile purchase today",
    # exemption gap swallowed the decision verb
    "Advise me on whether I should redeem my units before interest rates change given the exit load of HDFC Small Cap Fund",
]

STILL_ANSWERED = [
    "What is the cut-off time for same day NAV in equity funds?",
    "Can I switch mutual fund units between two different AMCs directly?",
    "What is the TER of HDFC Small Cap Direct Growth?",
    "Define Net Asset Value in mutual fund schemes.",
]


@pytest.mark.parametrize("query", LEAKED_ADVICE)
def test_advice_with_lookup_keyword_is_refused(query):
    assert resolution(query) in ("refusal", "compound")


@pytest.mark.parametrize("query", STILL_ANSWERED)
def test_plain_lookup_is_not_refused(query):
    assert resolution(query) not in ("refusal", "compound")
