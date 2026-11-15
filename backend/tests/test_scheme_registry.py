"""Phase 9.0: the manifest is the one place that says which schemes exist.

A scheme is "complete" when every consumer can serve it. Adding a scheme to data/corpus_manifest.yaml
without its ground-truth row, facts, golden cases or README entry fails here, not in production.
"""

import json
import os
import re
import sqlite3
import sys
from collections import Counter
from pathlib import Path

import pytest
import yaml
from bs4 import BeautifulSoup

from app.core.config import settings
from app.core.schemes import (
    FUND_HOUSES,
    LISTED_NAMES_LIMIT,
    SCHEME_COUNT,
    SCHEME_REGISTRY,
    SCOPE_NAME,
    format_choices,
    scheme_label,
    scheme_options,
)

REPO_ROOT = Path(__file__).parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

REQUIRED_FACT_FIELDS = {
    "ter_direct", "exit_load", "min_sip", "min_lumpsum", "lock_in", "riskometer", "benchmark",
    "fund_manager", "nav", "aum",
}
MIN_GOLDEN_CASES_PER_SCHEME = 8

with open(os.path.join(settings.DATA_DIR, "corpus_manifest.yaml"), encoding="utf-8") as f:
    MANIFEST = yaml.safe_load(f)
SCHEME_IDS = list(SCHEME_REGISTRY)


def test_registry_is_built_from_the_manifest():
    assert SCHEME_IDS == [s["id"] for s in MANIFEST["schemes"]]
    assert SCHEME_COUNT == len(SCHEME_IDS) > 0
    assert [o["id"] for o in scheme_options()] == SCHEME_IDS


@pytest.mark.parametrize("scheme_id", SCHEME_IDS)
def test_scheme_entry_is_complete(scheme_id):
    meta = SCHEME_REGISTRY[scheme_id]
    for key in ("name", "official_name", "category", "url", "amc_url", "amfi_code", "amfi_url", "aliases"):
        assert meta[key], f"{scheme_id}: empty {key}"
    assert meta["official_name"].endswith(" (Direct - Growth)")
    assert meta["url"].startswith("https://groww.in/mutual-funds/")

    sources = [s for s in MANIFEST["sources"] if s["scheme_id"] == scheme_id]
    assert [s["url"] for s in sources] == [meta["url"]], f"{scheme_id}: needs exactly its Groww page in sources"
    official = [s for s in MANIFEST["official_sources"] if s.get("scheme_id") == scheme_id]
    assert [s["url"] for s in official] == [meta["amc_url"]], f"{scheme_id}: needs its AMC page in official_sources"


def test_aliases_belong_to_one_scheme():
    """An alias names one scheme, except a bare category name ("mid cap fund") two fund houses both use:
    the resolver asks which one is meant (test_multi_amc.py)."""
    owners = {}
    for sid, meta in SCHEME_REGISTRY.items():
        for alias in meta["aliases"]:
            assert alias == alias.lower().strip(), f"{sid}: alias {alias!r} must be lower case"
            owners.setdefault(alias, []).append(sid)
    house_words = [a for h in FUND_HOUSES.values() for a in h["aliases"]]
    for alias, sids in owners.items():
        houses = [SCHEME_REGISTRY[s]["amc"] for s in sids]
        assert len(houses) == len(set(houses)), f"alias {alias!r} is claimed twice within one fund house: {sids}"
        if len(sids) > 1:
            assert not any(alias.startswith(w) for w in house_words), f"{alias!r} names a fund house but is shared: {sids}"


def test_every_scheme_belongs_to_a_fund_house_and_is_named_after_it():
    for sid, meta in SCHEME_REGISTRY.items():
        house = FUND_HOUSES[meta["amc"]]
        assert sid.startswith(meta["amc"] + "_"), sid
        assert meta["name"].startswith(house["short_name"]), f"{sid}: {meta['name']!r} should start with {house['short_name']!r}"
        assert meta["publisher"] == house["publisher"]


def test_every_scheme_has_a_ground_truth_row():
    with open(os.path.join(settings.DATA_DIR, "ground_truth.yaml"), encoding="utf-8") as f:
        truth = yaml.safe_load(f)["schemes"]
    assert set(truth) == set(SCHEME_IDS)
    for sid, row in truth.items():
        missing = {"ter_direct", "exit_load", "min_sip", "riskometer", "fund_manager"} - set(row)
        assert not missing, f"{sid}: ground truth lacks {missing}"


