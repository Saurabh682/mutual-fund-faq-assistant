import json
import sys
import time
from pathlib import Path
from unittest.mock import patch

# Ensure UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

REPO_DIR = Path("D:/VibeCode/Applied Generative AI Bootcamp/mutual-fund-faq-assistant")
sys.path.insert(0, str(REPO_DIR / "backend"))

from fastapi.testclient import TestClient
from app.main import app, _IP_REQUEST_TIMESTAMPS
from app.rag.synthesizer import ConstrainedSynthesizer

client = TestClient(app)

schemes = [
    "HDFC Small Cap Fund",
    "HDFC Mid-Cap Opportunities Fund",
    "HDFC Top 100 Fund",
    "HDFC Multi Cap Fund",
    "HDFC Silver ETF FoF",
]

fields = [
    "exit load",
    "expense ratio",
    "NAV",
    "minimum SIP",
    "fund manager",
    "benchmark",
    "lock-in period",
    "AUM",
    "riskometer",
    "minimum lumpsum",
]

decision_templates = [
    "Should I invest in {scheme} right now?",
    "Will {scheme} outperform the market over the next 5 years?",
    "Is {scheme} the best choice for wealth creation?",
    "Should a conservative retiree buy {scheme}?",
    "Would you advise starting an SIP in {scheme} during a market dip?",
    "Can you predict the future return of {scheme} for next year?",
    "Is it smart to allocate all my savings into {scheme} today?",
    "Is now a good time to exit {scheme}?",
    "Which is a better investment, {scheme1} or {scheme2}?",
    "Compare {scheme1} and {scheme2} and pick the winning fund.",
    "Rank {scheme1} against {scheme2} in terms of expected profits.",
    "Help me choose between {scheme1} and {scheme2} for my retirement.",
]

compound_templates = [
    "What is {scheme}'s {field}, and do you think I should invest?",
    "Tell me the {field} for {scheme}, and is it a good buy today?",
    "{scheme} {field}, plus should I redeem my units before next month?",
    "What is the {field} of {scheme}, and will it beat inflation by 2030?",
    "Please share {scheme} {field}, and whether it is safe for beginners.",
    "What is the {field} of {scheme}, also should I stop my SIP during volatility?",
    "Can you give me the {field} for {scheme}, and would you recommend it?",
]

unsupported_templates = [
    "What is the 3-year CAGR for {scheme}?",
    "What proportion of {scheme} is invested in banking stocks?",
    "How many stocks does {scheme} hold in its portfolio?",
    "What is the standard deviation of {scheme}?",
    "What was the Sharpe ratio of {scheme} over the last fiscal year?",
    "What is the beta metric of {scheme} relative to the market?",
    "What was {scheme}'s maximum drawdown during the 2020 correction?",
]

# Generate synthetic cases
cases = []
case_id = 1

# 1. Decision cases (~50)
for s in schemes:
    for t in decision_templates[:8]:
        cases.append({
            "id": f"syn_dec_{case_id:03d}",
            "type": "DECISION",
            "query": t.format(scheme=s),
        })
        case_id += 1

for i in range(len(schemes)):
    s1 = schemes[i]
    s2 = schemes[(i + 1) % len(schemes)]
    for t in decision_templates[8:]:
        cases.append({
            "id": f"syn_dec_{case_id:03d}",
            "type": "DECISION",
            "query": t.format(scheme1=s1, scheme2=s2),
        })
        case_id += 1

# 2. Compound cases (~35)
for s in schemes:
    for fld in fields[:7]:
        t = compound_templates[(case_id) % len(compound_templates)]
        cases.append({
            "id": f"syn_cmp_{case_id:03d}",
            "type": "COMPOUND",
            "query": t.format(scheme=s, field=fld),
        })
        case_id += 1

# 3. Unsupported cases (~35)
for s in schemes:
    for t in unsupported_templates:
        cases.append({
            "id": f"syn_uns_{case_id:03d}",
            "type": "UNSUPPORTED",
            "query": t.format(scheme=s),
        })
        case_id += 1

print(f"Total synthetic cases generated: {len(cases)}")
print(f"  Decision cases: {sum(1 for c in cases if c['type'] == 'DECISION')}")
print(f"  Compound cases: {sum(1 for c in cases if c['type'] == 'COMPOUND')}")
print(f"  Unsupported cases: {sum(1 for c in cases if c['type'] == 'UNSUPPORTED')}")

llm_call_count = 0
llm_decision_calls = 0
llm_compound_calls = 0

def mocked_llm(self, system_prompt, user_prompt, *args, **kwargs):
    global llm_call_count, current_type
    llm_call_count += 1
    if current_type == "DECISION":
        global llm_decision_calls
        llm_decision_calls += 1
    elif current_type == "COMPOUND":
        global llm_compound_calls
        llm_compound_calls += 1
    return "Mock synthesis answer"

results_by_type = {"DECISION": [], "COMPOUND": [], "UNSUPPORTED": []}

with patch.object(ConstrainedSynthesizer, "_call_llm", mocked_llm):
    for c in cases:
        current_type = c["type"]
        _IP_REQUEST_TIMESTAMPS.clear()
        t0 = time.perf_counter()
        resp = client.post("/api/v1/rag/ask", json={"query": c["query"]})
        elapsed = (time.perf_counter() - t0) * 1000
        data = resp.json()
        res_type = data.get("resolution_type", "unknown")
        results_by_type[c["type"]].append({
            "id": c["id"],
            "query": c["query"],
            "status": resp.status_code,
            "resolution_type": res_type,
            "elapsed_ms": elapsed,
        })

print("\n--- SYNTHETIC STRESS TEST RESULTS ---")
print(f"Total cases evaluated: {len(cases)}")
print(f"Total LLM calls across all cases: {llm_call_count}")
print(f"LLM calls on DECISION cases: {llm_decision_calls} (Invariant requirement: 0)")
print(f"LLM calls on COMPOUND cases: {llm_compound_calls} (Invariant requirement: 0)")

dec_resolutions = [r["resolution_type"] for r in results_by_type["DECISION"]]
print(f"Decision resolution breakdown: {dict((x, dec_resolutions.count(x)) for x in set(dec_resolutions))}")

cmp_resolutions = [r["resolution_type"] for r in results_by_type["COMPOUND"]]
print(f"Compound resolution breakdown: {dict((x, cmp_resolutions.count(x)) for x in set(cmp_resolutions))}")

uns_resolutions = [r["resolution_type"] for r in results_by_type["UNSUPPORTED"]]
print(f"Unsupported resolution breakdown: {dict((x, uns_resolutions.count(x)) for x in set(uns_resolutions))}")

assert llm_decision_calls == 0, f"FAILED: LLM was called {llm_decision_calls} times on decision queries!"
assert llm_compound_calls == 0, f"FAILED: LLM was called {llm_compound_calls} times on compound queries!"
print("\n>>> ALL INVARIANTS PASSED SUCCESSFULLY! ZERO LLM CALLS ON DECISION/COMPOUND. <<<")
