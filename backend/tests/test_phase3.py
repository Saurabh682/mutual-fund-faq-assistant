"""Phase 3 Test Suite: Hybrid Retrieval, Entity Resolution & Structured Fact Store.

Verifies:
1. EVAL-P3.1: Cross-Scheme Contamination Elimination (0% contamination with scheme filter).
2. EVAL-P3.2: Structured Fact Path Latency (< 50ms) and 100% numerical accuracy.
3. EVAL-P3.3: Out-of-Corpus Fallback (similarity < tau triggers 'not found' fallback).
4. Ambiguity Disambiguation (EC-ENT-01) and Pronoun Resolution (EC-ENT-02).
5. Procedural FAQ Retrieval (Groww FAQs retrieved for procedural queries).
"""

import time
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.rag.entities import (
    SCHEME_REGISTRY,
    get_disambiguation_response,
    resolve_entities,
)
from app.rag.facts import get_fact_from_db, lookup_fact
from app.rag.retriever import HybridRetriever, get_not_found_response

client = TestClient(app)
retriever = HybridRetriever()


class TestEntityResolution:
    """Verifies entity extraction, alias matching, pronoun resolution, and ambiguity handling."""

    @pytest.mark.parametrize(
        "query,expected_scheme,expected_field",
        [
            ("What is the exit load for HDFC Mid-Cap Opportunities Fund?", "hdfc_midcap_dg", "exit_load"),
            ("What is the TER of HDFC Small Cap Direct Growth?", "hdfc_smallcap_dg", "ter_direct"),
            ("What is the minimum SIP in HDFC Top 100?", "hdfc_largecap_dg", "min_sip"),
            ("Does HDFC Silver ETF have a lock-in period?", "hdfc_silver_fof_dg", "lock_in"),
            ("What is the riskometer rating for HDFC Multi Cap?", "hdfc_multicap_dg", "riskometer"),
            ("What benchmark does HDFC Mid Cap track?", "hdfc_midcap_dg", "benchmark"),
            ("What is the current NAV of HDFC Small Cap?", "hdfc_smallcap_dg", "nav"),
            ("What is the fund size of HDFC Top 100?", "hdfc_largecap_dg", "aum"),
            ("Who is the fund manager of HDFC Small Cap?", "hdfc_smallcap_dg", "fund_manager"),
            ("Who manages HDFC Top 100?", "hdfc_largecap_dg", "fund_manager"),
        ],
    )
    def test_entity_resolution_accuracy(
        self, query: str, expected_scheme: str, expected_field: str
    ):
        res = resolve_entities(query)
        assert res.scheme_id == expected_scheme
        assert res.field == expected_field
        assert res.is_ambiguous is False

    def test_pronoun_resolution_ec_ent_02(self):
        """EC-ENT-02: Pronouns inherit scheme_id from active session."""
        res = resolve_entities("What is its minimum SIP amount?", session_scheme_id="hdfc_largecap_dg")
        assert res.scheme_id == "hdfc_largecap_dg"
        assert res.field == "min_sip"
        assert res.is_ambiguous is False

    def test_ambiguous_query_ec_ent_01(self):
        """EC-ENT-01: Factual question asked without any scheme triggers ambiguity clarification."""
        res = resolve_entities("What is the exit load?")
        assert res.scheme_id is None
        assert res.field == "exit_load"
        assert res.is_ambiguous is True

        clarification = get_disambiguation_response()
        assert "Please specify which HDFC scheme" in clarification["text"]
        assert "Source: https://www.amfiindia.com/investor-corner/knowledge-center" in clarification["rendered"]


class TestEVAL_P3_2_StructuredFactPath:
    """EVAL-P3.2: Structured Fact Path Latency (< 50ms) and Numerical Accuracy."""

    CANONICAL_TEST_CASES = [
        ("hdfc_midcap_dg", "ter_direct", "0.74%"),
        ("hdfc_midcap_dg", "min_sip", "₹100"),
        ("hdfc_smallcap_dg", "ter_direct", "0.8%"),
        ("hdfc_smallcap_dg", "min_sip", "₹100"),
        ("hdfc_largecap_dg", "ter_direct", "1.02%"),
        ("hdfc_silver_fof_dg", "ter_direct", "0.21%"),
        ("hdfc_multicap_dg", "ter_direct", "0.96%"),
        ("hdfc_smallcap_dg", "fund_manager", "Chirag Setalvad"),
        ("hdfc_largecap_dg", "fund_manager", "Prashant Jain"),
    ]

    @pytest.mark.parametrize("scheme_id,field,expected_val", CANONICAL_TEST_CASES)
    def test_fact_db_accuracy(self, scheme_id: str, field: str, expected_val: str):
        fact = get_fact_from_db(scheme_id, field)
        assert fact is not None, f"Missing fact in DB: {scheme_id} -> {field}"
        assert fact["value"] == expected_val

    def test_fact_lookup_latency_under_50ms(self):
        query = "What is the Total Expense Ratio of HDFC Mid Cap Direct Growth?"
        t0 = time.perf_counter()
        res = lookup_fact(query)
        elapsed_ms = (time.perf_counter() - t0) * 1000

        assert res is not None
        assert elapsed_ms < 50.0, f"Fact lookup exceeded 50ms: {elapsed_ms:.2f}ms"
        assert "0.74%" in res["text"]
        assert res["last_updated"] == "2026-10-23"
        assert "Source: https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth" in res["rendered"]


