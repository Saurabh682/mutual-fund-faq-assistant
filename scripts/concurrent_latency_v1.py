"""Task 6: Unpaced Concurrency Latency Benchmark.

Executes 30 LLM-path queries with max_workers=5 (unpaced).
Measures n, p50, p95, max for:
- embedding
- retrieval
- Groq LLM synthesis
- validation
- total latency
Records counts of 429s from Groq, reached Groq count, and deadline fallbacks triggered.
"""

from __future__ import annotations

import concurrent.futures
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

import numpy as np

# Ensure backend app is in sys.path
BASE_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = BASE_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Suppress debug logs
logging.getLogger("app").setLevel(logging.INFO)

from app.api.rag import _retriever, _synthesizer
from app.guardrails.refusal import get_default_corpus_date
from app.guardrails.validator import validate_response
from app.rag.prompts import SYSTEM_SYNTHESIS_PROMPT, build_synthesis_user_prompt
from app.rag.retriever import encode_query, get_embedder

QUERIES_30 = [
    # 15 Procedural Queries (exercise hybrid retrieval + synthesis)
    "How do I complete KYC verification online for mutual funds?",
    "What are the steps to set up e-NACH autopay mandate on Groww?",
    "How can I pause an ongoing SIP installment for a few months?",
    "What documents are acceptable as proof of address for KYC?",
    "How do I update my registered bank account details?",
    "What is the cut-off time for same day NAV in equity mutual funds?",
    "How does the SEBI riskometer calculate scheme volatility?",
    "What is the procedure for redeeming mutual fund units?",
    "How to download the consolidated capital gains tax statement?",
    "What happens if an SIP installment bounces due to insufficient funds?",
    "What is the difference between direct plan and regular plan expense ratio?",
    "How are capital gains taxed on mutual fund investments after 2024?",
    "What is the settlement cycle for mutual fund redemptions in India?",
    "How do I track the order status of a mutual fund lump sum purchase?",
    "Can a minor invest in mutual funds with a guardian?",
    # 15 Out-of-Corpus Queries (reach retrieval / safe synthesis)
    "What is the expense ratio of Axis Bluechip Fund Direct Growth?",
    "Who is the current fund manager of ICICI Prudential Smallcap Fund?",
    "What is the latest NAV of SBI Small Cap Fund?",
    "Tell me the exit load of Mirae Asset Large Cap Fund.",
    "What is the AUM of Nippon India Growth Fund?",
    "Does Kotak Emerging Equity Fund have a lock-in period?",
    "What is the portfolio turnover of Parag Parikh Flexi Cap Fund?",
    "Who manages the DSP Midcap Fund currently?",
    "What benchmark index does UTI Nifty 50 Index Fund follow?",
    "What is the minimum SIP installment for Tata Digital India Fund?",
    "How to invest in international gold ETFs through Motilal Oswal?",
    "What is the riskometer rating of Canara Robeco Bluechip Equity?",
    "What is the direct expense ratio of Franklin India Smaller Companies?",
    "How to switch units from Axis Long Term Equity to Axis Bluechip?",
    "What is the dividend distribution history of Quant Active Fund?",
]


def run_single_query(query: str, worker_id: int) -> Dict[str, Any]:
    t_start = time.perf_counter()

    groq_429_count = 0
    deadline_fallback_count = 0
    reached_groq = False
    groq_success = False

    # 1. Embedding timing (serialized encode prevents OpenMP CPU thrashing)
    t_emb_0 = time.perf_counter()
    _ = encode_query(query, normalize_embeddings=True)
    t_emb = (time.perf_counter() - t_emb_0) * 1000

    # 2. Retrieval timing (Dense + BM25 + RRF)
    t_ret_0 = time.perf_counter()
    retrieval_res = _retriever.search(query=query, scheme_id=None, top_k=4)
    t_ret = (time.perf_counter() - t_ret_0) * 1000

    # 3. Groq Timing
    t_groq_0 = time.perf_counter()
    context_texts = [c.text for c in retrieval_res.chunks]
    raw_draft = ""
    is_fallback = False

    try:
        reached_groq = True
        user_prompt = build_synthesis_user_prompt(query, context_texts)
        raw_draft = _synthesizer._call_llm(SYSTEM_SYNTHESIS_PROMPT, user_prompt, deadline_t=time.perf_counter() + 1.8)
        groq_success = True
    except Exception as e:
        err_msg = str(e).lower()
        if "429" in err_msg:
            groq_429_count += 1
        if "timeout" in err_msg or "deadline" in err_msg:
            deadline_fallback_count += 1
        is_fallback = True
        raw_draft = "NOT_FOUND"

    t_groq = (time.perf_counter() - t_groq_0) * 1000

    # 4. Validation timing
    t_val_0 = time.perf_counter()
    citation_url = retrieval_res.primary_citation_url
    doc_date = get_default_corpus_date()
    val_res = validate_response(raw_draft, context_texts, primary_url=citation_url, doc_date=doc_date)
    t_val = (time.perf_counter() - t_val_0) * 1000

    t_total = (time.perf_counter() - t_start) * 1000

    return {
        "query": query,
        "worker_id": worker_id,
        "embedding_ms": t_emb,
        "retrieval_ms": t_ret,
        "groq_ms": t_groq,
        "validation_ms": t_val,
        "total_ms": t_total,
        "reached_groq": reached_groq,
        "groq_success": groq_success,
        "groq_429": groq_429_count,
        "deadline_fallback": deadline_fallback_count,
        "is_fallback": is_fallback,
        "is_valid": val_res.is_valid,
    }


