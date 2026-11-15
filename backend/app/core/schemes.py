"""Scheme catalogue: the one place that knows which fund houses and schemes exist.

Reads `fund_houses` and `schemes` from data/corpus_manifest.yaml, so adding a scheme or a fund house is a
manifest entry (plus its ground-truth row), not a code change. Everything that lists schemes, matches their
names or says how many there are, and for which fund houses, reads from here.
"""

from __future__ import annotations

import os
import re
from typing import Any, Dict, List
from urllib.parse import urlparse

import yaml

from app.core.config import settings

LISTED_NAMES_LIMIT = 5
_PLAN_SUFFIX = " (Direct - Growth)"


def _load() -> tuple[Dict[str, Dict[str, Any]], Dict[str, Dict[str, Any]]]:
    with open(os.path.join(settings.DATA_DIR, "corpus_manifest.yaml"), "r", encoding="utf-8") as f:
        manifest = yaml.safe_load(f)
    houses = {
        h["id"]: {
            "id": h["id"],
            "name": h["name"],
            "short_name": h["short_name"],
            "publisher": h["publisher"],
            "website": h["website"],
            "aliases": h["aliases"],
            "ignore_phrases": h.get("ignore_phrases", []),
        }
        for h in manifest["fund_houses"]
    }
    registry: Dict[str, Dict[str, Any]] = {}
    for s in manifest["schemes"]:
        house = houses[s["amc"]]
        registry[s["id"]] = {
            "id": s["id"],
            "name": s["name"],
            "official_name": s["official_name"],
            "category": s["category"],
            "url": s["groww_url"],
            "amc_url": s["amc_portal_url"],
            "amfi_code": s["amfi_scheme_code"],
            "amfi_url": s["amfi_url"],
            "isin": s.get("isin", ""),
            "amc": house["id"],
            "amc_name": house["name"],
            "amc_short_name": house["short_name"],
            "amc_domain": urlparse(house["website"]).netloc.removeprefix("www."),
            "publisher": house["publisher"],
            "aliases": s["aliases"],
            "also_called": s.get("also_called", []),
        }
    return houses, registry


FUND_HOUSES, SCHEME_REGISTRY = _load()
SCHEME_COUNT = len(SCHEME_REGISTRY)


def _join_names(names: List[str]) -> str:
    if len(names) <= 2:
        return " and ".join(names)
    return ", ".join(names[:-1]) + f" and {names[-1]}"


# "HDFC and Mahindra Manulife": how user-facing text names the fund houses it covers
SCOPE_NAME = _join_names([h["short_name"] for h in FUND_HOUSES.values()])
# "HDFC Mutual Fund and Mahindra Manulife Mutual Fund": the full names, for the API's `amc` field
FUND_HOUSE_NAMES = _join_names([h["name"] for h in FUND_HOUSES.values()])


def scheme_options() -> List[Dict[str, str]]:
    """The scheme entries /api/v1/meta lists, with the fund house the UI groups them by."""
    return [
        {"id": s["id"], "name": s["official_name"], "amc": s["amc"], "amc_name": s["amc_name"]}
        for s in SCHEME_REGISTRY.values()
    ]


def scheme_label(meta: Dict[str, Any]) -> str:
    """Display name without the plan suffix, e.g. 'HDFC Silver ETF FoF'."""
    return meta["official_name"].removesuffix(_PLAN_SUFFIX)


def format_choices(labels: List[str], limit: int = LISTED_NAMES_LIMIT) -> str:
    """'A, B, or C' for the first `limit` labels, so a long catalogue never becomes a wall of names."""
    shown = labels[:limit]
    if len(shown) <= 2:
        return " or ".join(shown)
    return ", ".join(shown[:-1]) + f", or {shown[-1]}"


def _house_patterns() -> Dict[str, re.Pattern]:
    return {
        hid: re.compile(r"\b(?:" + "|".join(re.escape(a) for a in sorted(h["aliases"], key=len, reverse=True)) + r")\b")
        for hid, h in FUND_HOUSES.items()
    }


_HOUSE_PATTERNS = _house_patterns()


def fund_houses_named(normalized_query: str) -> List[str]:
    """Supported fund houses a (lower-case, normalised) query mentions, e.g. 'mahindra mid cap' -> ['mahindra'].

    A phrase listed under a house's ignore_phrases (Kotak Mahindra, for Mahindra Manulife) is a different
    fund house and is removed first.
    """
    found = []
    for hid, pattern in _HOUSE_PATTERNS.items():
        text = normalized_query
        for phrase in FUND_HOUSES[hid]["ignore_phrases"]:
            text = re.sub(r"\b" + re.escape(phrase) + r"\b", " ", text)
        if pattern.search(text):
            found.append(hid)
    return found


def fund_house_word_pattern() -> str:
    """Regex alternation of every supported fund-house alias, longest first."""
    aliases = sorted({a for h in FUND_HOUSES.values() for a in h["aliases"]}, key=len, reverse=True)
    return "|".join(re.escape(a) for a in aliases)
