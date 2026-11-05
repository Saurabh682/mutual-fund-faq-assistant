import os
import sys
import time

sys.path.insert(0, os.path.abspath("backend"))

import numpy as np
from app.rag.synthesizer import ConstrainedSynthesizer

def main():
    print("Initializing ConstrainedSynthesizer...", flush=True)
    t_init = time.perf_counter()
    synth = ConstrainedSynthesizer()
    init_time_ms = (time.perf_counter() - t_init) * 1000
    print(f"Synthesizer initialization took: {init_time_ms:.1f}ms\n", flush=True)

    sample_queries = [
        "How do I redeem my mutual fund units on Groww?",
        "What documents are required for KYC verification?",
        "How to download capital gains statement on Groww?",
        "How do I start a Systematic Investment Plan?",
        "What is the cutoff timing for mutual fund redemption?",
        "How is exit load calculated when redeeming units?",
        "Can I change my SIP bank account on Groww?",
        "What happens when a SIP payment fails?",
        "What is the lock-in period for ELSS mutual funds?",
        "How do I switch from Regular plan to Direct plan?",
    ] * 3  # 30 queries

    context = [
        "Redemption can be placed via the Dashboard under Investments. Select the fund and enter units.",
        "Proceeds will be credited to the primary registered bank account within T+2 business days.",
        "KYC requires PAN card, Aadhaar linked to mobile number, and recent bank account proof.",
        "Capital Gains statement can be downloaded from Profile -> Reports -> Capital Gains.",
    ]

    latencies = []
    print(f"Executing 30 real-LLM Groq synthesis calls...", flush=True)
    for i, q in enumerate(sample_queries, start=1):
        t0 = time.perf_counter()
        res = synth.synthesize(
            query=q,
            context_chunks=context,
            primary_url="https://groww.in/mutual-funds",
            doc_date="2026-10-25",
        )
        elapsed = (time.perf_counter() - t0) * 1000
        latencies.append(elapsed)
        print(f"[{i:02d}/30] Latency: {elapsed:.1f}ms | Length: {len(res.text.split())} words | Valid: {res.is_valid}", flush=True)
        time.sleep(0.15)  # Respect rate limits

    latencies_np = np.array(latencies)
    p50 = np.percentile(latencies_np, 50)
    p95 = np.percentile(latencies_np, 95)
    p99 = np.percentile(latencies_np, 99)
    print("\n================= GROQ REAL-LLM PROFILING REPORT =================", flush=True)
    print(f"Total Successful Queries: {len(latencies_np)} / 30", flush=True)
    print(f"p50 (Median Latency):      {p50:.1f} ms", flush=True)
    print(f"p95 Latency:              {p95:.1f} ms", flush=True)
    print(f"p99 Latency:              {p99:.1f} ms", flush=True)
    print(f"Min Latency:              {np.min(latencies_np):.1f} ms", flush=True)
    print(f"Max Latency:              {np.max(latencies_np):.1f} ms", flush=True)
    print(f"Mean Latency:             {np.mean(latencies_np):.1f} ms", flush=True)
    print(f"Std Dev:                  {np.std(latencies_np):.1f} ms", flush=True)
    print("==================================================================", flush=True)

if __name__ == "__main__":
    main()
