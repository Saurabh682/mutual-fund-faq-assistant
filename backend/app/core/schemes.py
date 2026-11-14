"""Scheme catalogue: the one place that knows which schemes exist.

Reads the `schemes` list of data/corpus_manifest.yaml, so adding a scheme is a manifest entry
(plus its ground-truth row), not a code change. Everything that lists schemes, matches their
names or says how many there are reads from here.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List

import yaml

from app.core.config import settings

AMC_PUBLISHER = "HDFC Asset Management Company Limited"
LISTED_NAMES_LIMIT = 5
_PLAN_SUFFIX = " (Direct - Growth)"


def _load() -> Dict[str, Dict[str, Any]]:
    with open(os.path.join(settings.DATA_DIR, "corpus_manifest.yaml"), "r", encoding="utf-8") as f:
        manifest = yaml.safe_load(f)
    registry: Dict[str, Dict[str, Any]] = {}
    for s in manifest["schemes"]:
        registry[s["id"]] = {
            "id": s["id"],
            "name": s["name"],
            "official_name": s["official_name"],
            "category": s["category"],
            "url": s["groww_url"],
            "amc_url": s["amc_portal_url"],
            "amfi_code": s["amfi_scheme_code"],
            "amfi_url": s["amfi_url"],
            "publisher": AMC_PUBLISHER,
            "aliases": s["aliases"],
            "also_called": s.get("also_called", []),
        }
    return registry


SCHEME_REGISTRY: Dict[str, Dict[str, Any]] = _load()
SCHEME_COUNT = len(SCHEME_REGISTRY)


def scheme_options() -> List[Dict[str, str]]:
    """The id/name pairs the UI dropdowns and /api/v1/meta show."""
    return [{"id": s["id"], "name": s["official_name"]} for s in SCHEME_REGISTRY.values()]


def scheme_label(meta: Dict[str, Any]) -> str:
    """Display name without the plan suffix, e.g. 'HDFC Silver ETF FoF'."""
    return meta["official_name"].removesuffix(_PLAN_SUFFIX)


def format_choices(labels: List[str], limit: int = LISTED_NAMES_LIMIT) -> str:
    """'A, B, or C' for the first `limit` labels, so a long catalogue never becomes a wall of names."""
    shown = labels[:limit]
    if len(shown) <= 2:
        return " or ".join(shown)
    return ", ".join(shown[:-1]) + f", or {shown[-1]}"
