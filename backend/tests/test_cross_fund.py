"""Cross-fund questions: factual lookups answer as a table; rankings stay refused."""

import pytest

from app.rag.crossfund import answer_cross_fund


def test_riskometer_for_every_scheme():
    r = answer_cross_fund("What is the riskometer of all schemes?")
    assert r["type"] == "fact_store" and r["field"] == "riskometer"
    assert r["text"].count("\n| ") >= 20  # header + separator + one row per scheme
    assert r["rendered"].endswith(r["last_updated"])


def test_risk_level_filter_keeps_only_matching_schemes():
    r = answer_cross_fund("Which funds have a Very High risk?")
    rows = [l for l in r["text"].splitlines() if l.startswith("| ") and "Scheme" not in l and "---" not in l]
    assert rows and all(l.endswith("| Very High Risk |") for l in rows)


def test_fund_house_narrows_the_table():
    r = answer_cross_fund("Show the exit load of all HDFC schemes")
    names = [l.split("|")[1] for l in r["text"].splitlines() if l.startswith("| ") and "Scheme" not in l and "---" not in l]
    assert names and all("HDFC" in n for n in names)


@pytest.mark.parametrize("q", [
    "Which funds have the lowest expense ratio?",
    "Which scheme is the cheapest by TER across all funds?",
])
def test_rankings_are_refused_with_a_lookup_suggestion(q):
    r = answer_cross_fund(q)
    assert r["type"] == "refusal"
    assert any("of all schemes" in f for f in r["followups"])


@pytest.mark.parametrize("q", [
    "What is the exit load for HDFC Small Cap Fund?",
    "What are all the charges for HDFC Small Cap Fund?",
    "Which fund is best?",
    "What is TER?",
])
def test_other_questions_fall_through(q):
    assert answer_cross_fund(q) is None


@pytest.mark.parametrize("q,level", [
    ("among all which is the least risky", "Low Risk"),
    ("Which fund has the lowest risk?", "Low Risk"),
    ("which scheme has the highest risk among all", "Very High Risk"),
])
def test_risk_extremes_answer_as_the_riskometer_level_listed(q, level):
    r = answer_cross_fund(q)
    assert r["type"] == "fact_store" and f"is {level}" in r["text"]
    rows = [l for l in r["text"].splitlines() if l.startswith("| ") and "Scheme" not in l and "---" not in l]
    assert rows and all(l.endswith(f"| {level} |") for l in rows)
    assert "safest" not in r["text"].lower() and "best" not in r["text"].lower()