class TestEVAL_P3_1_CrossSchemeContamination:
    """EVAL-P3.1: 0% Cross-Scheme Contamination."""

    SMALLCAP_QUERIES = [
        "What is the exit load for HDFC Small Cap?",
        "How to redeem HDFC Small Cap Fund?",
        "What is the benchmark of HDFC Small Cap?",
        "Who is the fund manager of HDFC Small Cap?",
        "What is the minimum SIP in HDFC Small Cap?",
        "How to invest in HDFC Small Cap Fund Direct Growth?",
        "What is the risk level of HDFC Small Cap?",
        "Does HDFC Small Cap have any lock-in period?",
        "What is the AUM of HDFC Small Cap Fund?",
        "What is the NAV of HDFC Small Cap?",
        "Can I invest in SIP of HDFC Small Cap?",
        "What is the PE ratio of HDFC Small Cap?",
        "Stamp duty on HDFC Small Cap investment",
        "RTA details for HDFC Small Cap",
        "Tax implications on redeeming HDFC Small Cap",
        "Expense ratio of HDFC Small Cap Fund",
        "Minimum additional investment in HDFC Small Cap",
        "Holding terms of HDFC Small Cap",
        "How do I sell my HDFC Small Cap holdings?",
        "Is lumpsum allowed in HDFC Small Cap?",
        "Category of HDFC Small Cap Fund",
        "Inception returns of HDFC Small Cap",
        "Fund house for HDFC Small Cap",
        "ISIN code for HDFC Small Cap Direct Growth",
        "Direct Plan growth option of HDFC Small Cap",
    ]

    @pytest.mark.parametrize("query", SMALLCAP_QUERIES)
    def test_zero_cross_scheme_contamination(self, query: str):
        # Resolve scheme
        entity_res = resolve_entities(query)
        assert entity_res.scheme_id == "hdfc_smallcap_dg"

        # Search with scheme filter
        res = retriever.search(query, scheme_id=entity_res.scheme_id, top_k=4)
        assert not res.is_out_of_corpus
        assert len(res.chunks) > 0

        # Strict Invariant: 100% of chunks must belong strictly to hdfc_smallcap_dg
        for chunk in res.chunks:
            assert (
                chunk.metadata["scheme_id"] == "hdfc_smallcap_dg"
            ), f"Cross-scheme contamination found! Expected hdfc_smallcap_dg got {chunk.metadata['scheme_id']}"


class TestEVAL_P3_3_OutOfCorpusFallback:
    """EVAL-P3.3: Out-of-Corpus Queries Trigger Safe Fallback."""

    OUT_OF_CORPUS_QUERIES = [
        "What is the expense ratio of SBI Bluechip Fund?",
        "What is the NAV of ICICI Prudential Discovery Fund?",
        "What is the minimum investment in Axis Bluechip Fund?",
        "Who manages the Nippon India Small Cap Fund?",
        "What is the weather forecast in Mumbai today?",
    ]

    @pytest.mark.parametrize("query", OUT_OF_CORPUS_QUERIES)
    def test_out_of_corpus_triggers_fallback(self, query: str):
        resp = client.post("/api/v1/rag/retrieve", json={"query": query})
        assert resp.status_code == 200
        data = resp.json()
        assert data["resolution_type"] == "not_found"
        assert "I could not find official information regarding this topic" in data["text"]
        assert data["citation_url"] == "https://www.amfiindia.com/investor-corner/knowledge-center"
        assert "Last updated from sources:" in data["rendered"]


class TestProceduralFAQRetrieval:
    """Verifies that procedural inquiries retrieve the extracted official Groww FAQs."""

    def test_redeem_procedural_faq_retrieved(self):
        res = retriever.search("How to redeem HDFC Mid Cap?", scheme_id="hdfc_midcap_dg")
        assert len(res.chunks) > 0
        top_chunk = res.chunks[0]
        text_lower = " ".join(top_chunk.text.lower().split())
        assert "redeem" in text_lower
        assert "app or web" in text_lower
        assert top_chunk.metadata["scheme_id"] == "hdfc_midcap_dg"

    def test_invest_procedural_faq_retrieved(self):
        res = retriever.search("How to invest in HDFC Top 100?", scheme_id="hdfc_largecap_dg")
        assert len(res.chunks) > 0
        top_chunk = res.chunks[0]
        text_lower = " ".join(top_chunk.text.lower().split())
        assert "invest" in text_lower
        assert "kyc" in text_lower
        assert top_chunk.metadata["scheme_id"] == "hdfc_largecap_dg"


class TestVectorDBConfiguration:
    """Verifies vector database runtime configuration and fallback behavior."""

    def test_default_chroma_initialization(self):
        r = HybridRetriever()
        assert r.vector_db_type == "chroma"
        assert r.collection is not None
        assert r.collection.count() > 0

    def test_pinecone_unconfigured_fallback_to_chroma(self):
        r = HybridRetriever(vector_db_type="pinecone", pinecone_api_key="")
        assert r.vector_db_type == "chroma"
        assert r.collection is not None

    def test_top_k_chunk_limit_enforced(self):
        res = retriever.search("What is the exit load?", scheme_id="hdfc_smallcap_dg", top_k=2)
        assert len(res.chunks) <= 2

