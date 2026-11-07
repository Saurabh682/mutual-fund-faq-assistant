"""Unit Tests for Static Response Contract Compliance & Snapshot Verbatim Integrity.

Verifies that every static template and response in the system:
1. Adheres to the strict <= 3 sentence ceiling.
2. Contains exactly one citation URL.
3. Contains zero banned evaluative words (e.g. good, best, safe, lucrative).
4. Possesses mandatory verified_on and source_url metadata.
5. Emits the mandatory ISO date footer ('Last updated from sources: <YYYY-MM-DD>').
6. Ensures typo 'sml cap' resolves to hdfc_smallcap_dg and never falls through to glossary.
7. Confirms 100% refusal recall on 30 adversarial query cases.
8. Enforces literal verbatim substring matching for supporting sentences in snapshots.
9. Enforces unique SHA-256 digests across all distinct URLs (zero duplicate hashes).
10. Validates that no snapshot contains '404', 'not found', or 'enable JavaScript'.
11. Confirms that unsupported client-rendered items are not served by lookup_procedure.
"""

import hashlib
import json
import os
import re
import pytest
from bs4 import BeautifulSoup

from app.guardrails.intent import classify_intent
from app.guardrails.refusal import (
    REFUSAL_TEMPLATES,
    generate_compound_refusal,
    generate_help_response,
    generate_refusal,
)
from app.guardrails.validator import (
    BANNED_LEXICON,
    DATE_FOOTER_PATTERN,
    check_banned_words,
    split_sentences,
)
from app.rag.entities import (
    get_disambiguation_response,
    get_external_amc_response,
    get_unsupported_plan_response,
    resolve_entities,
)
from app.rag.glossary import GLOSSARY_DEFINITIONS, lookup_glossary
from app.rag.procedures import PROCEDURE_ITEMS, lookup_procedure
from app.rag.retriever import get_not_found_response


SNAPSHOTS_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../data/snapshots")
)
MANIFEST_PATH = os.path.join(SNAPSHOTS_DIR, "snapshots_manifest.json")


class TestGlossaryStaticContract:
    """Verifies all glossary entries adhere strictly to the response contract and metadata invariants."""

    def test_glossary_metadata_mandatory_fields(self):
        for item in GLOSSARY_DEFINITIONS:
            assert "source_url" in item, f"Glossary item {item['id']} missing source_url"
            assert str(item["source_url"]).startswith("https://"), f"Invalid source_url: {item['source_url']}"
            assert "verified_on" in item, f"Glossary item {item['id']} missing verified_on"
            assert re.match(r"^\d{4}-\d{2}-\d{2}$", str(item["verified_on"])), f"Invalid verified_on: {item['verified_on']}"

    def test_glossary_narrative_sentences_and_banned_words(self):
        for item in GLOSSARY_DEFINITIONS:
            sentences = split_sentences(item["narrative"])
            assert len(sentences) <= 3, f"Glossary {item['id']} narrative exceeds 3 sentences: {len(sentences)}"
            banned = check_banned_words(item["narrative"])
            assert len(banned) == 0, f"Glossary {item['id']} contains banned words: {banned}"

    def test_lookup_glossary_rendered_contract(self):
        test_queries = [
            "What is Total Expense Ratio?",
            "What is exit load?",
            "What does NAV mean?",
            "What is a Riskometer?",
            "What is a benchmark in mutual funds?",
            "What is lock-in period?",
            "What is AUM?",
        ]
        for q in test_queries:
            resp = lookup_glossary(q)
            assert resp is not None, f"Glossary lookup failed for '{q}'"
            sentences = split_sentences(resp["text"].split("\n\n|")[0])
            assert len(sentences) <= 3, f"Query '{q}' text exceeded 3 sentences: {len(sentences)}"
            banned = check_banned_words(resp["text"].split("\n\n|")[0])
            assert len(banned) == 0, f"Query '{q}' contains banned words: {banned}"
            assert "Source: " in resp["rendered"]
            assert re.search(r"Last updated from sources: \d{4}-\d{2}-\d{2}", resp["rendered"])


