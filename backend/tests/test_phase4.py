"""Phase 4 Test Suite: Constrained LLM Synthesis & Output Contract Validator.

Verifies:
1. EC-VAL-01: Sentence Splitting with Currency and Decimal Protection (₹102.50, 0.74%, Rs. 100).
2. EC-LLM-01: Sentence Ceiling Enforcement (<= 3 sentences, programmatic truncation).
3. Banned Lexicon Rejection: Evaluative and advisory words trigger rejection.
4. EC-LLM-02: Numeric Grounding: Hallucinated numbers not in source chunks are caught and rejected.
5. EC-LLM-03: Model URL Stripping: LLM-generated URLs are stripped, programmatic canonical URL appended.
6. EC-VAL-02: Date Footer Invariant: 'Last updated from sources: <YYYY-MM-DD>'.
7. Repair Loop: Automatic retry when model output violates constraints before falling closed.
8. Live Groq LLM Synthesis: Factual procedural query answering within <= 3 sentences.
9. End-to-End POST /api/v1/rag/ask API orchestration across all resolution paths.
"""

import re
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.guardrails.validator import (
    BANNED_LEXICON,
    DATE_FOOTER_PATTERN,
    check_banned_words,
    safe_contract_fallback,
    split_sentences,
    strip_urls,
    validate_response,
    verify_numeric_grounding,
)
from app.rag.prompts import (
    SYSTEM_SYNTHESIS_PROMPT,
    build_repair_prompt,
    build_synthesis_user_prompt,
)
from app.rag.synthesizer import ConstrainedSynthesizer

client = TestClient(app)


class TestSentenceTokenizerEC_VAL_01:
    """EC-VAL-01: Verify sentence splitting respects financial decimals and currency."""

    def test_decimal_nav_and_ter_not_split(self):
        text = "The NAV of HDFC Mid-Cap is ₹102.50 as of Oct 2026. The TER is 0.74% for Direct Plan."
        sentences = split_sentences(text)
        assert len(sentences) == 2
        assert sentences[0] == "The NAV of HDFC Mid-Cap is ₹102.50 as of Oct 2026."
        assert sentences[1] == "The TER is 0.74% for Direct Plan."

    def test_abbreviation_dot_not_split(self):
        text = "Minimum investment is Rs. 100 per month. Units are allocated on NAV date."
        sentences = split_sentences(text)
        assert len(sentences) == 2
        assert "Rs. 100" in sentences[0]

    def test_three_sentences_preserved(self):
        text = "First sentence here. Second sentence with ₹500 amount. Third sentence concludes the point."
        sentences = split_sentences(text)
        assert len(sentences) == 3

    def test_empty_and_single_sentence(self):
        assert split_sentences("") == []
        assert len(split_sentences("Single sentence without punctuation")) == 1
        assert len(split_sentences("Single sentence with period.")) == 1


class TestSentenceCeilingEnforcementEC_LLM_01:
    """EC-LLM-01: Output Contract ensures response NEVER exceeds 3 sentences."""

    def test_four_sentences_truncated_to_three(self):
        draft = "Sentence one. Sentence two. Sentence three. Sentence four that should be cut off."
        chunks = ["Sentence one. Sentence two. Sentence three. Sentence four that should be cut off."]
        res = validate_response(draft, chunks, "https://groww.in/test", "2026-10-25")

        assert res.is_valid is True
        assert res.sentence_count == 3
        assert res.repaired is True
        assert "Sentence four" not in res.text

    def test_five_sentences_truncated_to_three(self):
        draft = "One. Two. Three. Four. Five."
        chunks = ["One. Two. Three. Four. Five."]
        res = validate_response(draft, chunks, "https://groww.in/test", "2026-10-25")

        assert res.is_valid is True
        assert res.sentence_count == 3
        assert res.text == "One. Two. Three."