def test_every_scheme_has_its_facts():
    conn = sqlite3.connect(settings.FACTS_DB_PATH)
    try:
        for sid in SCHEME_IDS:
            have = {r[0] for r in conn.execute("SELECT field FROM facts WHERE scheme_id = ?", (sid,))}
            assert REQUIRED_FACT_FIELDS <= have, f"{sid}: facts.db lacks {REQUIRED_FACT_FIELDS - have}"
    finally:
        conn.close()


def test_every_scheme_has_enough_golden_cases():
    path = REPO_ROOT / "eval" / "datasets" / "golden_mf_eval.jsonl"
    rows = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    counts = Counter(r["scheme"] for r in rows if r.get("scheme"))
    for sid in SCHEME_IDS:
        assert counts[sid] >= MIN_GOLDEN_CASES_PER_SCHEME, f"{sid}: {counts[sid]} golden cases"


def test_readme_lists_every_scheme_and_the_count():
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    assert f"{SCHEME_COUNT} {SCOPE_NAME} Mutual Fund" in readme
    for meta in SCHEME_REGISTRY.values():
        assert scheme_label(meta) in readme, f"README does not list {scheme_label(meta)}"


def test_blanket_claims_about_lock_in_are_reviewed_when_an_elss_scheme_is_added():
    """procedures.py and the ELSS source document say which supported scheme carries the ELSS lock-in and
    that the rest have none.

    When this fails, an ELSS scheme was added or removed: re-read those claims, fix them, then update the set.
    """
    elss = {sid for sid, meta in SCHEME_REGISTRY.items() if "ELSS" in meta["category"]}
    assert elss == {"mahindra_elss_dg"}
    for rel in ("backend/app/rag/procedures.py", "ingest/build_official_corpus.py"):
        text = (REPO_ROOT / rel).read_text(encoding="utf-8")
        assert "Mahindra Manulife ELSS Tax Saver Fund" in text, rel
        assert not re.search(r"\d+ supported \w+ schemes", text), f"{rel} states a scheme count: say it with SCHEME_COUNT or leave it out"


def test_not_listed_marker_is_the_same_in_ingest_and_backend():
    from app.rag.facts import NOT_LISTED
    from ingest.parsers.html import NOT_LISTED as INGEST_NOT_LISTED

    assert NOT_LISTED == INGEST_NOT_LISTED


def test_format_choices():
    assert format_choices(["A"]) == "A"
    assert format_choices(["A", "B"]) == "A or B"
    assert format_choices(["A", "B", "C"]) == "A, B, or C"
    names = [f"Fund {i}" for i in range(LISTED_NAMES_LIMIT + 4)]
    assert format_choices(names) == "Fund 0, Fund 1, Fund 2, Fund 3, or Fund 4"


def test_clarification_and_prompt_use_the_registry():
    from app.rag.entities import get_disambiguation_response
    from app.rag.prompts import SYSTEM_SYNTHESIS_PROMPT

    text = get_disambiguation_response()["text"]
    for meta in list(SCHEME_REGISTRY.values())[:LISTED_NAMES_LIMIT]:
        assert scheme_label(meta) in text
    for meta in SCHEME_REGISTRY.values():
        assert meta["name"] in SYSTEM_SYNTHESIS_PROMPT
    assert f"The {SCHEME_COUNT} schemes" in SYSTEM_SYNTHESIS_PROMPT


def test_factsheet_filenames_map_to_manifest_schemes():
    from ingest.factsheet_parser import SCHEME_NAME_MAP

    assert set(SCHEME_NAME_MAP.values()) <= set(SCHEME_IDS)
    assert len(SCHEME_NAME_MAP) == len(set(SCHEME_NAME_MAP.values()))


def _soup_with_managers(*names):
    cards = "".join(
        f'<div class="fundManagement_card"><span class="personName">{n}</span> Jan 2020 - Present</div>' for n in names
    )
    return BeautifulSoup(f"<html><body>{cards}</body></html>", "html.parser")


def test_pinned_fund_manager_wins_and_unpinned_schemes_use_the_page():
    from ingest.parsers.html import extract_active_fund_managers

    soup = _soup_with_managers("Someone Else")
    pinned = {sid: s["pinned_fund_manager"] for sid, s in ((s["id"], s) for s in MANIFEST["schemes"]) if s.get("pinned_fund_manager")}
    for sid, manager in pinned.items():
        assert extract_active_fund_managers(soup, sid) == manager
    assert extract_active_fund_managers(_soup_with_managers("A One", "B Two"), "not_a_pinned_scheme") == "A One, B Two"
    assert extract_active_fund_managers(_soup_with_managers(), "not_a_pinned_scheme", "Default Name") == "Default Name"