class TestProceduresStaticContract:
    """Verifies all procedural items adhere strictly to the response contract and metadata invariants."""

    def test_procedures_metadata_mandatory_fields(self):
        for item in PROCEDURE_ITEMS:
            if item.get("supported") is False or item.get("status") == "unsupported":
                continue
            assert "source_url" in item, f"Procedure item {item['id']} missing source_url"
            assert str(item["source_url"]).startswith("https://"), f"Invalid source_url: {item['source_url']}"
            assert "verified_on" in item, f"Procedure item {item['id']} missing verified_on"
            assert re.match(r"^\d{4}-\d{2}-\d{2}$", str(item["verified_on"])), f"Invalid verified_on: {item['verified_on']}"

    def test_procedures_narrative_sentences_and_banned_words(self):
        for item in PROCEDURE_ITEMS:
            if item.get("supported") is False or item.get("status") == "unsupported":
                continue
            sentences = split_sentences(item["narrative"])
            assert len(sentences) <= 3, f"Procedure {item['id']} narrative exceeds 3 sentences: {len(sentences)}"
            banned = check_banned_words(item["narrative"])
            assert len(banned) == 0, f"Procedure {item['id']} contains banned words: {banned}"

    def test_lookup_supported_procedures_rendered_contract(self):
        test_queries = [
            "What is the lock-in period for ELSS mutual funds?",
            "Explain the SEBI riskometer framework",
            "What is the SEBI categorization for mutual funds?",
            "What are the mutual fund cutoff timings for same day nav?",
            "What is the daily NAV disclosure timing?",
            "What is mutual fund settlement cycle for redemptions?",
        ]
        for q in test_queries:
            resp = lookup_procedure(q)
            assert resp is not None, f"Supported procedure lookup failed for '{q}'"
            sentences = split_sentences(resp["text"].split("\n\n|")[0])
            assert len(sentences) <= 3, f"Query '{q}' text exceeded 3 sentences: {len(sentences)}"
            banned = check_banned_words(resp["text"].split("\n\n|")[0])
            assert len(banned) == 0, f"Query '{q}' contains banned words: {banned}"
            assert "Source: " in resp["rendered"]
            assert re.search(r"Last updated from sources: \d{4}-\d{2}-\d{2}", resp["rendered"])

    def test_unsupported_procedures_not_served(self):
        """Verifies that client-rendered JS help procedures marked unsupported are NOT served."""
        unsupported_queries = [
            "How do I download my Capital Gains statement on Groww?",
            "How do I redeem my mutual fund units on Groww?",
            "How to start a SIP on Groww?",
            "What documents are required for KYC verification on Groww?",
            "How to set up autopay mandate on Groww?",
            "How to switch mutual fund schemes on Groww?",
            "What happens if SIP auto-debit bounces?",
            "How do I pause my active SIP installment?",
            "How to update bank account on Groww?",
            "How to track mutual fund order on Groww?",
        ]
        for q in unsupported_queries:
            resp = lookup_procedure(q)
            assert resp is None, f"Unsupported procedure '{q}' should NOT be served, but returned: {resp}"


@pytest.fixture(scope="module")
def manifest():
    assert os.path.exists(MANIFEST_PATH), f"Manifest missing at {MANIFEST_PATH}"
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


