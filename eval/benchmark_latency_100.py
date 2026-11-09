"""100 Mixed Requests Latency Profiler for Mutual Fund FAQ Assistant.

Measures:
1. Model loading time.
2. Latency percentiles (p50 and p95) across:
   - Refusal path (35 queries)
   - Fact lookup path (35 queries)
   - LLM synthesis path (30 queries)
"""

import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Any

REPO_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_DIR / "backend"))

import numpy as np
from fastapi.testclient import TestClient
from app.main import app, _IP_REQUEST_TIMESTAMPS

REFUSAL_QUERIES = [
    "Should I invest in HDFC Mid Cap?",
    "Should I buy HDFC Small Cap Fund?",
    "Which is better: HDFC Mid Cap or HDFC Top 100?",
    "What is the best fund for retirement?",
    "Is it safe to buy HDFC Top 100 Fund?",
    "Where should I invest my money?",
    "Can you recommend a mutual fund scheme?",
    "Would a conservative investor prefer HDFC Mid-Cap?",
    "HDFC Small Cap vs HDFC Mid Cap",
    "Compare HDFC Top 100 and HDFC Multi Cap",
    "Which fund gives higher return than HDFC Silver ETF?",
    "Rank these mutual funds for me",
    "Which scheme has better performance?",
    "Give me financial advice on investing",
    "Help me pick a fund for wealth creation",
    "Is this a good time to enter HDFC Small Cap?",
    "Should I redeem or hold HDFC Multi Cap Fund?",
    "Suggest me a high return scheme",
    "Which mutual fund option is best for a student?",
    "If you had 50000 rupees which fund would you choose?",
    "Should I invest in HDFC Top 100?",
    "Can you advise me on fund selection?",
    "Is HDFC Small Cap good for aggressive growth?",
    "Which scheme should I buy today?",
    "Should I sell HDFC Mid Cap right now?",
    "Where should I put 1 lakh rupees?",
    "Recommend a good fund for 5 years.",
    "Should I invest in growth or IDCW?",
    "Is it safe to invest in equity right now?",
    "Can you give me investment advice?",
    "Which fund is best for capital protection?",
    "Should I invest in HDFC Silver ETF FoF?",
    "Which fund will give highest returns?",
    "Help me choose between small cap and mid cap.",
    "Give me financial recommendations.",
]

FACT_LOOKUP_QUERIES = [
    "What is the expense ratio of HDFC Small Cap Fund?",
    "What is the NAV of HDFC Mid-Cap Opportunities Fund?",
    "What is the exit load for HDFC Top 100 Fund?",
    "What is the minimum SIP amount for HDFC Multi Cap Fund?",
    "What is the total AUM of HDFC Small Cap Fund?",
    "Who is the fund manager of HDFC Mid-Cap Opportunities Fund?",
    "What is the benchmark of HDFC Top 100 Fund?",
    "What is the riskometer rating for HDFC Silver ETF FoF?",
    "What is the lock-in period for HDFC Mid-Cap Opportunities Fund?",
    "What is the minimum lumpsum investment for HDFC Small Cap?",
    "Tell me the TER of HDFC Top 100 Direct Growth.",
    "What is the exit load for HDFC Small Cap Fund if redeemed within 1 year?",
    "Who manages HDFC Top 100 Fund?",
    "What is the AUM of HDFC Mid-Cap Opportunities Fund?",
    "What is the benchmark index for HDFC Multi Cap Fund?",
    "What is the latest NAV of HDFC Silver ETF FoF?",
    "What is the minimum SIP for HDFC Small Cap Direct Growth?",
    "Does HDFC Top 100 Fund have any lock-in duration?",
    "What is the expense ratio for HDFC Silver ETF FoF?",
    "Who is managing HDFC Multi Cap Fund?",
    "What is the risk rating on the riskometer for HDFC Mid Cap?",
    "What is the exit load for HDFC Silver ETF FoF?",
    "What is the minimum additional investment for HDFC Top 100?",
    "What is the TER of HDFC Multi Cap Direct Growth?",
    "What is the AUM for HDFC Top 100 Fund?",
    "What is the benchmark for HDFC Small Cap Fund?",
    "What is the NAV of HDFC Top 100 Fund?",
    "Who manages HDFC Silver ETF FoF?",
    "What is the exit load of HDFC Multi Cap Fund?",
    "What is the lock-in for HDFC Small Cap Fund?",
    "What is the AUM of HDFC Silver ETF FoF?",
    "What is the expense ratio of HDFC Mid-Cap Opportunities Fund?",
    "What is the riskometer category for HDFC Top 100 Fund?",
    "What is the minimum SIP for HDFC Mid-Cap Opportunities?",
    "What is the NAV of HDFC Multi Cap Fund?",
]