class TestBannedLexiconRejection:
    """Verifies that evaluative, opinionated, or advisory terms trigger contract invalidation."""

    @pytest.mark.parametrize(
        "word",
        [
            "good", "great", "best", "better", "safe", "safest", "attractive",
            "lucrative", "recommended", "ideal", "guaranteed", "outperform",
        ],
    )
    def test_banned_words_detected(self, word: str):
        text = f"This fund is a {word} choice for investment."
        hits = check_banned_words(text)
        assert word in hits

        res = validate_response(text, [text], "https://groww.in/test", "2026-10-25")
        assert res.is_valid is False
        assert any("BANNED_WORDS" in reason for reason in res.violation_reasons)


class TestNumericGroundingEC_LLM_02:
    """EC-LLM-02: Verifies that numbers/percentages not in source context are rejected."""

    def test_grounded_numbers_pass(self):
        chunks = ["Minimum SIP is ₹100 and exit load is 1% if redeemed within 365 days."]
        draft = "The minimum SIP is ₹100. The exit load is 1% within 365 days."

        is_grounded, ungrounded = verify_numeric_grounding(draft, chunks)
        assert is_grounded is True
        assert ungrounded == []

        res = validate_response(draft, chunks, "https://groww.in/test", "2026-10-25")
        assert res.is_valid is True

    def test_hallucinated_number_rejected(self):
        chunks = ["Minimum SIP is ₹100 and exit load is 1% if redeemed within 365 days."]
        # Model hallucinated ₹500 and 5 years
        draft = "The minimum SIP is ₹500. The holding tenure is 5 years."

        is_grounded, ungrounded = verify_numeric_grounding(draft, chunks)
        assert is_grounded is False
        assert "500" in ungrounded or "5" in ungrounded

        res = validate_response(draft, chunks, "https://groww.in/test", "2026-10-25")
        assert res.is_valid is False
        assert any("UNGROUNDED_NUMBERS" in r for r in res.violation_reasons)


class TestURLStrippingAndAttachmentEC_LLM_03:
    """EC-LLM-03: Model-generated URLs stripped; exactly 1 canonical URL attached."""

    def test_model_generated_urls_stripped(self):
        draft = "Details are at https://hdfcfund.com/fund-info and www.groww.in/bogus. Check it out."
        clean = strip_urls(draft)
        assert "https://" not in clean
        assert "www." not in clean
        assert clean == "Details are at and . Check it out."

    def test_programmatic_citation_attached(self):
        draft = "The minimum SIP is ₹100."
        chunks = ["The minimum SIP is ₹100."]
        url = "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth"
        doc_date = "2026-10-25"

        res = validate_response(draft, chunks, url, doc_date)
        assert res.is_valid is True
        assert res.citation_url == url
        assert f"Source: {url}" in res.rendered
        assert f"Last updated from sources: {doc_date}" in res.rendered


class TestDateFooterInvariantEC_VAL_02:
    r"""EC-VAL-02: Verifies that footer matches regex ^Last updated from sources: \d{4}-\d{2}-\d{2}$."""

    def test_date_footer_regex(self):
        res = safe_contract_fallback(
            "https://groww.in/test", "2026-10-25", reason="TEST"
        )
        footer_line = res.rendered.split("\n")[-1]
        assert DATE_FOOTER_PATTERN.match(footer_line) is not None


class TestPromptBuilders:
    """Verifies that prompt builders produce compliant templates."""

    def test_system_prompt_rules(self):
        assert "Maximum 3 sentences" in SYSTEM_SYNTHESIS_PROMPT
        assert "Never give advice" in SYSTEM_SYNTHESIS_PROMPT
        assert "NOT_FOUND" in SYSTEM_SYNTHESIS_PROMPT

    def test_user_prompt_structure(self):
        p = build_synthesis_user_prompt("How to invest?", ["Step 1. Complete KYC.", "Step 2. Make payment."])
        assert "CONTEXT:" in p
        assert "[1] Step 1. Complete KYC." in p
        assert "[2] Step 2. Make payment." in p
        assert "QUESTION:\nHow to invest?" in p

    def test_repair_prompt_structure(self):
        p = build_repair_prompt("How to invest?", ["Step 1."], "Bad draft.", "BANNED_WORDS:best")
        assert "violated the strict output contract: BANNED_WORDS:best" in p
        assert "PREVIOUS DRAFT:\n\"Bad draft.\"" in p


