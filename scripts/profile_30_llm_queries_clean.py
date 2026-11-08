import os
import sys
import time
import statistics
from typing import List, Dict, Any

sys.path.insert(0, os.path.abspath("backend"))

from app.core.config import settings
from app.rag.retriever import HybridRetriever, get_embedder
from app.rag.entities import resolve_entities
from app.rag.prompts import SYSTEM_SYNTHESIS_PROMPT, build_synthesis_user_prompt
from app.rag.synthesizer import ConstrainedSynthesizer
from app.guardrails.validator import validate_response

queries = [
    "What is the investment objective of HDFC Top 100 Fund?",
    "What sectors does HDFC Mid-Cap Opportunities Fund invest in?",
    "What are the major holdings of HDFC Small Cap Fund?",
    "What is the asset allocation strategy of HDFC Multi Cap Fund?",
    "How does HDFC Silver ETF FoF invest in physical silver or ETF units?",
    "What is the minimum additional investment for HDFC Top 100 Fund?",
    "What is the benchmark of HDFC Mid-Cap Opportunities Fund?",
    "What are the key risks associated with HDFC Small Cap Fund?",
    "Does HDFC Multi Cap Fund maintain minimum 25% allocation in large, mid, and small cap?",
    "What is the fund house philosophy for HDFC Top 100?",
    "What are the top 5 stock holdings of HDFC Top 100 Fund?",
    "What are the exit load terms for HDFC Small Cap Fund?",
    "What is the portfolio turnover disclosed in HDFC Top 100 factsheet?",
    "What are the redemption settlement cycles for HDFC Mid-Cap Opportunities Fund?",
    "What is the statutory lock-in period for ELSS compared to HDFC Top 100?",
    "What is the expense ratio breakdown for HDFC Small Cap Direct Plan?",
    "What is the taxation on long term capital gains for HDFC Multi Cap Fund?",
    "How is NAV calculated daily for HDFC Silver ETF FoF?",
    "What is the minimum lumpsum investment amount for HDFC Mid-Cap Opportunities?",
    "What index does HDFC Small Cap Fund track as its benchmark?",
    "What is the role of lead fund manager in HDFC Top 100 Fund?",
    "What are the banking and financial sector weights in HDFC Top 100?",
    "What is the mandate for small cap stock selection in HDFC Small Cap Fund?",
    "How does HDFC Multi Cap rebalance between market capitalizations?",
    "What are the custodian and registrar details for HDFC Silver ETF FoF?",
    "What are the cut-off timings for same-day NAV in HDFC Top 100 Fund?",
    "What documents are required for physical redemption of HDFC Mid Cap units?",
    "How does dividend distribution or IDCW work in HDFC Small Cap Fund?",
    "What are the portfolio disclosure frequencies for HDFC Multi Cap Fund?",
    "What is the commodity exposure in HDFC Silver ETF FoF?",
]

