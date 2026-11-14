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
    LISTED_NAMES_LIMIT,
    SCHEME_COUNT,
    SCHEME_REGISTRY,
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
    owners = {}
    for sid, meta in SCHEME_REGISTRY.items():
        for alias in meta["aliases"]:
            assert alias == alias.lower().strip(), f"{sid}: alias {alias!r} must be lower case"
            assert alias not in owners, f"alias {alias!r} is claimed by {owners[alias]} and {sid}"
            owners[alias] = sid


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
    assert f"{SCHEME_COUNT} HDFC Mutual Fund" in readme
    for meta in SCHEME_REGISTRY.values():
        assert scheme_label(meta) in readme, f"README does not list {scheme_label(meta)}"


def test_blanket_claims_about_all_schemes_are_reviewed_when_the_count_changes():
    """Static text says things like 'all 5 supported HDFC schemes have 0 lock-in'.

    When this fails, a scheme was added: re-read those claims (minimum amount, lock-in, ELSS wording)
    and fix them, then update the number.
    """
    for rel in ("backend/app/rag/procedures.py", "ingest/build_official_corpus.py"):
        text = (REPO_ROOT / rel).read_text(encoding="utf-8")
        for n in re.findall(r"(\d+) supported HDFC schemes", text):
            assert int(n) == SCHEME_COUNT, f"{rel} claims {n} supported schemes, registry has {SCHEME_COUNT}"


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