class TestLiveGroqSynthesis:
    """Verifies live Groq LLM synthesis against the 5-point Output Response Contract."""

    @pytest.fixture(autouse=True)
    def setup_synthesizer(self):
        self.synth = ConstrainedSynthesizer()

    def test_procedural_faq_synthesis(self):
        context = [
            "To redeem HDFC Small Cap Fund, log in to Groww, open the Dashboard, "
            "select HDFC Small Cap Fund, enter the redemption units or amount, "
            "and confirm the order. Redemption proceeds are credited within 3 working days."
        ]
        res = self.synth.synthesize(
            query="How to redeem HDFC Small Cap Fund?",
            context_chunks=context,
            primary_url="https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth",
            doc_date="2026-10-25",
        )

        assert res.is_valid is True
        assert res.sentence_count <= 3
        assert "https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth" in res.rendered
        assert "Last updated from sources: 2026-10-25" in res.rendered
        # Zero banned words
        assert check_banned_words(res.text) == []

    def test_not_found_context_synthesis(self):
        res = self.synth.synthesize(
            query="What is the color of the manager's car?",
            context_chunks=[],
            primary_url="https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth",
            doc_date="2026-10-25",
        )
        assert res.is_valid is True
        assert "I could not find official information regarding this topic" in res.text


class TestEndToEndAskEndpoint:
    """Verifies POST /api/v1/rag/ask across all resolution branches."""

    def test_ask_factual_fact_store_path(self):
        resp = client.post(
            "/api/v1/rag/ask",
            json={"query": "What is the expense ratio of HDFC Small Cap Direct Growth?"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["resolution_type"] == "fact_store"
        assert "0.8%" in data["text"]
        assert data["sentence_count"] <= 3
        assert "https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth" in data["citation_url"]
        assert "Last updated from sources:" in data["rendered"]
        assert data["latency_ms"] < 60.0

    def test_ask_advisory_refusal_path(self):
        resp = client.post(
            "/api/v1/rag/ask",
            json={"query": "Should I invest in HDFC Mid Cap Fund?"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["resolution_type"] == "refusal"
        assert "cannot offer investment advice" in data["text"]
        assert data["sentence_count"] <= 3
        assert data["citation_url"] == "https://www.amfiindia.com/investor-corner/knowledge-center"

    def test_ask_pii_firewall_blocks_request(self):
        resp = client.post(
            "/api/v1/rag/ask",
            json={"query": "My PAN is ABCPE1234F, what is my folio balance?"},
        )
        assert resp.status_code == 400
        data = resp.json()
        assert data["error"] == "PII_DETECTED"
        assert "PAN" in data["detected_types"]

    def test_ask_ambiguous_clarification_path(self):
        resp = client.post(
            "/api/v1/rag/ask",
            json={"query": "What is the minimum SIP?"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["resolution_type"] == "clarification"
        assert "Please specify which HDFC scheme" in data["text"]
        assert data["sentence_count"] == 1

    def test_ask_out_of_corpus_fallback_path(self):
        resp = client.post(
            "/api/v1/rag/ask",
            json={"query": "What is the expense ratio of SBI Bluechip Fund?"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["resolution_type"] == "not_found"
        assert "I could not find official information regarding this topic" in data["text"]
        assert data["citation_url"] == "https://www.amfiindia.com/investor-corner/knowledge-center"

    def test_ask_procedural_llm_synthesis_path(self):
        resp = client.post(
            "/api/v1/rag/ask",
            json={"query": "How to redeem HDFC Mid Cap Fund?"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["resolution_type"] == "llm_synthesis"
        assert data["sentence_count"] <= 3
        assert "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth" in data["citation_url"]
        assert "Last updated from sources:" in data["rendered"]
        assert len(data["chunks"]) > 0