LLM_SYNTHESIS_QUERIES = [
    "What is the step by step process to redeem mutual fund units on Groww?",
    "How does an investor switch between mutual fund schemes?",
    "What documents are required to complete mutual fund KYC verification?",
    "What happens if an investor misses a monthly SIP installment due to low balance?",
    "How is capital gains tax calculated for equity mutual fund redemptions?",
    "What is the statutory lock-in period for ELSS mutual funds under Indian tax law?",
    "Explain the difference between Direct plans and Regular plans.",
    "What is the cutoff timing for same-day NAV allotment in equity schemes?",
    "How do I set up an autopay e-mandate for mutual fund SIP payments?",
    "What is the role of RTAs like CAMS and KFintech in mutual fund servicing?",
    "How can an investor update bank account details registered with a mutual fund?",
    "Explain the meaning of Very High Risk on the SEBI mutual fund riskometer.",
    "What is the grievance redressal mechanism for mutual fund investors via SCORES?",
    "Can an investor make a partial redemption of mutual fund units?",
    "How long does it take for redemption proceeds to credit into a bank account?",
    "What is the difference between Growth and IDCW options in mutual funds?",
    "Why is PAN mandatory for all mutual fund investments in India?",
    "What is the procedure for transmission of mutual fund units upon death of unit holder?",
    "How do equity fund cut-off timings work for purchases above two lakh rupees?",
    "What is the SEBI mandate regarding portfolio disclosure frequency for mutual funds?",
    "How can an investor download annual capital gains statement for income tax filing?",
    "What is the process to cancel or pause an ongoing SIP?",
    "How does SEBI categorize multi-cap equity funds in terms of market cap allocation?",
    "What are the consequences of not linking Aadhaar with PAN for mutual fund folios?",
    "How are short term capital gains taxed when mutual fund units are held for less than one year?",
    "What is a Consolidated Account Statement (CAS) and how can an investor request it?",
    "Can a minor invest in mutual funds and what is the documentation required?",
    "What is the NAV formula used by AMCs to calculate daily net asset value?",
    "What is the role of trustees in safeguarding mutual fund investors' interests?",
    "How does an investor register a nominee for an existing mutual fund folio?",
]


def measure_model_load_time() -> float:
    """Measures clean model loading time using SentenceTransformer."""
    from sentence_transformers import SentenceTransformer
    from app.core.config import settings

    t0 = time.perf_counter()
    _ = SentenceTransformer(settings.EMBEDDING_MODEL, device="cpu")
    elapsed_ms = (time.perf_counter() - t0) * 1000
    return elapsed_ms


