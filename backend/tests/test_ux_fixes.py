"""Wording and typing fixes from the 2026-11 UX review of the live app."""

from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.api import threads as threads_api
from app.main import app
from app.rag.facts import format_fact_response, format_multi_fact_response, group_indian, plain_exit_load
from app.rag.synthesizer import NOT_FOUND_PREFIX, SynthesisResult, is_not_found

client = TestClient(app)


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("₹100687.07 Cr", "₹1,00,687.07 Cr"),
        ("₹1234567.5 Cr", "₹12,34,567.5 Cr"),
        ("₹38512.3 Cr", "₹38,512.3 Cr"),
        ("₹4521 Cr", "₹4,521 Cr"),
        ("₹101,856 Cr", "₹101,856 Cr"),  # already grouped: left alone
        ("₹229.697", "₹229.697"),
        ("0.73%", "0.73%"),
    ],
)
def test_group_indian(raw, expected):
    assert group_indian(raw) == expected


def test_exit_load_sentence_does_not_repeat_the_label():
    fact = {"scheme_id": "hdfc_smallcap_dg", "field": "exit_load", "value": "Exit load of 1% if redeemed within 1 year.", "as_of": "2026-11-13"}
    text = format_fact_response(fact)["text"]
    assert "is 1% if redeemed within 1 year." in text
    assert "is Exit load" not in text
    assert "| **Exit Load** | 1% if redeemed within 1 year |" in text
    assert plain_exit_load("Nil") == "Nil"


def test_aum_is_grouped_and_labelled():
    fact = {"scheme_id": "hdfc_midcap_dg", "field": "aum", "value": "₹100687.07 Cr", "as_of": "2026-11-13"}
    text = format_fact_response(fact)["text"]
    assert "₹1,00,687.07 Cr" in text
    assert "**AUM (Fund Size)**" in text and "**Aum**" not in text


def test_multi_fact_keeps_the_case_of_values():
    facts = [
        {"scheme_id": "hdfc_midcap_dg", "field": "benchmark", "value": "NIFTY Midcap 150 Total Return Index", "as_of": "2026-11-13"},
        {"scheme_id": "hdfc_midcap_dg", "field": "riskometer", "value": "Very High Risk", "as_of": "2026-11-13"},
    ]
    text = format_multi_fact_response(facts, "hdfc_midcap_dg")["text"]
    assert "NIFTY Midcap 150 Total Return Index" in text and "Very High Risk" in text
    assert "(ter)" not in text.lower() or "(TER)" in text


def _result(text, raw_draft=""):
    return SynthesisResult(text=text, sentence_count=1, citation_url="u", last_updated="2026-11-13", rendered=text, is_valid=True, raw_draft=raw_draft)


def test_is_not_found():
    assert is_not_found(_result("anything", raw_draft="NOT_FOUND"))
    assert is_not_found(_result(f"{NOT_FOUND_PREFIX}. I can answer questions about TER."))
    assert not is_not_found(_result("The minimum SIP investment amount for HDFC Top 100 Fund is ₹100."))


def _new_thread(client_id):
    resp = client.post("/api/v1/threads", json={"client_id": client_id, "title": "New Conversation"}, headers={"X-Client-Id": client_id})
    assert resp.status_code in (200, 201)
    return resp.json()["id"]


def _post(thread_id, client_id, text):
    return client.post(f"/api/v1/threads/{thread_id}/messages", json={"text": text}, headers={"X-Client-Id": client_id})


def test_thread_is_titled_even_when_its_first_message_is_blocked():
    cid = "ux_title_client"
    tid = _new_thread(cid)
    assert _post(tid, cid, "My PAN is ABCPE1234F").json()["type"] == "pii_block"
    assert _post(tid, cid, "What is the exit load of HDFC Small Cap Fund?").json()["type"] == "fact_store"
    title = client.get(f"/api/v1/threads/{tid}", headers={"X-Client-Id": cid}).json()["title"]
    assert title.startswith("What is the exit load")


def test_no_information_reply_is_typed_not_found(monkeypatch):
    chunk = SimpleNamespace(chunk_id="c1", text="context")
    monkeypatch.setattr(
        threads_api._retriever,
        "search",
        lambda **_: SimpleNamespace(is_out_of_corpus=False, chunks=[chunk], primary_citation_url="https://groww.in", primary_doc_date="2026-11-13"),
    )
    monkeypatch.setattr(
        threads_api._synthesizer,
        "synthesize",
        lambda **_: _result(f"{NOT_FOUND_PREFIX}. I can answer questions about TER.", raw_draft="NOT_FOUND"),
    )
    cid = "ux_nf_client"
    tid = _new_thread(cid)
    reply = _post(tid, cid, "How does HDFC Silver ETF FoF invest in silver?").json()
    assert reply["type"] == "not_found"