def compute_stats(values: List[float]) -> Dict[str, float]:
    arr = np.array(values)
    return {
        "n": len(arr),
        "p50": float(np.percentile(arr, 50)),
        "p95": float(np.percentile(arr, 95)),
        "max": float(np.max(arr)),
    }


def main():
    print(f"Pre-warming embedding model and prototype cache on main thread...")
    t_warm_0 = time.perf_counter()
    get_embedder()
    from app.guardrails.intent_prototype import get_prototype_data
    get_prototype_data()
    print(f"Warmup complete in {(time.perf_counter() - t_warm_0)*1000:.1f}ms")

    print(f"\nStarting unpaced concurrency latency run on {len(QUERIES_30)} queries with max_workers=5...")
    wall_t0 = time.perf_counter()

    results: List[Dict[str, Any]] = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            executor.submit(run_single_query, q, idx % 5): q
            for idx, q in enumerate(QUERIES_30)
        }
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            results.append(res)
            print(f"  [{len(results):02d}/30] total: {res['total_ms']:.1f}ms | emb: {res['embedding_ms']:.1f}ms | groq: {res['groq_ms']:.1f}ms | 429: {res['groq_429']} | fallback: {res['deadline_fallback']}")

    wall_elapsed = time.perf_counter() - wall_t0

    # Aggregate stats
    emb_stats = compute_stats([r["embedding_ms"] for r in results])
    ret_stats = compute_stats([r["retrieval_ms"] for r in results])
    groq_stats = compute_stats([r["groq_ms"] for r in results])
    val_stats = compute_stats([r["validation_ms"] for r in results])
    total_stats = compute_stats([r["total_ms"] for r in results])

    total_reached_groq = sum(1 for r in results if r["reached_groq"])
    total_groq_success = sum(1 for r in results if r["groq_success"])
    total_429s = sum(r["groq_429"] for r in results)
    total_deadlines = sum(r["deadline_fallback"] for r in results)

    report = {
        "concurrency": 5,
        "query_count": len(results),
        "wall_time_sec": round(wall_elapsed, 2),
        "reached_groq_count": total_reached_groq,
        "groq_success_count": total_groq_success,
        "groq_429_count": total_429s,
        "deadline_fallback_count": total_deadlines,
        "embedding": emb_stats,
        "retrieval": ret_stats,
        "groq": groq_stats,
        "validation": val_stats,
        "total": total_stats,
    }

    out_file = BASE_DIR / "eval" / "reports" / "concurrent_latency_v1.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("\n" + "=" * 60)
    print("UNPACED CONCURRENCY LATENCY BENCHMARK RESULTS (max_workers=5)")
    print("=" * 60)
    print(f"Total Queries (n):          {len(results)}")
    print(f"Wall-clock Time:            {wall_elapsed:.2f} s")
    print(f"Queries Reached Groq:       {total_reached_groq} / {len(results)}")
    print(f"Groq Synthesis Successes:   {total_groq_success} / {len(results)}")
    print(f"Total Groq 429 Count:       {total_429s}")
    print(f"Deadline Fallbacks Used:    {total_deadlines}")
    print("-" * 60)
    print(f"{'Metric':<14} | {'n':<4} | {'p50 (ms)':<9} | {'p95 (ms)':<9} | {'max (ms)':<9}")
    print("-" * 60)
    for name, s in [
        ("embedding", emb_stats),
        ("retrieval", ret_stats),
        ("Groq", groq_stats),
        ("validation", val_stats),
        ("total", total_stats),
    ]:
        print(f"{name:<14} | {s['n']:<4} | {s['p50']:<9.1f} | {s['p95']:<9.1f} | {s['max']:<9.1f}")
    print("=" * 60)


if __name__ == "__main__":
    main()
