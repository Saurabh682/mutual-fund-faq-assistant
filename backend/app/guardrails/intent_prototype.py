"""Embedding-Prototype Intent Classifier for Compliance Guardrails.

Provides semantic similarity classification against curated advisory and factual
prototypes using the singleton SentenceTransformer instance.
Ensures zero-tolerance advisory screening before any LLM invocation.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import yaml

logger = logging.getLogger(__name__)

_PROTOTYPES_CACHE: Optional[Dict[str, List[str]]] = None
_CENTROIDS_CACHE: Optional[Dict[str, np.ndarray]] = None

PROTOTYPES_PATH = Path(__file__).resolve().parents[3] / "data" / "intent_prototypes.yaml"


def load_prototypes(path: Optional[Path] = None) -> Dict[str, List[str]]:
    """Loads advisory and factual prototype sentences from YAML."""
    global _PROTOTYPES_CACHE
    if _PROTOTYPES_CACHE is not None:
        return _PROTOTYPES_CACHE

    target_path = path or PROTOTYPES_PATH
    if not os.path.exists(target_path):
        logger.warning(f"Intent prototypes file not found at {target_path}")
        return {"advisory": [], "factual": []}

    try:
        with open(target_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
            _PROTOTYPES_CACHE = {
                "advisory": data.get("advisory", []),
                "factual": data.get("factual", []),
            }
            return _PROTOTYPES_CACHE
    except Exception as e:
        logger.error(f"Error loading intent prototypes: {e}")
        return {"advisory": [], "factual": []}


def get_centroids() -> Optional[Dict[str, np.ndarray]]:
    """Computes and caches normalized mean centroid vectors for each class."""
    global _CENTROIDS_CACHE
    if _CENTROIDS_CACHE is not None:
        return _CENTROIDS_CACHE

    try:
        from app.rag.retriever import get_embedder

        embedder = get_embedder()
        prototypes = load_prototypes()
        adv_list = prototypes.get("advisory", [])
        fac_list = prototypes.get("factual", [])

        if not adv_list or not fac_list:
            return None

        adv_vecs = embedder.encode(adv_list, normalize_embeddings=True)
        fac_vecs = embedder.encode(fac_list, normalize_embeddings=True)

        adv_centroid = np.mean(adv_vecs, axis=0)
        adv_centroid = adv_centroid / np.linalg.norm(adv_centroid)

        fac_centroid = np.mean(fac_vecs, axis=0)
        fac_centroid = fac_centroid / np.linalg.norm(fac_centroid)

        _CENTROIDS_CACHE = {
            "advisory": adv_centroid,
            "factual": fac_centroid,
        }
        return _CENTROIDS_CACHE
    except Exception as e:
        logger.warning(f"Could not compute prototype centroids: {e}")
        return None


def classify_clause_prototype(clause: str) -> Tuple[str, float, float]:
    """Classifies a clause against embedding prototype centroids.

    Returns:
        (category, advisory_sim, factual_sim)
        category is one of: "ADVISORY", "FACTUAL", "UNCERTAIN"
    """
    centroids = get_centroids()
    if not centroids:
        return ("UNCERTAIN", 0.0, 0.0)

    try:
        from app.rag.retriever import get_embedder

        embedder = get_embedder()
        clean = clause.strip()
        if not clean:
            return ("UNCERTAIN", 0.0, 0.0)

        vec = embedder.encode([clean], normalize_embeddings=True)[0]
        sim_adv = float(np.dot(vec, centroids["advisory"]))
        sim_fac = float(np.dot(vec, centroids["factual"]))

        # Fail closed towards advisory if advisory similarity is high or exceeds factual
        if sim_adv >= 0.25 and sim_adv > sim_fac:
            return ("ADVISORY", sim_adv, sim_fac)
        elif sim_fac >= 0.35 and sim_fac > sim_adv:
            return ("FACTUAL", sim_adv, sim_fac)
        elif sim_adv >= 0.22:
            # Uncertain with notable advisory lean -> fail-closed refusal
            return ("UNCERTAIN", sim_adv, sim_fac)
        else:
            return ("UNCERTAIN", sim_adv, sim_fac)
    except Exception as e:
        logger.warning(f"Prototype classification error: {e}")
        return ("UNCERTAIN", 0.0, 0.0)
