"""Regression tests: single-clause compound refusal must not fire on plain fact lookups.

Root cause (2026-11-14 eval): the single-clause branch of classify_clause_level_intent
trusted the embedding intent head alone. Short keyword-style fact queries score low
on every prototype class and fall inside the head's fail-closed margin, so they were
labelled DECISION_REQUEST and answered with a fact + advisory-refusal compound.
"""

import pytest

from app.guardrails.intent import classify_clause_level_intent

PLAIN_FACT_QUERIES = [
    "TER for hdfc small cap direct growth",
    "hdfc small-cap opportunities exit load period",
    "hdfc top 100 direct growth TER percentage",
    "hdfc multicap direct growth minimum sip limit",
    "hdfc mid cap opportunities fund nav direct growth today",
    "who is managing hdfc multicap fund direct growth",
    "What is the exit load for HDFC Mid-Cap Opportunities Fund?",
    "What is the TER of HDFC Small Cap Direct Growth?",
]

# Held-out decision prototypes wrapped around a supported fact. These must stay compound:
# loosening the single-clause gate must not turn them into bare fact answers.
HYBRID_DECISION_QUERIES = [
    "Tell me if this is a suitable moment to exit my mutual fund positions given the exit load of HDFC Small Cap Fund",
    "Considering the expense ratio of HDFC Mid-Cap Opportunities Fund, is it prudent to commit spare cash into this fund ahead of elections",
    "Which option carries the smallest chance of losing capital during a downturn given the exit load of HDFC Small Cap Fund",
    "Considering the expense ratio of HDFC Mid-Cap Opportunities Fund, should I continue my monthly contribution if markets keep declining",
]


@pytest.mark.parametrize("query", PLAIN_FACT_QUERIES)
def test_single_clause_fact_query_is_not_compound(query):
    assert classify_clause_level_intent(query) is None


@pytest.mark.parametrize(
    "query",
    [
        "Should I buy HDFC Small Cap given its exit load",
        "Is the HDFC Mid-Cap expense ratio low enough that I should invest now",
        *HYBRID_DECISION_QUERIES,
    ],
)
def test_single_clause_fact_plus_decision_still_compound(query):
    resp = classify_clause_level_intent(query)
    assert resp is not None
    assert "cannot" in resp["text"].lower() or "advice" in resp["text"].lower()
