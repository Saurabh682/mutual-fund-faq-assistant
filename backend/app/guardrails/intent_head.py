"""Dual/Triple-Head Intent Classifier: Information Request vs Unsupported Information vs Decision Request.

Distinguishes:
1. DECISION_REQUEST: Prohibited advisory, comparisons, recommendations, outperformance, market timing, suitability.
2. INFORMATION_REQUEST: In-scope factual and procedural inquiries (TER, NAV, exit load, min SIP/lumpsum, AUM, manager, benchmark, riskometer, procedures, definitions).
3. UNSUPPORTED_INFORMATION: Objective factual queries about mutual funds that the assistant cannot answer from its indexed records (CAGR/historical returns, sector allocations, holding stock counts, standard deviation/beta, cheque clearing time, company founding history).

Fails closed to DECISION_REQUEST whenever the similarity margin between decision
and information/unsupported is small (margin < 0.05).
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
    """Loads train and dev prototypes for decision_request, information_request, and unsupported_information."""
    target_path = path or PROTOTYPES_PATH
    if not os.path.exists(target_path):
        logger.warning(f"Intent head prototypes file not found at {target_path}")
        return {
            "decision_request": {"train": [], "dev": []},
            "information_request": {"train": [], "dev": []},
            "unsupported_information": {"train": [], "dev": []},
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
            "unsupported_information": {
                "train": data.get("unsupported_information", {}).get("train", []),
                "dev": data.get("unsupported_information", {}).get("dev", []),
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
        unsup_train = data["unsupported_information"]["train"]

        if not dec_train or not info_train:
            return None

        dec_vecs = encode_query(dec_train, normalize_embeddings=True)
        info_vecs = encode_query(info_train, normalize_embeddings=True)

        dec_centroid = np.mean(dec_vecs, axis=0)
        dec_centroid = dec_centroid / np.linalg.norm(dec_centroid)

        info_centroid = np.mean(info_vecs, axis=0)
        info_centroid = info_centroid / np.linalg.norm(info_centroid)

        unsup_vecs = None
        unsup_centroid = None
        if unsup_train:
            unsup_vecs = encode_query(unsup_train, normalize_embeddings=True)
            unsup_centroid = np.mean(unsup_vecs, axis=0)
            unsup_centroid = unsup_centroid / np.linalg.norm(unsup_centroid)

        _CACHE = {
            "decision_vecs": dec_vecs,
            "info_vecs": info_vecs,
            "decision_centroid": dec_centroid,
            "info_centroid": info_centroid,
            "unsup_vecs": unsup_vecs,
            "unsup_centroid": unsup_centroid,
            "data": data,
        }
        return _CACHE
    except Exception as e:
        logger.error(f"Error computing intent head vectors: {e}")
        return None


def classify_intent_head(query: str, margin_threshold: float = 0.05) -> Tuple[str, float, float, float]:
    """Classifies a query or clause into DECISION_REQUEST, INFORMATION_REQUEST, or UNSUPPORTED_INFORMATION.

    Uses maximum nearest-neighbor cosine similarity combined with centroid cosine similarity.
    Fails closed: if decision similarity is within margin_threshold of the highest information/unsupported
    similarity, it classifies as DECISION_REQUEST to strictly prevent advisory leakage.

    Returns:
        (classification, score_decision, score_info, score_unsupported)
    """
    clean = query.strip()
    if not clean:
        return ("INFORMATION_REQUEST", 0.0, 0.0, 0.0)

    cache = get_head_vectors()
    if not cache:
        return ("INFORMATION_REQUEST", 0.0, 0.0, 0.0)

    try:
        from app.rag.retriever import encode_query

        q_vec = encode_query(clean, normalize_embeddings=True)

        # Decision similarities
        nn_dec = float(np.max(np.dot(cache["decision_vecs"], q_vec)))
        c_dec = float(np.dot(q_vec, cache["decision_centroid"]))
        effective_dec = max(nn_dec, c_dec)

        # Info similarities
        nn_info = float(np.max(np.dot(cache["info_vecs"], q_vec)))
        c_info = float(np.dot(q_vec, cache["info_centroid"]))
        effective_info = max(nn_info, c_info)

        # Unsupported similarities
        effective_unsup = 0.0
        if cache.get("unsup_vecs") is not None and cache.get("unsup_centroid") is not None:
            nn_unsup = float(np.max(np.dot(cache["unsup_vecs"], q_vec)))
            c_unsup = float(np.dot(q_vec, cache["unsup_centroid"]))
            effective_unsup = max(nn_unsup, c_unsup)

        # Out-of-corpus check: if all scores are low (< 0.35), query is out of domain
        max_score = max(effective_dec, effective_info, effective_unsup)
        if max_score < 0.35:
            return ("OUT_OF_CORPUS", effective_dec, effective_info, effective_unsup)

        # Fail-closed rule: if decision score >= max(info, unsup) - margin, treat as decision request
        max_non_dec = max(effective_info, effective_unsup)
        if effective_dec >= (max_non_dec - margin_threshold):
            return ("DECISION_REQUEST", effective_dec, effective_info, effective_unsup)

        if effective_unsup > effective_info:
            return ("UNSUPPORTED_INFORMATION", effective_dec, effective_info, effective_unsup)
        else:
            return ("INFORMATION_REQUEST", effective_dec, effective_info, effective_unsup)
    except Exception as e:
        logger.warning(f"Error during intent head classification: {e}")
        return ("INFORMATION_REQUEST", 0.0, 0.0, 0.0)


def evaluate_head_dev_set() -> Dict[str, Any]:
    """Evaluates accuracy on the held-out dev prototypes."""
    data = load_head_prototypes()
    dec_dev = data["decision_request"]["dev"]
    info_dev = data["information_request"]["dev"]
    unsup_dev = data.get("unsupported_information", {}).get("dev", [])

    total = len(dec_dev) + len(info_dev) + len(unsup_dev)
    correct = 0

    classes = ["DECISION_REQUEST", "INFORMATION_REQUEST", "UNSUPPORTED_INFORMATION"]
    conf_matrix = {c_true: {c_pred: 0 for c_pred in classes + ["OUT_OF_CORPUS"]} for c_true in classes}

    for q in dec_dev:
        cls, sd, si, su = classify_intent_head(q)
        conf_matrix["DECISION_REQUEST"][cls] += 1
        if cls == "DECISION_REQUEST":
            correct += 1

    for q in info_dev:
        cls, sd, si, su = classify_intent_head(q)
        conf_matrix["INFORMATION_REQUEST"][cls] += 1
        if cls == "INFORMATION_REQUEST":
            correct += 1

    for q in unsup_dev:
        cls, sd, si, su = classify_intent_head(q)
        conf_matrix["UNSUPPORTED_INFORMATION"][cls] += 1
        if cls == "UNSUPPORTED_INFORMATION":
            correct += 1

    acc = correct / total if total > 0 else 0.0
    return {
        "total": total,
        "correct": correct,
        "accuracy": acc,
        "confusion_matrix": conf_matrix,
    }