def profile():
    retriever = HybridRetriever()
    embedder = get_embedder()
    synthesizer = ConstrainedSynthesizer()

    records: List[Dict[str, float]] = []

    print(f"Profiling {len(queries)} LLM-path queries with pacing to respect TPM limit...")
    print(f"Model: {settings.GROQ_MODEL} (timeout=1.8s, max_retries=0)\n", flush=True)

    for idx, q in enumerate(queries, 1):
        t_total_start = time.perf_counter()

        # Stage 1: Embedding
        t_emb_start = time.perf_counter()
        q_emb = embedder.encode([q.strip()]).tolist()
        t_emb_ms = (time.perf_counter() - t_emb_start) * 1000

        # Stage 2: Retrieval (ChromaDB + BM25 + RRF)
        t_ret_start = time.perf_counter()
        ent = resolve_entities(q)
        ret_res = retriever.search(q, scheme_id=ent.scheme_id, top_k=4)
        t_ret_ms = (time.perf_counter() - t_ret_start) * 1000

        # Prepare context
        context_texts = [c.text for c in ret_res.chunks]
        if not context_texts:
            context_texts = ["HDFC Mutual Fund verified facts and scheme information."]

        # Stage 3: Groq LLM Call with retry on rate limit
        user_prompt = build_synthesis_user_prompt(q, context_texts)
        raw_draft = ""
        groq_status = "OK"
        
        # If rate limited, sleep and retry up to 2 times to ensure we get a clean real LLM latency
        for attempt in range(3):
            t_groq_start = time.perf_counter()
            try:
                raw_draft = synthesizer._call_llm(SYSTEM_SYNTHESIS_PROMPT, user_prompt)
                t_groq_ms = (time.perf_counter() - t_groq_start) * 1000
                groq_status = "OK"
                break
            except Exception as e:
                t_groq_ms = (time.perf_counter() - t_groq_start) * 1000
                if "rate_limit" in str(e).lower() and attempt < 2:
                    time.sleep(3.0)
                    continue
                groq_status = f"ERROR ({type(e).__name__})"
                break

        # Validation
        val_res = validate_response(
            raw_draft if raw_draft else "NOT_FOUND",
            context_chunks=context_texts,
            primary_url=ret_res.primary_citation_url,
            doc_date="2026-11-05",
        )

        t_total_ms = (time.perf_counter() - t_total_start) * 1000

        rec = {
            "query": q,
            "embedding_ms": t_emb_ms,
            "retrieval_ms": t_ret_ms,
            "groq_ms": t_groq_ms,
            "total_ms": t_total_ms,
            "groq_status": groq_status,
            "valid": val_res.is_valid,
        }
        records.append(rec)

        print(f"[{idx:02d}/30] Emb: {t_emb_ms:5.1f}ms | Ret: {t_ret_ms:5.1f}ms | Groq: {t_groq_ms:6.1f}ms | Total: {t_total_ms:6.1f}ms | Status: {groq_status}", flush=True)

        # Pace calls to respect 8000 TPM
        time.sleep(3.0)

    def p50(vals):
        return statistics.median(vals)

    def p95(vals):
        sorted_vals = sorted(vals)
        k = int(len(sorted_vals) * 0.95)
        return sorted_vals[min(k, len(sorted_vals) - 1)]

    # Filter to OK queries for accurate LLM generation timings
    ok_records = [r for r in records if r["groq_status"] == "OK"]
    print(f"\nSuccessful LLM generations: {len(ok_records)}/{len(records)}")

    emb_vals = [r["embedding_ms"] for r in records]
    ret_vals = [r["retrieval_ms"] for r in records]
    groq_vals = [r["groq_ms"] for r in ok_records] if ok_records else [r["groq_ms"] for r in records]
    tot_vals = [r["total_ms"] for r in ok_records] if ok_records else [r["total_ms"] for r in records]

    print("\n" + "=" * 70)
    print("30-QUERY REAL-LLM STAGE-BY-STAGE LATENCY PROFILE")
    print("=" * 70)
    print(f"{'Stage':<16} | {'n':<4} | {'p50 (ms)':<10} | {'p95 (ms)':<10} | {'max (ms)':<10}")
    print("-" * 70)
    print(f"{'Embedding':<16} | {len(records):<4} | {p50(emb_vals):<10.1f} | {p95(emb_vals):<10.1f} | {max(emb_vals):<10.1f}")
    print(f"{'Retrieval':<16} | {len(records):<4} | {p50(ret_vals):<10.1f} | {p95(ret_vals):<10.1f} | {max(ret_vals):<10.1f}")
    print(f"{'Groq (LLM)':<16} | {len(groq_vals):<4} | {p50(groq_vals):<10.1f} | {p95(groq_vals):<10.1f} | {max(groq_vals):<10.1f}")
    print(f"{'Total Turn':<16} | {len(tot_vals):<4} | {p50(tot_vals):<10.1f} | {p95(tot_vals):<10.1f} | {max(tot_vals):<10.1f}")
    print("=" * 70, flush=True)

if __name__ == "__main__":
    profile()
