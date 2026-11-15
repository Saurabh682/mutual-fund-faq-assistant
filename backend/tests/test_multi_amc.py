"""Two fund houses in one assistant: names they share are asked about, never guessed.

A fund house word narrows a question to that fund house; a bare category name that both use ("mid cap fund")
gets a clarification with one button-ready option per scheme; text about the scope names every fund house.
"""

import pytest
from fastapi.testclient import TestClient

from app.core.schemes import FUND_HOUSES, SCHEME_COUNT, SCHEME_REGISTRY, SCOPE_NAME, scheme_label
from app.main import app
from app.rag.entities import _FIELD_QUESTIONS, get_clarification_response, resolve_entities

client = TestClient(app)

SHARED_NAMES = ["mid cap fund", "large cap fund", "multi cap fund"]


def _ask(query: str) -> dict:
    resp = client.post("/api/v1/rag/ask", json={"query": query})
    assert resp.status_code == 200
    return resp.json()


@pytest.mark.parametrize("scheme_id", list(SCHEME_REGISTRY))
def test_every_scheme_resolves_from_its_full_name(scheme_id):
    meta = SCHEME_REGISTRY[scheme_id]
    for name in {scheme_label(meta), meta["name"]}:
        res = resolve_entities(f"What is the expense ratio of {name}?")
        assert res.scheme_id == scheme_id, name
        assert res.ambiguous_scheme_ids == [], name


@pytest.mark.parametrize("scheme_id", list(SCHEME_REGISTRY))
@pytest.mark.parametrize("field", list(_FIELD_QUESTIONS))
def test_a_clarification_option_resolves_back_to_its_scheme_and_field(scheme_id, field):
    prompt = _FIELD_QUESTIONS[field].format(n=scheme_label(SCHEME_REGISTRY[scheme_id]))
    res = resolve_entities(prompt)
    assert (res.scheme_id, res.field) == (scheme_id, field), prompt


@pytest.mark.parametrize("name", SHARED_NAMES)
def test_a_name_both_fund_houses_use_asks_which_scheme(name):
    query = f"What is the expense ratio of {name}?"
    res = resolve_entities(query)
    assert res.scheme_id is None
    assert {SCHEME_REGISTRY[s]["amc"] for s in res.ambiguous_scheme_ids} == set(FUND_HOUSES)
    assert res.needs_scheme_choice

    data = _ask(query)
    assert data["resolution_type"] == "clarification"
    assert "HDFC" in data["text"] and "Mahindra Manulife" in data["text"]


def test_clarification_options_repeat_the_question_for_each_candidate():
    clarification = get_clarification_response(resolve_entities("What is the exit load of mid cap fund?"))
    assert [o["id"] for o in clarification["options"]] == ["hdfc_midcap_dg", "mahindra_midcap_dg"]
    for option in clarification["options"]:
        assert option["label"] in option["prompt"]
        assert "exit load" in option["prompt"].lower()
        assert resolve_entities(option["prompt"]).scheme_id == option["id"]


def test_a_named_fund_house_narrows_the_clarification_to_its_schemes():
    res = resolve_entities("What is the expense ratio of Mahindra?")
    assert res.scheme_id is None and res.named_fund_house_ids == ["mahindra"]
    options = get_clarification_response(res)["options"]
    assert options and all(SCHEME_REGISTRY[o["id"]]["amc"] == "mahindra" for o in options)


def test_a_shared_name_is_not_answered_with_a_generic_definition():
    # "expense ratio" is also a glossary term; the question is about a fund, so the clarification comes first
    assert _ask("What is the expense ratio of mid cap fund?")["resolution_type"] == "clarification"


@pytest.mark.parametrize(
    "query, scheme_id",
    [
        ("What is the TER of Mahindra mid cap fund?", "mahindra_midcap_dg"),
        ("expense ratio of hdfc mid cap", "hdfc_midcap_dg"),
        ("liquid fund of mahindra exit load", "mahindra_liquid_dg"),
        ("ultra short to short term fund exit load mahindra", "mahindra_ultra_short_short_dg"),
        ("What is the TER of Mahindra Manulife Large & Mid Cap Fund?", "mahindra_largemid_dg"),
        ("What is the NAV of manulife focused fund?", "mahindra_focused_dg"),
    ],
)
def test_fund_house_words_pick_the_scheme(query, scheme_id):
    res = resolve_entities(query)
    assert res.scheme_id == scheme_id
    assert res.ambiguous_scheme_ids == []


def test_the_longer_name_wins_over_the_name_inside_it():
    assert resolve_entities("TER of Mahindra Manulife Large and Mid Cap Fund").scheme_id == "mahindra_largemid_dg"


