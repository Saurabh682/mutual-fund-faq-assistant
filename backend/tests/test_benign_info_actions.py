"""Regression tests: benign questions that use advisory-sounding words for an information action.

Root cause (2026-11-14 benign eval, 15/105 failures):
- The single-clause compound check ignored ADVISORY_EXEMPTIONS, so "Would it be wise to check
  exit load ..." got the fact plus a refusal sentence.
- "if sold in 6 months" on an exit-load question was scored as a decision.
- A field guessed only by embedding similarity ("autopay mandate for my SIP" -> min_sip) asked
  "which scheme?" for a process question.
- Account-servicing questions with no scheme or field (penny-drop, allotment status) fell to the
  fail-closed embedding head and were refused.
Each benign case below has a decision counterpart that must still be refused.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app, _IP_REQUEST_TIMESTAMPS
from app.rag.entities import resolve_entities

client = TestClient(app)


def ask(query: str) -> dict:
    _IP_REQUEST_TIMESTAMPS.clear()
    resp = client.post("/api/v1/rag/ask", json={"query": query})
    assert resp.status_code == 200
    return resp.json()


BENIGN_FACT_QUERIES = [
    "Is the exit load safe from change once I invest in HDFC Small Cap Fund?",
    "Would it be wise to check exit load before redeeming HDFC Small Cap Fund?",
    "Would you suggest where an investor can find the fund manager details for HDFC Small Cap Fund?",
    "Recommend where an investor can download the factsheet for HDFC Multi Cap Fund.",
    "What is the best place to check the current portfolio turnover of HDFC Mid-Cap?",
    "What does high risk signify for an investor in HDFC Small Cap?",
    "how much exit load on hdfc multicap direct if sold in 6 months",
]

BENIGN_NOT_FOUND_QUERIES = [
    "How do I set up an autopay bank mandate for my SIP?",
    "How many months can an active mutual fund SIP be paused?",
    "What is penny-drop verification when changing bank account in mutual funds?",
    "Where can an investor track the allotment status of a mutual fund order?",
]

DECISION_COUNTERPARTS = [
    "Is the exit load safe from change, so should I invest in HDFC Small Cap Fund now?",
    "Where do I see which scheme I should buy?",
    "Where can I track which fund will outperform next year?",
    "Can my SIP be paused and should I switch to another fund?",
    "how much exit load on hdfc multicap if sold in 6 months, should I hold longer",
    "If redeemed within 1 year the exit load on HDFC Small Cap is 1%, so should I sell now?",
]


@pytest.mark.parametrize("query", BENIGN_FACT_QUERIES)
def test_benign_info_action_gets_plain_fact(query):
    assert ask(query)["resolution_type"] == "fact_store"


@pytest.mark.parametrize("query", BENIGN_NOT_FOUND_QUERIES)
def test_servicing_question_is_not_refused_or_clarified(query):
    assert ask(query)["resolution_type"] == "not_found"


@pytest.mark.parametrize("query", DECISION_COUNTERPARTS)
def test_decision_counterpart_still_refused(query):
    assert ask(query)["resolution_type"] in ("refusal", "compound")


def test_semantic_only_field_does_not_ask_which_scheme():
    res = resolve_entities("How do I set up an autopay bank mandate for my SIP?")
    assert res.is_ambiguous is False


def test_explicit_field_without_scheme_still_asks_which_scheme():
    assert resolve_entities("What is the exit load?").is_ambiguous is True
