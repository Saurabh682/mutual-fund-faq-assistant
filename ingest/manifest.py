"""The `schemes` list of data/corpus_manifest.yaml, for ingestion code that must not hard-code scheme ids."""

import os
from functools import lru_cache
from typing import Any, Dict

import yaml

MANIFEST_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "corpus_manifest.yaml")


@lru_cache(maxsize=1)
def load_schemes() -> Dict[str, Dict[str, Any]]:
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        return {s["id"]: s for s in yaml.safe_load(f)["schemes"]}
