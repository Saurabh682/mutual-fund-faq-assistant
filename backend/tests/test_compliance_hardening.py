"""Compliance and Hardening Unit Tests.

Validates:
1. Clause splitting safety: non-splitting of coordinating noun phrases ('TER and exit load',
   'Direct and Regular') vs accurate splitting of mixed factual-advisory queries.
2. Pure similarity retrieval: out-of-corpus rejection without named entity blocklists,
   and zero false not-founds on unusual in-corpus questions (portfolio turnover, SIP dates).
3. Deadline fallback with max_retries=0: 3s delay injection triggering fallback and deadline_fallback_used=True.
4. Capital gains statement procedure: official Groww navigation steps, single URL, valid date.
"""

from __future__ import annotations

import time
from unittest.mock import patch
import pytest

from app.guardrails.intent import (
    classify_clause_level_intent,
    classify_intent,
    split_clauses,
)
from app.rag.entities import resolve_entities
from app.rag.facts import lookup_fact
from app.rag.procedures import lookup_procedure
from app.rag.retriever import HybridRetriever
from app.rag.synthesizer import ConstrainedSynthesizer


# =====================================================================
# 1. Clause Splitting Safety Tests
# =====================================================================
def test_clause_splitting_preserves_coordinating_conjunctions():
    """Ensures coordinating noun phrases are NOT split on 'and'."""
    queries_should_not_split = [
        "What is the TER and exit load of Small Cap",
        "What is the expense ratio and minimum SIP for HDFC Mid Cap?",
        "Explain the difference between Direct and Regular plans",
        "HDFC Silver ETF FoF and gold comparison",
        "What is the NAV and AUM of HDFC Top 100?",
    ]
    for q in queries_should_not_split:
        clauses = split_clauses(q)
        assert len(clauses) == 1, f"Query '{q}' was unexpectedly split into: {clauses}"


def test_clause_splitting_splits_mixed_intent():
    """Ensures mixed factual-plus-advisory queries split cleanly and trigger compound refusals."""
    compound_queries = [
        ("What is the TER of HDFC Mid Cap and should I invest in it?", 2),
        ("What is the exit load for HDFC Small Cap Fund, but is it a good time to buy?", 2),
        ("What is HDFC Top 100 NAV? Also will it outperform Nifty 50?", 2),
        ("What is the minimum SIP for HDFC Multi Cap Fund and how much will 5000 grow to in 5 years?", 2),
    ]
    for q, expected_len in compound_queries:
        clauses = split_clauses(q)
        assert len(clauses) >= expected_len, f"Query '{q}' failed to split: {clauses}"
        compound_resp = classify_clause_level_intent(q)
        assert compound_resp is not None, f"Query '{q}' failed to produce a compound refusal"
        assert compound_resp["citation_url"].startswith("http")
        assert len(compound_resp["text"].split("\n\n")[0].split(". ")) <= 3


def test_multi_field_query_resolves_intact():
    """Ensures queries with multiple fields resolve to structured multi-fact responses."""
    q = "What is the TER and exit load of Small Cap"
    fact_resp = lookup_fact(q)
    assert fact_resp is not None
    assert "field" in fact_resp
    assert "0.8" in fact_resp["text"] or "0.8%" in fact_resp["text"] or "1%" in fact_resp["text"]


# =====================================================================
# 2. Pure Similarity Retrieval & Zero False Not-Founds
# =====================================================================
def test_retriever_zero_hardcoded_blocklists():
    """Asserts UNINDEXED_ENTITIES blocklist is removed from retriever module."""
    from app.rag import retriever
    assert not hasattr(retriever, "UNINDEXED_ENTITIES")
    ret = HybridRetriever()
    assert not hasattr(ret, "UNINDEXED_ENTITIES")


def test_in_corpus_unusual_questions_pass_retrieval():
    """Asserts unusual in-corpus questions do NOT get falsely marked as out-of-corpus."""
    ret = HybridRetriever()
    in_corpus_queries = [
        ("What is the portfolio turnover of HDFC Top 100?", "hdfc_largecap_dg"),
        ("What are the SIP dates for HDFC Mid Cap?", "hdfc_midcap_dg"),
        ("What is the NAV of HDFC Small Cap?", "hdfc_smallcap_dg"),
        ("Who manages HDFC Multi Cap?", "hdfc_multicap_dg"),
    ]
    for q, expected_scheme in in_corpus_queries:
        ent = resolve_entities(q)
        assert ent.scheme_id == expected_scheme
        res = ret.search(q, scheme_id=ent.scheme_id)
        assert not res.is_out_of_corpus, f"Query '{q}' was wrongly flagged out-of-corpus"
        assert len(res.chunks) > 0, f"Query '{q}' found 0 chunks"


def test_unrelated_query_out_of_corpus():
    """Asserts truly unrelated queries with low similarity are marked out-of-corpus."""
    ret = HybridRetriever()
    res = ret.search("What is the recipe for chicken biryani?", scheme_id=None)
    assert res.is_out_of_corpus
    assert len(res.chunks) == 0


# =====================================================================
# 3. Deadline Fallback with max_retries=0 and Injected 3s Delay
# =====================================================================
def test_deadline_fallback_with_injected_delay():
    """Injects a 3.0s delay in LLM call to verify strict deadline fallback triggers cleanly."""
    syn = ConstrainedSynthesizer()
    assert syn.client.max_retries == 0

    def slow_llm(*args, **kwargs):
        time.sleep(3.0)
        return "Draft that took 3 seconds"

    context = ["HDFC Top 100 Fund TER is 0.62% as of 2026-11-05."]
    with patch.object(syn, "_call_llm", side_effect=slow_llm):
        t0 = time.perf_counter()
        res = syn.synthesize(
            query="What is HDFC Top 100 TER?",
            context_chunks=context,
            primary_url="https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth",
            doc_date="2026-11-05",
        )
        elapsed = time.perf_counter() - t0

    assert res.deadline_fallback_used is True
    assert res.is_valid is True
    # Verify fallback text is either extractive top-chunk or the clean timeout message
    assert (
        "Please try again shortly; real-time verification timed out." in res.text
        or "0.62%" in res.text
        or "HDFC Top 100" in res.text
    )


# =====================================================================
# 4. Capital Gains Statement Procedure Accuracy
# =====================================================================
def test_capital_gains_statement_procedure():
    """Verifies official navigation steps for downloading Capital Gains statement."""
    q = "How do I get my capital gains statement?"
    proc = lookup_procedure(q)
    assert proc is not None
    assert "capital gains" in proc["text"].lower()
    assert "groww" in proc["rendered"].lower() or "cams" in proc["rendered"].lower()
    assert proc["citation_url"].startswith("http")
    assert proc["last_updated"] == "2026-11-05"
    assert proc["sentence_count"] <= 3
