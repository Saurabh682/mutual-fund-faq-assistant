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
_VECTORS_CACHE: Optional[Dict[str, np.ndarray]] = None

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


def get_prototype_data() -> Optional[Tuple[Dict[str, np.ndarray], Dict[str, np.ndarray]]]:
    """Returns (centroids, vectors) for advisory and factual prototypes."""
    global _CENTROIDS_CACHE, _VECTORS_CACHE
    if _CENTROIDS_CACHE is not None and _VECTORS_CACHE is not None:
        return _CENTROIDS_CACHE, _VECTORS_CACHE

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
        _VECTORS_CACHE = {
            "advisory": adv_vecs,
            "factual": fac_vecs,
        }
        return _CENTROIDS_CACHE, _VECTORS_CACHE
    except Exception as e:
        logger.warning(f"Could not compute prototype data: {e}")
        return None


def get_centroids() -> Optional[Dict[str, np.ndarray]]:
    """Returns cached centroid vectors."""
    data = get_prototype_data()
    return data[0] if data else None


def classify_clause_prototype(clause: str) -> Tuple[str, float, float]:
    """Classifies a clause against embedding prototype vectors and centroids.

    Uses nearest-neighbor and centroid cosine similarity.
    Returns:
        (category, advisory_sim, factual_sim)
        category is one of: "ADVISORY", "FACTUAL", "UNCERTAIN"
    """
    data = get_prototype_data()
    if not data:
        return ("UNCERTAIN", 0.0, 0.0)

    centroids, vectors = data

    try:
        from app.rag.retriever import get_embedder

        embedder = get_embedder()
        clean = clause.strip()
        if not clean:
            return ("UNCERTAIN", 0.0, 0.0)

        vec = embedder.encode([clean], normalize_embeddings=True)[0]

        # Nearest-neighbor cosine similarities (max over individual prototypes)
        nn_adv = float(np.max(np.dot(vectors["advisory"], vec)))
        nn_fac = float(np.max(np.dot(vectors["factual"], vec)))

        # Centroid cosine similarities
        sim_adv = float(np.dot(vec, centroids["advisory"]))
        sim_fac = float(np.dot(vec, centroids["factual"]))

        effective_adv = max(nn_adv, sim_adv)
        effective_fac = max(nn_fac, sim_fac)

        # 0. Low-similarity fast path for out-of-corpus queries (neither advisory nor factual)
        if nn_adv < 0.50 and nn_fac < 0.50 and sim_adv < 0.35 and sim_fac < 0.35:
            return ("OUT_OF_CORPUS", effective_adv, effective_fac)

        # 1. High nearest-neighbor advisory match (>= 0.70) or NN advisory exceeds NN factual
        if nn_adv >= 0.70 or (nn_adv >= 0.55 and nn_adv > nn_fac):
            return ("ADVISORY", effective_adv, effective_fac)

        # 2. Strong factual match (NN factual exceeds NN advisory by clear margin)
        if nn_fac >= 0.70 and nn_fac > nn_adv:
            return ("FACTUAL", effective_adv, effective_fac)

        # 3. Centroid fallback with fail-closed advisory bias
        if sim_adv >= 0.35 and sim_adv > sim_fac:
            return ("ADVISORY", effective_adv, effective_fac)
        elif sim_fac >= 0.45 and sim_fac > sim_adv:
            return ("FACTUAL", effective_adv, effective_fac)
        elif effective_adv >= 0.30:
            return ("UNCERTAIN", effective_adv, effective_fac)
        else:
            return ("UNCERTAIN", effective_adv, effective_fac)
    except Exception as e:
        logger.warning(f"Prototype classification error: {e}")
        return ("UNCERTAIN", 0.0, 0.0)