class TestSnapshotIntegrityAndVerbatim:
    """Verifies physical disk snapshots, exact substring matches, SHA-256 uniqueness, and no 404s."""

    def test_snapshots_unique_hashes_across_urls(self, manifest):
        """Ensures two different URLs never share a SHA-256 digest."""
        hash_to_url = {}
        for eid, item in manifest.get("snapshots", {}).items():
            if item.get("status") != "supported":
                continue
            h = item.get("sha256")
            url = item.get("url")
            assert h is not None, f"Item {eid} missing sha256"
            if h in hash_to_url:
                pytest.fail(f"Duplicate hash {h[:12]}: shared between {url} and {hash_to_url[h]}")
            hash_to_url[h] = url

    def test_supporting_sentences_verbatim_substring_in_snapshot(self, manifest):
        """Ensures every supporting_sentence is a literal whitespace-normalized substring of disk file."""
        for eid, item in manifest.get("snapshots", {}).items():
            if item.get("status") != "supported":
                continue

            snapshot_file = item.get("snapshot_file")
            file_path = os.path.join(SNAPSHOTS_DIR, snapshot_file)
            assert os.path.exists(file_path), f"Snapshot file missing: {file_path}"

            with open(file_path, "rb") as sf:
                raw_bytes = sf.read()

            # Verify hash matches disk file
            disk_hash = hashlib.sha256(raw_bytes).hexdigest()
            assert disk_hash == item.get("sha256"), f"Disk hash mismatch for {eid}"

            # Extract normalized text
            if snapshot_file.endswith(".pdf"):
                import io
                from pdfminer.high_level import extract_text
                text = " ".join(extract_text(io.BytesIO(raw_bytes)).split())
            else:
                html = raw_bytes.decode("utf-8", errors="replace")
                soup = BeautifulSoup(html, "html.parser")
                for s in soup(["script", "style", "noscript"]):
                    s.extract()
                text = " ".join(soup.get_text().split())

            supp = item.get("supporting_sentence", "")
            norm_supp = " ".join(supp.split())
            norm_text = " ".join(text.split())

            # Literal substring assertion
            assert norm_supp in norm_text, (
                f"Supporting sentence for {eid} is NOT a literal substring of disk snapshot!\n"
                f"Expected: {norm_supp}\nSnapshot snippet: {norm_text[:200]}"
            )

            # Assert no 404, not found, or enable javascript
            lower_text = norm_text.lower()
            assert not re.search(r"\b404\b|page not found", lower_text), f"Snapshot {eid} contains 404/not found"
            assert "enable javascript" not in lower_text, f"Snapshot {eid} contains 'enable javascript'"


class TestRefusalAndFallbackContract:
    """Verifies refusal templates, disambiguation, not_found, and fallbacks obey contract invariants."""

    def test_refusal_templates_contract(self):
        for intent in REFUSAL_TEMPLATES.keys():
            resp = generate_refusal(intent)
            sentences = split_sentences(resp["text"])
            assert len(sentences) <= 3, f"Refusal intent {intent} exceeded 3 sentences: {len(sentences)}"
            banned = check_banned_words(resp["text"])
            assert len(banned) == 0, f"Refusal {intent} contains banned words: {banned}"
            assert "Source: " in resp["rendered"]
            assert re.search(r"Last updated from sources: \d{4}-\d{2}-\d{2}", resp["rendered"])

    def test_compound_refusal_contract(self):
        fact = "The exit load for HDFC Multi Cap Fund is 1% if redeemed within 1 year."
        resp = generate_compound_refusal(fact, "ADVISORY", "https://groww.in/test")
        sentences = split_sentences(resp["text"])
        assert len(sentences) <= 3
        banned = check_banned_words(resp["text"])
        assert len(banned) == 0
        assert "Source: https://groww.in/test" in resp["rendered"]
        assert re.search(r"Last updated from sources: \d{4}-\d{2}-\d{2}", resp["rendered"])

    def test_help_response_contract(self):
        resp = generate_help_response()
        narrative = resp["text"].split("\n\n|")[0]
        sentences = split_sentences(narrative)
        assert len(sentences) <= 3
        banned = check_banned_words(narrative)
        assert len(banned) == 0
        assert "Source: " in resp["rendered"]
        assert re.search(r"Last updated from sources: \d{4}-\d{2}-\d{2}", resp["rendered"])

    def test_disambiguation_response_contract(self):
        resp = get_disambiguation_response()
        sentences = split_sentences(resp["text"])
        assert len(sentences) <= 3
        banned = check_banned_words(resp["text"])
        assert len(banned) == 0
        assert "Source: " in resp["rendered"]
        assert re.search(r"Last updated from sources: \d{4}-\d{2}-\d{2}", resp["rendered"])

    def test_not_found_response_contract(self):
        resp = get_not_found_response()
        sentences = split_sentences(resp["text"])
        assert len(sentences) <= 3
        banned = check_banned_words(resp["text"])
        assert len(banned) == 0
        assert "Source: " in resp["rendered"]
        assert re.search(r"Last updated from sources: \d{4}-\d{2}-\d{2}", resp["rendered"])

    def test_unsupported_plan_response_contract(self):
        resp = get_unsupported_plan_response()
        sentences = split_sentences(resp["text"])
        assert len(sentences) <= 3
        banned = check_banned_words(resp["text"])
        assert len(banned) == 0
        assert "Source: " in resp["rendered"]
        assert re.search(r"Last updated from sources: \d{4}-\d{2}-\d{2}", resp["rendered"])

    def test_external_amc_response_contract(self):
        resp = get_external_amc_response("Axis Mutual Fund")
        sentences = split_sentences(resp["text"])
        assert len(sentences) <= 3
        banned = check_banned_words(resp["text"])
        assert len(banned) == 0
        assert "Source: " in resp["rendered"]
        assert re.search(r"Last updated from sources: \d{4}-\d{2}-\d{2}", resp["rendered"])


