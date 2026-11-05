import os
import sys
import time
from typing import List

sys.path.insert(0, os.path.abspath("backend"))

import numpy as np
from app.rag.retriever import HybridRetriever
from app.rag.synthesizer import ConstrainedSynthesizer
from app.guardrails.intent import classify_intent
from app.guardrails.pii import scan_pii

def run_benchmark():
    print("=" * 70, flush=True)
    print("END-TO-END RAG & GROQ SYNTHESIS LATENCY PROFILING BENCHMARK", flush=True)
    print("=" * 70, flush=True)

    print("1. Initializing HybridRetriever and ConstrainedSynthesizer...", flush=True)
    t_start = time.perf_counter()
    retriever = HybridRetriever()
    synth = ConstrainedSynthesizer()
    init_ms = (time.perf_counter() - t_start) * 1000
    print(f"   [OK] Components initialized in {init_ms:.1f}ms\n", flush=True)

    # 30 real-world queries across 5 distinct query archetypes:
    # 1. Procedural redemption & platform instructions
    # 2. Regulatory KYC & documentation norms
    # 3. Tax, lock-in & statutory guidelines
    # 4. SIP mechanics, cut-offs & payment handling
    # 5. Plan switching & portfolio operations
    benchmark_queries = [
        # Procedural (Redemption & Portfolio)
        "How do I redeem mutual fund units on Groww?",
        "What are the steps to place a switch request between schemes?",
        "Where can I find the capital gains tax statement?",
        "How do I track my active SIPs and lump-sum holdings?",
        "Can I place a partial redemption for my mutual fund units?",
        "How long does it take for redemption money to reach my bank?",

        # Regulatory & KYC
        "What documents are needed for KYC verification?",
        "How do I update my registered email and mobile number with the RTA?",
        "Why is PAN mandatory for mutual fund investments under SEBI rules?",
        "What is the investor grievance escalation mechanism through SCORES?",
        "How do I verify if my mutual fund KYC is validated or registered?",
        "What is the role of CAMS and KFintech as RTAs?",

        # Tax, Lock-in & Categorization
        "What is the statutory lock-in period for ELSS tax saver schemes?",
        "How are equity mutual fund long term capital gains taxed?",
        "What are the STCG tax implications when redeeming before one year?",
        "What is the SEBI categorization rule for multi-cap equity funds?",
        "Explain the difference between Growth and IDCW options.",
        "What does Very High Risk on the SEBI riskometer signify?",

        # SIP Operations & Banking
        "How do I set up an autopay mandate for my monthly SIP?",
        "What happens if my bank account lacks sufficient balance on SIP date?",
        "What is the official NAV cut-off timing for same-day allotment?",
        "Can I pause my SIP temporarily without cancelling the mandate?",
        "What is the minimum additional investment amount for equity funds?",
        "How is the exit load calculated on SIP installments redeemed early?",

        # Scheme Mechanics & Disclosures
        "What is the difference between Direct plan and Regular plan?",
        "Where can an investor inspect the monthly portfolio disclosures?",
        "What constitutes the Total Expense Ratio of a direct mutual fund?",
        "How is the Net Asset Value computed by asset management companies?",
        "What is tracking error in exchange traded funds and index funds?",
        "Are mutual fund investments covered under deposit insurance?",
    ]

    e2e_latencies: List[float] = []
    llm_latencies: List[float] = []
    retrieval_latencies: List[float] = []

    print(f"Executing 30 end-to-end queries (PII Redaction -> Intent -> Retrieval -> LLM -> Validation)...\n", flush=True)

    for idx, query in enumerate(benchmark_queries, start=1):
        t_query_start = time.perf_counter()

        # Step 1: PII Guardrail
        has_pii, pii_types, clean_query = scan_pii(query)

        # Step 2: Intent Classification
        intent_res = classify_intent(clean_query)

        # Step 3: Hybrid Retrieval (Dense Vector + BM25)
        t_ret_start = time.perf_counter()
        ret_result = retriever.search(clean_query, top_k=3)
        ret_ms = (time.perf_counter() - t_ret_start) * 1000
        retrieval_latencies.append(ret_ms)

        # Step 4: Constrained LLM Synthesis
        t_llm_start = time.perf_counter()
        context_texts = [c.text for c in ret_result.chunks] if ret_result.chunks else ["Official mutual fund factual guidance."]
        synth_res = synth.synthesize(
            query=clean_query,
            context_chunks=context_texts,
            primary_url=ret_result.primary_citation_url or "https://www.amfiindia.com",
            doc_date=ret_result.primary_doc_date or "2026-11-05",
        )
        llm_ms = (time.perf_counter() - t_llm_start) * 1000
        llm_latencies.append(llm_ms)

        total_ms = (time.perf_counter() - t_query_start) * 1000
        e2e_latencies.append(total_ms)

        print(
            f"[{idx:02d}/30] Total: {total_ms:6.1f}ms | Ret: {ret_ms:4.1f}ms | LLM: {llm_ms:6.1f}ms | "
            f"Words: {len(synth_res.text.split()):2d} | Valid: {synth_res.is_valid}",
            flush=True,
        )
        time.sleep(0.12)  # Respect API rate limits

    e2e_np = np.array(e2e_latencies)
    llm_np = np.array(llm_latencies)
    ret_np = np.array(retrieval_latencies)

    print("\n" + "=" * 70, flush=True)
    print("BENCHMARK REPORT: 30 REAL-LLM END-TO-END QUERIES", flush=True)
    print("=" * 70, flush=True)
    print(f"{'Metric':<25} | {'End-to-End (RAG+LLM)':<20} | {'LLM Synthesis Only':<20}", flush=True)
    print("-" * 70, flush=True)
    print(f"{'p50 (Median)':<25} | {np.percentile(e2e_np, 50):8.1f} ms          | {np.percentile(llm_np, 50):8.1f} ms", flush=True)
    print(f"{'p95':<25} | {np.percentile(e2e_np, 95):8.1f} ms          | {np.percentile(llm_np, 95):8.1f} ms", flush=True)
    print(f"{'p99':<25} | {np.percentile(e2e_np, 99):8.1f} ms          | {np.percentile(llm_np, 99):8.1f} ms", flush=True)
    print(f"{'Mean':<25} | {np.mean(e2e_np):8.1f} ms          | {np.mean(llm_np):8.1f} ms", flush=True)
    print(f"{'Min':<25} | {np.min(e2e_np):8.1f} ms          | {np.min(llm_np):8.1f} ms", flush=True)
    print(f"{'Max':<25} | {np.max(e2e_np):8.1f} ms          | {np.max(llm_np):8.1f} ms", flush=True)
    print(f"{'Retrieval Avg (Dense+BM25)':<25} | {np.mean(ret_np):8.1f} ms          | -", flush=True)
    print("=" * 70, flush=True)

if __name__ == "__main__":
    run_benchmark()
