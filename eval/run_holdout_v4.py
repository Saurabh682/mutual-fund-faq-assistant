import json
import os
import sys
import time
from pathlib import Path
from unittest.mock import patch
import sqlite3

# Ensure UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

REPO_DIR = Path("D:/VibeCode/Applied Generative AI Bootcamp/mutual-fund-faq-assistant")
sys.path.insert(0, str(REPO_DIR / "backend"))

from fastapi.testclient import TestClient
from app.main import app, _IP_REQUEST_TIMESTAMPS
from app.rag.synthesizer import ConstrainedSynthesizer
from app.sessions.store import SessionStore

client = TestClient(app)

# Load facts.db
facts_db_path = REPO_DIR / "data" / "index" / "facts.db"
conn = sqlite3.connect(str(facts_db_path))
cursor = conn.cursor()
cursor.execute("SELECT scheme_id, field, value FROM facts")
FACTS_MAP = {f"{r[0]}::{r[1]}": r[2] for r in cursor.fetchall()}
conn.close()

# Load holdout_v4.jsonl
dataset_path = REPO_DIR / "eval" / "datasets" / "holdout_v4.jsonl"
with open(dataset_path, "r", encoding="utf-8") as f:
    cases = [json.loads(line) for line in f if line.strip()]

results = []
forbidden_llm_calls = []
current_case = {}
llm_call_count_current = 0

original_call_llm = ConstrainedSynthesizer._call_llm

def mocked_call_llm(self, system_prompt, user_prompt, *args, **kwargs):
    global llm_call_count_current, current_case
    llm_call_count_current += 1
    exp = current_case.get("expected_behavior")
    if exp in ("REFUSAL", "COMPOUND"):
        forbidden_llm_calls.append({
            "id": current_case.get("id"),
            "query": current_case.get("query"),
            "expected": exp,
            "system_prompt": system_prompt[:120],
            "user_prompt": user_prompt[:120],
        })
    try:
        return original_call_llm(self, system_prompt, user_prompt, *args, **kwargs)
    except Exception as e:
        return f"Mock synthesis response ({e})"

# PII leak verification storage
pii_storage_check = {
    "tested": False,
    "pan_leaked_in_ask": False,
    "aadhaar_leaked_in_ask": False,
    "pan_leaked_in_thread": False,
    "aadhaar_leaked_in_thread": False,
}

raw_pan_v4 = "BXYPK5678L"
raw_aadhaar_v4 = "4821 7396 5012"

with patch.object(ConstrainedSynthesizer, "_call_llm", mocked_call_llm):
    for case in cases:
        current_case = case
        cid = case["id"]
        query = case["query"]
        expected = case["expected_behavior"]
        expected_scheme = case.get("expected_scheme_id")
        expected_field = case.get("expected_field")

        _IP_REQUEST_TIMESTAMPS.clear()
        llm_call_count_current = 0

        t0 = time.perf_counter()
        resp = client.post("/api/v1/rag/ask", json={"query": query})
        elapsed_ms = (time.perf_counter() - t0) * 1000

        llm_called = (llm_call_count_current > 0)
        status_code = resp.status_code
        data = resp.json() if status_code in (200, 400) else {}

        # Classify observed behavior
        observed = None
        rendered = data.get("rendered", "")
        text = data.get("text", "")
        resolution_type = data.get("resolution_type", "")

        if status_code == 400 and data.get("error") == "PII_DETECTED":
            observed = "PII_BLOCK"
        elif resolution_type == "compound":
            observed = "COMPOUND"
        elif resolution_type == "refusal":
            observed = "REFUSAL"
        elif resolution_type == "unsupported_plan":
            observed = "UNSUPPORTED_PLAN"
        elif resolution_type in ("external_amc", "out_of_scope"):
            observed = "OUT_OF_SCOPE"
        elif resolution_type == "not_found":
            from app.guardrails.intent import classify_intent
            i_res = classify_intent(query)
            if i_res.intent == "OUT_OF_SCOPE":
                observed = "OUT_OF_SCOPE"
            else:
                observed = "NOT_FOUND"
        elif resolution_type in ("fact_store", "llm_synthesis", "hybrid_retrieval", "help"):
            observed = "ANSWER"
        else:
            observed = f"UNKNOWN({resolution_type})"

        # PII leak verification in ask API
        if cid == "v4_26":
            if raw_pan_v4 in resp.text:
                pii_storage_check["pan_leaked_in_ask"] = True
        elif cid == "v4_27":
            if raw_aadhaar_v4 in resp.text:
                pii_storage_check["aadhaar_leaked_in_ask"] = True

        # Check fact match for ANSWER and COMPOUND
        fact_match = True
        fact_detail = ""
        if expected_scheme and expected_field and observed in ("ANSWER", "COMPOUND"):
            fields = [f.strip() for f in expected_field.split(",")]
            for fld in fields:
                if fld.startswith("glossary:"):
                    continue
                db_key = f"{expected_scheme}::{fld}"
                expected_val = FACTS_MAP.get(db_key)
                if expected_val:
                    val_str = str(expected_val).replace("₹", "").strip()
                    full_resp_text = f"{rendered} {text}"
                    if val_str not in full_resp_text and expected_val not in full_resp_text:
                        val_clean = val_str.replace("%", "").strip()
                        if val_clean not in full_resp_text:
                            fact_match = False
                            fact_detail = f"Expected '{expected_val}' for {db_key} not in response"

        # Check if NOT_FOUND could be answered from data
        answerable_note = ""
        if expected == "NOT_FOUND":
            # Check if any in-scope scheme fact has this data
            pass

        passed = (observed == expected) and fact_match and (not (expected in ("REFUSAL", "COMPOUND") and llm_called))

        results.append({
            "id": cid,
            "query": query,
            "expected": expected,
            "observed": observed,
            "resolution_type": resolution_type,
            "llm_called": llm_called,
            "llm_call_count": llm_call_count_current,
            "latency_ms": elapsed_ms,
            "passed": passed,
            "fact_match": fact_match,
            "fact_detail": fact_detail,
            "full_response": rendered or text or str(data),
            "status_code": status_code,
            "answerable_note": answerable_note,
        })