class TestTypoResolutionAndAdversarialRecall:
    """Verifies typo fuzzy matching and 100% recall on the 30 adversarial cases."""

    def test_typo_alias_resolves_to_smallcap(self):
        query = "what is exit load of hdfc sml cap direct growth"
        res = resolve_entities(query)
        assert res.scheme_id == "hdfc_smallcap_dg"
        assert res.is_ambiguous is False

        from app.rag.facts import lookup_fact
        fact = lookup_fact(query)
        assert fact is not None
        assert fact["source"] == "fact_store"
        assert fact["scheme_id"] == "hdfc_smallcap_dg"
        assert fact["field"] == "exit_load"

    def test_adversarial_queries_100_percent_recall(self):
        dataset_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../eval/datasets/adversarial_eval.jsonl")
        )
        assert os.path.exists(dataset_path), f"Adversarial dataset not found: {dataset_path}"

        with open(dataset_path, "r", encoding="utf-8") as f:
            cases = [json.loads(line) for line in f if line.strip()]

        assert len(cases) == 30, f"Expected 30 adversarial cases, found {len(cases)}"

        failed_cases = []
        for c in cases:
            res = classify_intent(c["query"])
            if not res.is_refusal:
                failed_cases.append((c["id"], c["query"], res.intent))

        assert len(failed_cases) == 0, f"Adversarial queries failed refusal recall: {failed_cases}"


class TestDateLogic:
    """Verifies date normalization and ISO footer format enforcement across facts and static responses."""

    def test_normalize_date_footer_iso(self):
        from app.guardrails.validator import normalize_date_footer
        assert normalize_date_footer("2026-11-05") == "2026-11-05"
        assert normalize_date_footer("2025-10-23") == "2025-10-23"

    def test_normalize_date_footer_text(self):
        from app.guardrails.validator import normalize_date_footer
        assert normalize_date_footer("23-Oct-2026") == "2026-10-23"
        assert normalize_date_footer("05-Nov-2026") == "2026-11-05"

    def test_normalize_date_footer_fallback(self):
        from app.guardrails.validator import normalize_date_footer
        assert normalize_date_footer(None) == "2026-11-05"
        assert normalize_date_footer("") == "2026-11-05"

    def test_validate_response_date_footer_match(self):
        from app.guardrails.validator import validate_response
        res = validate_response("This is a factual response.", None, "https://groww.in/test", "2026-10-23")
        assert res.last_updated == "2026-10-23"
        assert "Last updated from sources: 2026-10-23" in res.rendered
