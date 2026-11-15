"""data/corpus_manifest.yaml for ingestion code that must not hard-code scheme ids or fund houses."""

import os
from functools import lru_cache
from typing import Any, Dict

import yaml

MANIFEST_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "corpus_manifest.yaml")


@lru_cache(maxsize=1)
def _manifest() -> Dict[str, Any]:
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_schemes() -> Dict[str, Dict[str, Any]]:
    return {s["id"]: s for s in _manifest()["schemes"]}


def load_fund_houses() -> Dict[str, Dict[str, Any]]:
    return {h["id"]: h for h in _manifest().get("fund_houses", [])}


def fund_house_of(scheme_id: str) -> Dict[str, Any]:
    """The fund house a scheme belongs to, or {} if the manifest does not say."""
    return load_fund_houses().get(load_schemes().get(scheme_id, {}).get("amc"), {})