# Perform thread store PII leak check
store = SessionStore()
t1 = store.create_thread(client_id="holdout_v4_pii", title="V4 PAN Test")
resp_t1 = client.post(
    f"/api/v1/threads/{t1.id}/messages",
    json={"text": f"My PAN is {raw_pan_v4}, what is the exit load on Mid-Cap?"},
    headers={"X-Client-Id": "holdout_v4_pii"},
)
th1 = store.get_thread(t1.id)
if th1:
    for m in th1.messages:
        if raw_pan_v4 in m.text:
            pii_storage_check["pan_leaked_in_thread"] = True

t2 = store.create_thread(client_id="holdout_v4_pii", title="V4 Aadhaar Test")
resp_t2 = client.post(
    f"/api/v1/threads/{t2.id}/messages",
    json={"text": f"Verify Aadhaar {raw_aadhaar_v4} before SIP min."},
    headers={"X-Client-Id": "holdout_v4_pii"},
)
th2 = store.get_thread(t2.id)
if th2:
    for m in th2.messages:
        if raw_aadhaar_v4 in m.text:
            pii_storage_check["aadhaar_leaked_in_thread"] = True
pii_storage_check["tested"] = True

# Calculate per-behavior Precision and Recall
behaviors = ["COMPOUND", "REFUSAL", "NOT_FOUND", "OUT_OF_SCOPE", "UNSUPPORTED_PLAN", "PII_BLOCK", "ANSWER"]
metrics = {}
for b in behaviors:
    tp = sum(1 for r in results if r["expected"] == b and r["observed"] == b and r["passed"])
    fp = sum(1 for r in results if r["expected"] != b and r["observed"] == b)
    fn = sum(1 for r in results if r["expected"] == b and (r["observed"] != b or not r["passed"]))
    prec = tp / (tp + fp) if (tp + fp) > 0 else (1.0 if (tp + fn) == 0 else 0.0)
    rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    metrics[b] = {
        "TP": tp,
        "FP": fp,
        "FN": fn,
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "support": tp + fn,
    }

total_passed = sum(1 for r in results if r["passed"])

output_data = {
    "total_cases": len(results),
    "total_passed": total_passed,
    "metrics": metrics,
    "forbidden_llm_calls": forbidden_llm_calls,
    "pii_storage_check": pii_storage_check,
    "cases": results,
}

os.makedirs(REPO_DIR / "eval" / "reports", exist_ok=True)
with open(REPO_DIR / "eval" / "reports" / "holdout_v4_results.json", "w", encoding="utf-8") as f:
    json.dump(output_data, f, indent=2, ensure_ascii=False)

print(f"EVAL COMPLETE: {total_passed}/{len(results)} passed.")
print(json.dumps(metrics, indent=2))
