"""Dual-Head Intent Classifier: Information Request vs Decision Request.

Distinguishes objective factual inquiries (TER, NAV, procedures, definitions, rules)
from subjective/advisory decision requests (fund selection, rankings, outperformance,
allocations, market timing, suitability).

Fails closed to DECISION_REQUEST whenever the similarity margin between decision
and information is small (margin < 0.05).
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import yaml

logger = logging.getLogger(__name__)

PROTOTYPES_PATH = Path(__file__).resolve().parents[3] / "data" / "intent_head_prototypes.yaml"

_CACHE: Optional[Dict[str, Any]] = None


def load_head_prototypes(path: Optional[Path] = None) -> Dict[str, Dict[str, List[str]]]:
    """Loads train and dev prototypes for decision_request and information_request."""
    target_path = path or PROTOTYPES_PATH
    if not os.path.exists(target_path):
        logger.warning(f"Intent head prototypes file not found at {target_path}")
        return {
            "decision_request": {"train": [], "dev": []},
            "information_request": {"train": [], "dev": []},
        }

    with open(target_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
        return {
            "decision_request": {
                "train": data.get("decision_request", {}).get("train", []),
                "dev": data.get("decision_request", {}).get("dev", []),
            },
            "information_request": {
                "train": data.get("information_request", {}).get("train", []),
                "dev": data.get("information_request", {}).get("dev", []),
            },
        }


def get_head_vectors() -> Optional[Dict[str, Any]]:
    """Encodes training prototypes and caches normalized vectors and centroids."""
    global _CACHE
    if _CACHE is not None:
        return _CACHE

    try:
        from app.rag.retriever import encode_query

        data = load_head_prototypes()
        dec_train = data["decision_request"]["train"]
        info_train = data["information_request"]["train"]

        if not dec_train or not info_train:
            return None

        dec_vecs = encode_query(dec_train, normalize_embeddings=True)
        info_vecs = encode_query(info_train, normalize_embeddings=True)

        dec_centroid = np.mean(dec_vecs, axis=0)
        dec_centroid = dec_centroid / np.linalg.norm(dec_centroid)

        info_centroid = np.mean(info_vecs, axis=0)
        info_centroid = info_centroid / np.linalg.norm(info_centroid)

        _CACHE = {
            "decision_vecs": dec_vecs,
            "info_vecs": info_vecs,
            "decision_centroid": dec_centroid,
            "info_centroid": info_centroid,
            "data": data,
        }
        return _CACHE
    except Exception as e:
        logger.error(f"Error computing intent head vectors: {e}")
        return None


def classify_intent_head(query: str, margin_threshold: float = 0.05) -> Tuple[str, float, float]:
    """Classifies a query or clause into DECISION_REQUEST or INFORMATION_REQUEST.

    Uses maximum nearest-neighbor cosine similarity combined with centroid cosine similarity.
    Fails closed: if decision similarity is within margin_threshold of information similarity,
    it classifies as DECISION_REQUEST to strictly prevent advisory leakage.

    Returns:
        (classification, score_decision, score_info)
    """
    clean = query.strip()
    if not clean:
        return ("INFORMATION_REQUEST", 0.0, 0.0)

    cache = get_head_vectors()
    if not cache:
        return ("INFORMATION_REQUEST", 0.0, 0.0)

    try:
        from app.rag.retriever import encode_query

        q_vec = encode_query(clean, normalize_embeddings=True)

        # Nearest neighbor similarities
        nn_dec = float(np.max(np.dot(cache["decision_vecs"], q_vec)))
        nn_info = float(np.max(np.dot(cache["info_vecs"], q_vec)))

        # Centroid similarities
        c_dec = float(np.dot(q_vec, cache["decision_centroid"]))
        c_info = float(np.dot(q_vec, cache["info_centroid"]))

        effective_dec = max(nn_dec, c_dec)
        effective_info = max(nn_info, c_info)

        # Out-of-corpus check: if both decision and info similarity are low, query is out of corpus
        if effective_dec < 0.35 and effective_info < 0.35:
            return ('OUT_OF_CORPUS', effective_dec, effective_info)

        # Fail-closed rule: if decision score >= info score - margin, treat as decision request
        if effective_dec >= (effective_info - margin_threshold):
            return ("DECISION_REQUEST", effective_dec, effective_info)
        else:
            return ("INFORMATION_REQUEST", effective_dec, effective_info)
    except Exception as e:
        logger.warning(f"Error during intent head classification: {e}")
        return ("INFORMATION_REQUEST", 0.0, 0.0)


def evaluate_head_dev_set() -> Dict[str, Any]:
    """Evaluates accuracy on the held-out dev prototypes."""
    data = load_head_prototypes()
    dec_dev = data["decision_request"]["dev"]
    info_dev = data["information_request"]["dev"]

    correct_dec = 0
    for q in dec_dev:
        label, _, _ = classify_intent_head(q)
        if label == "DECISION_REQUEST":
            correct_dec += 1

    correct_info = 0
    for q in info_dev:
        label, _, _ = classify_intent_head(q)
        if label == "INFORMATION_REQUEST":
            correct_info += 1

    total_dev = len(dec_dev) + len(info_dev)
    total_correct = correct_dec + correct_info
    accuracy = (total_correct / total_dev) if total_dev > 0 else 0.0

    return {
        "dev_accuracy": accuracy,
        "total_dev": total_dev,
        "correct_decision": correct_dec,
        "total_decision": len(dec_dev),
        "correct_info": correct_info,
        "total_info": len(info_dev),
    }