def run_benchmark():
    print("=" * 70)
    print("100 MIXED REQUESTS LATENCY BENCHMARK AFTER APPLICATION WARMUP")
    print("=" * 70)

    # 1. Model Load Time
    print("\n1. Measuring Model Load Time...")
    model_load_ms = measure_model_load_time()
    print(f"   Model Load Time: {model_load_ms:.2f} ms")

    # 2. Warm up client using TestClient lifespan
    print("\n2. Initializing and Warming Up Application...")
    client = TestClient(app)
    with client:
        # Verify warm up request
        warm_resp = client.get("/api/v1/health")
        assert warm_resp.status_code == 200
        print("   Application Lifespan & Middleware Warm: Ready")

        # 3. Execute 100 Mixed Requests
        print(f"\n3. Executing 100 Mixed Requests:")
        print(f"   - Refusal Queries: {len(REFUSAL_QUERIES)}")
        print(f"   - Fact Lookup Queries: {len(FACT_LOOKUP_QUERIES)}")
        print(f"   - LLM Synthesis Queries: {len(LLM_SYNTHESIS_QUERIES)}")
        total_requests = len(REFUSAL_QUERIES) + len(FACT_LOOKUP_QUERIES) + len(LLM_SYNTHESIS_QUERIES)
        assert total_requests == 100, f"Expected 100 queries, got {total_requests}"

        refusal_latencies = []
        fact_latencies = []
        llm_latencies = []

        # Run Refusal Queries
        print("\n   [1/3] Benchmarking Refusal Path (35 requests)...")
        for i, q in enumerate(REFUSAL_QUERIES, 1):
            _IP_REQUEST_TIMESTAMPS.clear()
            t0 = time.perf_counter()
            r = client.post("/api/v1/rag/ask", json={"query": q})
            dur = (time.perf_counter() - t0) * 1000
            refusal_latencies.append(dur)
            assert r.status_code == 200

        # Run Fact Lookup Queries
        print("   [2/3] Benchmarking Fact Lookup Path (35 requests)...")
        for i, q in enumerate(FACT_LOOKUP_QUERIES, 1):
            _IP_REQUEST_TIMESTAMPS.clear()
            t0 = time.perf_counter()
            r = client.post("/api/v1/rag/ask", json={"query": q})
            dur = (time.perf_counter() - t0) * 1000
            fact_latencies.append(dur)
            assert r.status_code == 200

        # Run LLM Synthesis Queries
        print("   [3/3] Benchmarking LLM Synthesis Path (30 requests)...")
        for i, q in enumerate(LLM_SYNTHESIS_QUERIES, 1):
            _IP_REQUEST_TIMESTAMPS.clear()
            t0 = time.perf_counter()
            r = client.post("/api/v1/rag/ask", json={"query": q})
            dur = (time.perf_counter() - t0) * 1000
            llm_latencies.append(dur)
            assert r.status_code == 200

        all_latencies = refusal_latencies + fact_latencies + llm_latencies

        # Compute statistics
        print("\n" + "=" * 70)
        print("LATENCY BENCHMARK RESULTS SUMMARY (100 MIXED REQUESTS)")
        print("=" * 70)
        print(f"Model Load Time: {model_load_ms:.2f} ms\n")

        print(f"{'Path':<22} | {'Count':<6} | {'p50 (ms)':<10} | {'p95 (ms)':<10} | {'Mean (ms)':<10}")
        print("-" * 65)

        ref_p50 = np.percentile(refusal_latencies, 50)
        ref_p95 = np.percentile(refusal_latencies, 95)
        ref_mean = np.mean(refusal_latencies)
        print(f"{'Refusal Path':<22} | {len(refusal_latencies):<6} | {ref_p50:<10.2f} | {ref_p95:<10.2f} | {ref_mean:<10.2f}")

        fact_p50 = np.percentile(fact_latencies, 50)
        fact_p95 = np.percentile(fact_latencies, 95)
        fact_mean = np.mean(fact_latencies)
        print(f"{'Fact Lookup Path':<22} | {len(fact_latencies):<6} | {fact_p50:<10.2f} | {fact_p95:<10.2f} | {fact_mean:<10.2f}")

        llm_p50 = np.percentile(llm_latencies, 50)
        llm_p95 = np.percentile(llm_latencies, 95)
        llm_mean = np.mean(llm_latencies)
        print(f"{'LLM Synthesis Path':<22} | {len(llm_latencies):<6} | {llm_p50:<10.2f} | {llm_p95:<10.2f} | {llm_mean:<10.2f}")

        all_p50 = np.percentile(all_latencies, 50)
        all_p95 = np.percentile(all_latencies, 95)
        all_mean = np.mean(all_latencies)
        print("-" * 65)
        print(f"{'Overall (100 Mixed)':<22} | {len(all_latencies):<6} | {all_p50:<10.2f} | {all_p95:<10.2f} | {all_mean:<10.2f}")
        print("=" * 70)


if __name__ == "__main__":
    run_benchmark()