def test_the_session_scheme_breaks_a_tie_between_fund_houses():
    res = resolve_entities("and the exit load of mid cap fund?", session_scheme_id="mahindra_largecap_dg")
    assert res.scheme_id == "mahindra_midcap_dg"
    res = resolve_entities("and the exit load of mid cap fund?", session_scheme_id="hdfc_smallcap_dg")
    assert res.scheme_id == "hdfc_midcap_dg"


def test_another_fund_house_with_a_similar_name_is_out_of_scope():
    res = resolve_entities("What is the expense ratio of Kotak Mahindra mid cap fund?")
    assert res.is_external_amc and res.scheme_id is None and not res.ambiguous_scheme_ids


@pytest.mark.parametrize(
    "query",
    [
        "What is the lock-in period for ELSS mutual funds?",
        "What is a liquid fund?",
        "What is an arbitrage fund?",
    ],
)
def test_generic_questions_are_not_taken_for_a_scheme(query):
    res = resolve_entities(query)
    assert res.scheme_id is None and not res.ambiguous_scheme_ids


def test_a_category_name_suggests_its_scheme_but_does_not_choose_it():
    res = resolve_entities("What is the exit load of a liquid fund?")
    assert res.scheme_id is None
    assert res.suggested_scheme_ids == ["mahindra_liquid_dg"]


def test_scope_wording_names_every_fund_house():
    from app.guardrails.refusal import REFUSAL_TEMPLATES

    for key in ("OUT_OF_SCOPE", "SMALLTALK", "HELP"):
        for house in FUND_HOUSES.values():
            assert house["short_name"] in REFUSAL_TEMPLATES[key], key

    data = _ask("Who is the CEO of Mahindra Manulife AMC?")
    assert f"{SCHEME_COUNT} {SCOPE_NAME} schemes" in data["rendered"]
    assert data["citation_url"].startswith(FUND_HOUSES["mahindra"]["website"])


def test_amc_level_citation_is_the_named_fund_houses_site():
    data = _ask("Who is the Chief Executive Officer (CEO) of HDFC AMC?")
    assert data["citation_url"].startswith(FUND_HOUSES["hdfc"]["website"])


@pytest.mark.parametrize("scheme_id", list(SCHEME_REGISTRY))
def test_fact_cards_name_the_schemes_own_fund_house(scheme_id):
    from app.rag.facts import format_fact_response

    meta = SCHEME_REGISTRY[scheme_id]
    fact = {"scheme_id": scheme_id, "field": "amc_name", "value": meta["publisher"], "as_of": "2026-11-05"}
    text = format_fact_response(fact)["text"]
    assert meta["publisher"] in text
    for house in FUND_HOUSES.values():
        if house["id"] != meta["amc"]:
            assert house["publisher"] not in text and house["website"].split("//")[1].removeprefix("www.") not in text


def test_a_value_the_groww_page_does_not_list_reads_as_such():
    from app.rag.facts import NOT_LISTED, format_fact_response

    for field in ("min_sip", "ter_direct", "exit_load"):
        fact = {"scheme_id": "mahindra_overnight_dg", "field": field, "value": NOT_LISTED, "as_of": "2026-11-05"}
        text = format_fact_response(fact)["text"]
        assert "not listed on the Groww scheme page" in text
        assert "₹Not" not in text and "%Not" not in text and "Not listed on the Groww page%" not in text


def test_thread_clarification_carries_its_options():
    thread = client.post("/api/v1/threads", json={"client_id": "multi-amc-test"}).json()
    resp = client.post(
        f"/api/v1/threads/{thread['id']}/messages",
        json={"text": "What is the minimum SIP of large cap fund?"},
        headers={"X-Client-Id": "multi-amc-test"},
    )
    assert resp.status_code == 200
    msg = resp.json()
    assert msg["type"] == "clarification"
    assert [o["id"] for o in msg["options"]] == ["hdfc_largecap_dg", "mahindra_largecap_dg"]
    assert all("minimum SIP" in o["prompt"] for o in msg["options"])


def test_reloading_a_thread_keeps_clarification_options_and_followups():
    thread = client.post("/api/v1/threads", json={"client_id": "multi-amc-reload"}).json()
    headers = {"X-Client-Id": "multi-amc-reload"}
    sent = client.post(
        f"/api/v1/threads/{thread['id']}/messages", json={"text": "What is the exit load of mid cap fund?"}, headers=headers
    ).json()
    reloaded = client.get(f"/api/v1/threads/{thread['id']}", headers=headers).json()["messages"][-1]
    assert reloaded["options"] == sent["options"] and len(sent["options"]) == 2
    assert reloaded["suggested_followups"] == sent["suggested_followups"]
